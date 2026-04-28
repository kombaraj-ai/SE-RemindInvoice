"""
Invoice business-logic service layer.

All database mutations live here so routers remain thin. Key rules enforced:

* invoice_number  — auto-generated as INV-YYYYMM-XXXX (sequential per user).
* public_token    — UUID v4 string, generated once at creation.
* subtotal / tax_amount / total — always computed server-side; client values ignored.
* Only DRAFT invoices may be edited or deleted (ConflictError otherwise).
* Sending an invoice generates a PDF, emails the client, sets sent_at and status→sent.
* Overdue detection runs as a Celery periodic task but ``update_overdue_statuses``
  can also be called on-demand.
"""

import logging
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.exceptions import ConflictError, ForbiddenError, NotFoundError  # noqa: F401
from app.models.client import Client
from app.models.invoice import Invoice, InvoiceItem, InvoiceStatus
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _generate_invoice_number(db: Session, user_id: int) -> str:
    """
    Return the next sequential invoice number for *user_id* in the current month.

    Format: ``INV-YYYYMM-XXXX``  e.g. ``INV-202604-0003``.

    The counter resets each month because the prefix changes.
    """
    prefix = f"INV-{datetime.now().strftime('%Y%m')}"
    count: int = (
        db.query(func.count(Invoice.id))
        .filter(
            Invoice.user_id == user_id,
            Invoice.invoice_number.like(f"{prefix}%"),
        )
        .scalar()
        or 0
    )
    return f"{prefix}-{count + 1:04d}"


def _compute_totals(
    items: list[InvoiceItem],
    tax_rate: Decimal,
    discount_amount: Decimal,
) -> tuple[Decimal, Decimal, Decimal]:
    """
    Compute and return ``(subtotal, tax_amount, total)`` from a list of items.

    All values are quantized to 2 decimal places. ``total`` is clamped to zero
    to prevent negative totals caused by large discounts.
    """
    subtotal: Decimal = sum(
        Decimal(str(item.quantity)) * Decimal(str(item.unit_price))
        for item in items
    )
    tax_amount: Decimal = (subtotal * tax_rate / 100).quantize(Decimal("0.01"))
    total_raw: Decimal = subtotal + tax_amount - discount_amount
    total: Decimal = max(total_raw, Decimal("0")).quantize(Decimal("0.01"))
    return subtotal.quantize(Decimal("0.01")), tax_amount, total


def _build_item(
    invoice_id: int,
    item_data: object,
    fallback_sort: int,
) -> InvoiceItem:
    """Construct an ``InvoiceItem`` ORM object from a schema item."""
    quantity = Decimal(str(item_data.quantity))
    unit_price = Decimal(str(item_data.unit_price))
    amount = (quantity * unit_price).quantize(Decimal("0.01"))
    sort_order = item_data.sort_order if item_data.sort_order else fallback_sort
    return InvoiceItem(
        invoice_id=invoice_id,
        description=item_data.description,
        quantity=quantity,
        unit_price=unit_price,
        amount=amount,
        sort_order=sort_order,
    )


# ---------------------------------------------------------------------------
# Read operations
# ---------------------------------------------------------------------------


def get_invoices(
    db: Session,
    user_id: int,
    status: InvoiceStatus | None = None,
    client_id: int | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[Invoice], int]:
    """
    Return a paginated list of invoices for *user_id* and the total count.

    Optional filters:
    * ``status``    — restrict to a specific lifecycle state.
    * ``client_id`` — restrict to a specific client.
    """
    q = (
        db.query(Invoice)
        .options(joinedload(Invoice.client), joinedload(Invoice.items))
        .filter(Invoice.user_id == user_id)
    )
    if status is not None:
        q = q.filter(Invoice.status == status)
    if client_id is not None:
        q = q.filter(Invoice.client_id == client_id)

    total: int = q.count()
    invoices: list[Invoice] = (
        q.order_by(Invoice.created_at.desc()).offset(skip).limit(limit).all()
    )
    return invoices, total


def get_invoice(db: Session, invoice_id: int, user_id: int) -> Invoice:
    """
    Fetch a single invoice by primary key, scoped to *user_id*.

    :raises NotFoundError: If the invoice does not exist or belongs to another user.
    """
    invoice: Invoice | None = (
        db.query(Invoice)
        .options(joinedload(Invoice.items), joinedload(Invoice.client))
        .filter(Invoice.id == invoice_id, Invoice.user_id == user_id)
        .first()
    )
    if not invoice:
        raise NotFoundError("Invoice")
    return invoice


def get_invoice_by_token(db: Session, token: str) -> Invoice:
    """
    Fetch a single invoice by its public UUID token (no user-ownership check).

    Used by the unauthenticated public view endpoint.

    :raises NotFoundError: If no invoice carries the given token.
    """
    invoice: Invoice | None = (
        db.query(Invoice)
        .options(joinedload(Invoice.items), joinedload(Invoice.client))
        .filter(Invoice.public_token == token)
        .first()
    )
    if not invoice:
        raise NotFoundError("Invoice")
    return invoice


# ---------------------------------------------------------------------------
# Write operations
# ---------------------------------------------------------------------------


def create_invoice(db: Session, user_id: int, data: InvoiceCreate) -> Invoice:
    """
    Create a new DRAFT invoice with auto-generated ``invoice_number`` and
    ``public_token``. Totals are computed server-side from the supplied items.

    :raises NotFoundError: If ``data.client_id`` does not belong to *user_id*.
    """
    client: Client | None = (
        db.query(Client)
        .filter(Client.id == data.client_id, Client.user_id == user_id)
        .first()
    )
    if not client:
        raise NotFoundError("Client")

    invoice = Invoice(
        user_id=user_id,
        client_id=data.client_id,
        invoice_number=_generate_invoice_number(db, user_id),
        public_token=str(uuid.uuid4()),
        status=InvoiceStatus.draft,
        issue_date=data.issue_date,
        due_date=data.due_date,
        tax_rate=data.tax_rate,
        discount_amount=data.discount_amount,
        currency=data.currency,
        notes=data.notes,
        # Placeholder totals — recalculated below after items are persisted
        subtotal=Decimal("0"),
        tax_amount=Decimal("0"),
        total=Decimal("0"),
    )
    db.add(invoice)
    db.flush()  # obtain invoice.id before inserting items

    orm_items: list[InvoiceItem] = []
    for i, item_data in enumerate(data.items):
        item = _build_item(invoice.id, item_data, fallback_sort=i)
        db.add(item)
        orm_items.append(item)

    db.flush()

    subtotal, tax_amount, total = _compute_totals(
        orm_items, data.tax_rate, data.discount_amount
    )
    invoice.subtotal = subtotal
    invoice.tax_amount = tax_amount
    invoice.total = total

    db.commit()
    db.refresh(invoice)
    logger.info("Invoice created: %s user_id=%d", invoice.invoice_number, user_id)
    return invoice


def update_invoice(
    db: Session, invoice_id: int, user_id: int, data: InvoiceUpdate
) -> Invoice:
    """
    Partially update a DRAFT invoice.

    When ``data.items`` is supplied the existing items are replaced wholesale
    and totals are recomputed. Only fields included in the payload are changed.

    :raises NotFoundError: If the invoice does not exist for *user_id*.
    :raises ConflictError: If the invoice is not in DRAFT status.
    """
    invoice = get_invoice(db, invoice_id, user_id)
    if invoice.status != InvoiceStatus.draft:
        raise ConflictError("Only draft invoices can be edited")

    # Apply scalar field updates
    for field, value in data.model_dump(exclude_none=True, exclude={"items"}).items():
        setattr(invoice, field, value)

    # Replace line items if provided
    if data.items is not None:
        db.query(InvoiceItem).filter(InvoiceItem.invoice_id == invoice_id).delete()
        db.flush()

        new_items: list[InvoiceItem] = []
        for i, item_data in enumerate(data.items):
            item = _build_item(invoice_id, item_data, fallback_sort=i)
            db.add(item)
            new_items.append(item)

        db.flush()

        subtotal, tax_amount, total = _compute_totals(
            new_items,
            Decimal(str(invoice.tax_rate)),
            Decimal(str(invoice.discount_amount)),
        )
        invoice.subtotal = subtotal
        invoice.tax_amount = tax_amount
        invoice.total = total

    db.commit()
    db.refresh(invoice)
    logger.info("Invoice updated: id=%d user_id=%d", invoice_id, user_id)
    return invoice


def delete_invoice(db: Session, invoice_id: int, user_id: int) -> None:
    """
    Permanently delete a DRAFT invoice (cascade deletes its items).

    :raises NotFoundError: If the invoice does not exist for *user_id*.
    :raises ConflictError: If the invoice is not in DRAFT status.
    """
    invoice = get_invoice(db, invoice_id, user_id)
    if invoice.status != InvoiceStatus.draft:
        raise ConflictError("Only draft invoices can be deleted")

    db.delete(invoice)
    db.commit()
    logger.info("Invoice deleted: id=%d user_id=%d", invoice_id, user_id)


def send_invoice(db: Session, invoice_id: int, user_id: int) -> Invoice:
    """
    Send an invoice to its client.

    Steps:
    1. Generate a PDF (best-effort — skipped if WeasyPrint is absent).
    2. Email the client with the public view link and optional PDF reference.
    3. Transition status to SENT and record ``sent_at``.

    :raises NotFoundError: If the invoice does not exist for *user_id*.
    :raises ConflictError: If the invoice is CANCELLED.
    """
    from app.services.email import send_invoice_email
    from app.services.pdf import generate_invoice_pdf

    invoice = get_invoice(db, invoice_id, user_id)
    if invoice.status in (InvoiceStatus.cancelled, InvoiceStatus.paid):
        raise ConflictError(f"Cannot send a {invoice.status.value} invoice")

    invoice_data: dict = {
        "invoice_number": invoice.invoice_number,
        "status": invoice.status.value,
        "issue_date": str(invoice.issue_date),
        "due_date": str(invoice.due_date),
        "client_name": invoice.client.name,
        "client_email": invoice.client.email,
        "client_company": invoice.client.company_name or "",
        "currency": invoice.currency,
        "subtotal": str(invoice.subtotal),
        "tax_rate": str(invoice.tax_rate),
        "tax_amount": str(invoice.tax_amount),
        "discount_amount": str(invoice.discount_amount),
        "total": str(invoice.total),
        "notes": invoice.notes,
        "items": [
            {
                "description": item.description,
                "quantity": str(item.quantity),
                "unit_price": str(item.unit_price),
                "amount": str(item.amount),
            }
            for item in invoice.items
        ],
    }

    pdf_path: str = generate_invoice_pdf(invoice_data)
    if pdf_path:
        invoice.pdf_url = pdf_path

    send_invoice_email(
        invoice.client.email,
        invoice.client.name,
        invoice.invoice_number,
        invoice.public_token,
        pdf_path or None,
    )

    invoice.status = InvoiceStatus.sent
    invoice.sent_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(invoice)
    logger.info("Invoice sent: %s user_id=%d", invoice.invoice_number, user_id)
    return invoice


def mark_paid(db: Session, invoice_id: int, user_id: int) -> Invoice:
    """
    Mark an invoice as PAID and record ``paid_at``.

    DRAFT and CANCELLED invoices cannot be marked paid.

    :raises NotFoundError: If the invoice does not exist for *user_id*.
    :raises ConflictError: If the invoice is in DRAFT or CANCELLED status.
    """
    invoice = get_invoice(db, invoice_id, user_id)
    if invoice.status in (InvoiceStatus.cancelled, InvoiceStatus.draft):
        raise ConflictError(
            f"Cannot mark a {invoice.status.value} invoice as paid"
        )

    invoice.status = InvoiceStatus.paid
    invoice.paid_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(invoice)
    logger.info(
        "Invoice marked paid: id=%d user_id=%d", invoice_id, user_id
    )
    return invoice


def duplicate_invoice(db: Session, invoice_id: int, user_id: int) -> Invoice:
    """
    Create a new DRAFT invoice copied from an existing one.

    The duplicate gets today's issue/due dates, a fresh invoice number, and a
    new ``public_token``. Status is always DRAFT regardless of the source.

    :raises NotFoundError: If the source invoice does not exist for *user_id*.
    """
    source = get_invoice(db, invoice_id, user_id)

    new_invoice = Invoice(
        user_id=user_id,
        client_id=source.client_id,
        invoice_number=_generate_invoice_number(db, user_id),
        public_token=str(uuid.uuid4()),
        status=InvoiceStatus.draft,
        issue_date=date.today(),
        due_date=date.today(),
        tax_rate=source.tax_rate,
        discount_amount=source.discount_amount,
        currency=source.currency,
        notes=source.notes,
        subtotal=source.subtotal,
        tax_amount=source.tax_amount,
        total=source.total,
    )
    db.add(new_invoice)
    db.flush()  # obtain new_invoice.id

    for item in source.items:
        db.add(
            InvoiceItem(
                invoice_id=new_invoice.id,
                description=item.description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                amount=item.amount,
                sort_order=item.sort_order,
            )
        )

    db.commit()
    db.refresh(new_invoice)
    logger.info(
        "Invoice duplicated: source_id=%d new_id=%d user_id=%d",
        invoice_id,
        new_invoice.id,
        user_id,
    )
    return new_invoice


# ---------------------------------------------------------------------------
# Background / scheduled operations
# ---------------------------------------------------------------------------


def update_overdue_statuses(db: Session) -> int:
    """
    Transition all SENT or VIEWED invoices whose ``due_date`` is in the past
    to OVERDUE.

    Intended to be called from a Celery beat task (daily). Returns the number
    of invoices updated.
    """
    today = date.today()
    overdue_invoices: list[Invoice] = (
        db.query(Invoice)
        .filter(
            Invoice.status.in_([InvoiceStatus.sent, InvoiceStatus.viewed]),
            Invoice.due_date < today,
        )
        .all()
    )

    count = 0
    for invoice in overdue_invoices:
        invoice.status = InvoiceStatus.overdue
        count += 1

    if count:
        db.commit()

    logger.info("Updated %d invoice(s) to overdue", count)
    return count
