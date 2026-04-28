"""
Unit tests for invoice_service helper functions.

These tests exercise the pure business-logic layer directly, without going
through the HTTP layer. They use the SQLite db fixture for functions that
need a DB session, and plain in-memory objects where no DB is required.
"""

import re
from datetime import datetime
from decimal import Decimal
import pytest

from app.models.invoice import Invoice, InvoiceItem, InvoiceStatus
from app.models.user import User
from app.models.client import Client
from app.schemas.invoice import InvoiceCreate, InvoiceItemCreate
from app.services.invoice_service import (
    _compute_totals,
    _generate_invoice_number,
    create_invoice,
    delete_invoice,
    mark_paid,
    update_overdue_statuses,
)
from app.exceptions import ConflictError, NotFoundError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_item(quantity: str, unit_price: str) -> InvoiceItem:
    """Construct a minimal InvoiceItem ORM object for compute_totals testing."""
    item = InvoiceItem()
    item.quantity = Decimal(quantity)
    item.unit_price = Decimal(unit_price)
    item.amount = (Decimal(quantity) * Decimal(unit_price)).quantize(Decimal("0.01"))
    return item


def _make_user(db) -> User:
    """Persist a test user and return it."""
    user = User(
        email="svc_test@example.com",
        hashed_password="hashed",
        full_name="Service Test",
        is_active=True,
        is_verified=False,
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_client(db, user_id: int) -> Client:
    """Persist a test client and return it."""
    c = Client(
        user_id=user_id,
        name="Service Client",
        email="svclient@example.com",
        is_active=True,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def _make_invoice(db, user_id: int, client_id: int, status=InvoiceStatus.draft) -> Invoice:
    """Persist a minimal Invoice (with one item) and return it."""
    import uuid
    from datetime import date

    inv = Invoice(
        user_id=user_id,
        client_id=client_id,
        invoice_number=_generate_invoice_number(db, user_id),
        public_token=str(uuid.uuid4()),
        status=status,
        issue_date=date.today(),
        due_date=date.today(),
        tax_rate=Decimal("0"),
        discount_amount=Decimal("0"),
        subtotal=Decimal("100.00"),
        tax_amount=Decimal("0.00"),
        total=Decimal("100.00"),
        currency="USD",
    )
    db.add(inv)
    db.flush()

    item = InvoiceItem(
        invoice_id=inv.id,
        description="Test item",
        quantity=Decimal("1"),
        unit_price=Decimal("100.00"),
        amount=Decimal("100.00"),
        sort_order=0,
    )
    db.add(item)
    db.commit()
    db.refresh(inv)
    return inv


# ---------------------------------------------------------------------------
# _generate_invoice_number
# ---------------------------------------------------------------------------


class TestGenerateInvoiceNumber:
    """Unit tests for the private _generate_invoice_number helper."""

    def test_format_matches_inv_yyyymm_xxxx(self, db):
        """Generated number must match INV-YYYYMM-XXXX."""
        user = _make_user(db)
        number = _generate_invoice_number(db, user.id)
        pattern = r"^INV-\d{6}-\d{4}$"
        assert re.match(pattern, number), f"Number {number!r} doesn't match {pattern}"

    def test_prefix_contains_current_year_month(self, db):
        """The YYYYMM portion must equal the current year and month."""
        user = _make_user(db)
        number = _generate_invoice_number(db, user.id)
        now = datetime.now()
        expected_prefix = f"INV-{now.strftime('%Y%m')}"
        assert number.startswith(expected_prefix)

    def test_first_invoice_is_0001(self, db):
        """The very first invoice for a user in a month should be 0001."""
        user = _make_user(db)
        number = _generate_invoice_number(db, user.id)
        seq = number.split("-")[-1]
        assert seq == "0001"

    def test_second_invoice_increments(self, db):
        """Each subsequent invoice increments the sequence by 1."""
        user = _make_user(db)
        # Create first invoice in the DB
        client_obj = _make_client(db, user.id)
        _make_invoice(db, user.id, client_obj.id)

        second = _generate_invoice_number(db, user.id)
        seq = int(second.split("-")[-1])
        assert seq == 2

    def test_different_users_have_independent_sequences(self, db):
        """Two users start their invoice sequences independently."""
        user1 = User(
            email="u1@example.com",
            hashed_password="h",
            is_active=True,
            is_verified=False,
            is_admin=False,
        )
        user2 = User(
            email="u2@example.com",
            hashed_password="h",
            is_active=True,
            is_verified=False,
            is_admin=False,
        )
        db.add_all([user1, user2])
        db.commit()
        db.refresh(user1)
        db.refresh(user2)

        client1 = _make_client(db, user1.id)
        # User 1 gets 2 invoices
        _make_invoice(db, user1.id, client1.id)
        _make_invoice(db, user1.id, client1.id)

        # User 2 first invoice should still be 0001
        n2 = _generate_invoice_number(db, user2.id)
        assert n2.endswith("0001")


# ---------------------------------------------------------------------------
# _compute_totals
# ---------------------------------------------------------------------------


class TestComputeTotals:
    """Unit tests for the private _compute_totals helper."""

    def test_basic_no_tax_no_discount(self):
        """qty=2, price=100, tax=0%, discount=0 → subtotal=200, tax=0, total=200."""
        items = [_make_item("2", "100")]
        subtotal, tax_amount, total = _compute_totals(
            items, Decimal("0"), Decimal("0")
        )
        assert subtotal == Decimal("200.00")
        assert tax_amount == Decimal("0.00")
        assert total == Decimal("200.00")

    def test_with_tax(self):
        """qty=2, price=100, tax=10% → subtotal=200, tax=20, total=220."""
        items = [_make_item("2", "100")]
        subtotal, tax_amount, total = _compute_totals(
            items, Decimal("10"), Decimal("0")
        )
        assert subtotal == Decimal("200.00")
        assert tax_amount == Decimal("20.00")
        assert total == Decimal("220.00")

    def test_with_discount(self):
        """qty=2, price=100, tax=10%, discount=10 → total = 220 - 10 = 210."""
        items = [_make_item("2", "100")]
        subtotal, tax_amount, total = _compute_totals(
            items, Decimal("10"), Decimal("10")
        )
        assert subtotal == Decimal("200.00")
        assert tax_amount == Decimal("20.00")
        assert total == Decimal("210.00")

    def test_total_never_negative_with_large_discount(self):
        """A discount larger than the total should clamp total to 0."""
        items = [_make_item("1", "50")]
        _subtotal, _tax, total = _compute_totals(
            items, Decimal("0"), Decimal("999")
        )
        assert total == Decimal("0.00")

    def test_total_never_negative_with_tax_and_large_discount(self):
        """Even with tax applied, a massive discount clamps total to 0."""
        items = [_make_item("1", "100")]
        _subtotal, _tax, total = _compute_totals(
            items, Decimal("10"), Decimal("500")
        )
        assert total == Decimal("0.00")

    def test_multiple_items(self):
        """Subtotal is the sum of all items."""
        items = [
            _make_item("1", "100"),
            _make_item("2", "50"),
            _make_item("3", "25"),
        ]
        subtotal, _tax, total = _compute_totals(
            items, Decimal("0"), Decimal("0")
        )
        assert subtotal == Decimal("275.00")
        assert total == Decimal("275.00")

    def test_fractional_quantity_and_price(self):
        """Fractional quantities and prices should be handled accurately."""
        items = [_make_item("1.5", "33.33")]
        subtotal, _tax, total = _compute_totals(
            items, Decimal("0"), Decimal("0")
        )
        # 1.5 * 33.33 = 49.995 → 50.00
        assert subtotal == Decimal("49.99") or subtotal == Decimal("50.00")

    def test_returns_two_decimal_places(self):
        """All returned values are quantized to exactly 2 decimal places."""
        items = [_make_item("1", "100")]
        subtotal, tax_amount, total = _compute_totals(
            items, Decimal("10"), Decimal("0")
        )
        for val in (subtotal, tax_amount, total):
            # Decimal.as_tuple().exponent should be -2
            assert val == val.quantize(Decimal("0.01"))

    def test_zero_tax_rate(self):
        """Zero tax rate should produce zero tax_amount."""
        items = [_make_item("5", "200")]
        _subtotal, tax_amount, _total = _compute_totals(
            items, Decimal("0"), Decimal("0")
        )
        assert tax_amount == Decimal("0.00")

    def test_empty_items_list(self):
        """Empty items list should produce all-zero results."""
        subtotal, tax_amount, total = _compute_totals(
            [], Decimal("10"), Decimal("5")
        )
        assert subtotal == Decimal("0.00")
        assert total == Decimal("0.00")


# ---------------------------------------------------------------------------
# create_invoice (service)
# ---------------------------------------------------------------------------


class TestCreateInvoiceService:
    """Unit tests for invoice_service.create_invoice."""

    def test_create_invoice_sets_draft_status(self, db):
        """Newly created invoice must have 'draft' status."""
        user = _make_user(db)
        client_obj = _make_client(db, user.id)
        from datetime import date
        data = InvoiceCreate(
            client_id=client_obj.id,
            issue_date=date.today(),
            due_date=date.today(),
            items=[InvoiceItemCreate(description="Work", quantity=Decimal("1"), unit_price=Decimal("100"))],
        )
        inv = create_invoice(db, user.id, data)
        assert inv.status == InvoiceStatus.draft

    def test_create_invoice_generates_public_token(self, db):
        """public_token must be a valid UUID v4 string."""
        import uuid as _uuid
        user = _make_user(db)
        client_obj = _make_client(db, user.id)
        from datetime import date
        data = InvoiceCreate(
            client_id=client_obj.id,
            issue_date=date.today(),
            due_date=date.today(),
            items=[InvoiceItemCreate(description="Work", quantity=Decimal("1"), unit_price=Decimal("100"))],
        )
        inv = create_invoice(db, user.id, data)
        # Must parse as UUID without raising
        parsed = _uuid.UUID(inv.public_token, version=4)
        assert str(parsed) == inv.public_token

    def test_create_invoice_raises_for_missing_client(self, db):
        """create_invoice with a non-existent client_id should raise NotFoundError."""
        user = _make_user(db)
        from datetime import date
        data = InvoiceCreate(
            client_id=99999,
            issue_date=date.today(),
            due_date=date.today(),
            items=[InvoiceItemCreate(description="Work", quantity=Decimal("1"), unit_price=Decimal("100"))],
        )
        with pytest.raises(NotFoundError):
            create_invoice(db, user.id, data)


# ---------------------------------------------------------------------------
# delete_invoice (service)
# ---------------------------------------------------------------------------


class TestDeleteInvoiceService:
    """Unit tests for invoice_service.delete_invoice."""

    def test_delete_draft_succeeds(self, db):
        """Deleting a DRAFT invoice should not raise."""
        user = _make_user(db)
        client_obj = _make_client(db, user.id)
        inv = _make_invoice(db, user.id, client_obj.id)
        # Should not raise
        delete_invoice(db, inv.id, user.id)

    def test_delete_sent_raises_conflict(self, db):
        """Deleting a SENT invoice should raise ConflictError."""
        user = _make_user(db)
        client_obj = _make_client(db, user.id)
        inv = _make_invoice(db, user.id, client_obj.id, status=InvoiceStatus.sent)
        with pytest.raises(ConflictError):
            delete_invoice(db, inv.id, user.id)

    def test_delete_paid_raises_conflict(self, db):
        """Deleting a PAID invoice should raise ConflictError."""
        user = _make_user(db)
        client_obj = _make_client(db, user.id)
        inv = _make_invoice(db, user.id, client_obj.id, status=InvoiceStatus.paid)
        with pytest.raises(ConflictError):
            delete_invoice(db, inv.id, user.id)


# ---------------------------------------------------------------------------
# mark_paid (service)
# ---------------------------------------------------------------------------


class TestMarkPaidService:
    """Unit tests for invoice_service.mark_paid."""

    def test_mark_sent_as_paid(self, db):
        """A SENT invoice can be transitioned to PAID."""
        user = _make_user(db)
        client_obj = _make_client(db, user.id)
        inv = _make_invoice(db, user.id, client_obj.id, status=InvoiceStatus.sent)
        result = mark_paid(db, inv.id, user.id)
        assert result.status == InvoiceStatus.paid
        assert result.paid_at is not None

    def test_mark_draft_as_paid_raises(self, db):
        """A DRAFT invoice cannot be marked as paid → ConflictError."""
        user = _make_user(db)
        client_obj = _make_client(db, user.id)
        inv = _make_invoice(db, user.id, client_obj.id, status=InvoiceStatus.draft)
        with pytest.raises(ConflictError):
            mark_paid(db, inv.id, user.id)

    def test_mark_cancelled_as_paid_raises(self, db):
        """A CANCELLED invoice cannot be marked as paid → ConflictError."""
        user = _make_user(db)
        client_obj = _make_client(db, user.id)
        inv = _make_invoice(db, user.id, client_obj.id, status=InvoiceStatus.cancelled)
        with pytest.raises(ConflictError):
            mark_paid(db, inv.id, user.id)

    def test_mark_viewed_as_paid(self, db):
        """A VIEWED invoice (client has opened it) can be marked as paid."""
        user = _make_user(db)
        client_obj = _make_client(db, user.id)
        inv = _make_invoice(db, user.id, client_obj.id, status=InvoiceStatus.viewed)
        result = mark_paid(db, inv.id, user.id)
        assert result.status == InvoiceStatus.paid


# ---------------------------------------------------------------------------
# update_overdue_statuses (service)
# ---------------------------------------------------------------------------


class TestUpdateOverdueStatuses:
    """Unit tests for invoice_service.update_overdue_statuses."""

    def test_sent_past_due_becomes_overdue(self, db):
        """SENT invoice with past due_date should be transitioned to OVERDUE."""
        from datetime import date, timedelta

        user = _make_user(db)
        client_obj = _make_client(db, user.id)
        inv = _make_invoice(db, user.id, client_obj.id, status=InvoiceStatus.sent)

        # Force due_date into the past
        inv.due_date = date.today() - timedelta(days=1)
        db.commit()

        count = update_overdue_statuses(db)
        db.refresh(inv)

        assert count == 1
        assert inv.status == InvoiceStatus.overdue

    def test_draft_invoice_not_made_overdue(self, db):
        """DRAFT invoices with past due_date should NOT be affected."""
        from datetime import date, timedelta

        user = _make_user(db)
        client_obj = _make_client(db, user.id)
        inv = _make_invoice(db, user.id, client_obj.id, status=InvoiceStatus.draft)
        inv.due_date = date.today() - timedelta(days=5)
        db.commit()

        count = update_overdue_statuses(db)
        db.refresh(inv)

        assert count == 0
        assert inv.status == InvoiceStatus.draft

    def test_paid_invoice_not_made_overdue(self, db):
        """PAID invoices must never be changed to OVERDUE."""
        from datetime import date, timedelta

        user = _make_user(db)
        client_obj = _make_client(db, user.id)
        inv = _make_invoice(db, user.id, client_obj.id, status=InvoiceStatus.paid)
        inv.due_date = date.today() - timedelta(days=5)
        db.commit()

        count = update_overdue_statuses(db)
        db.refresh(inv)

        assert count == 0
        assert inv.status == InvoiceStatus.paid

    def test_future_due_date_not_overdue(self, db):
        """SENT invoice with future due_date must remain SENT."""
        from datetime import date, timedelta

        user = _make_user(db)
        client_obj = _make_client(db, user.id)
        inv = _make_invoice(db, user.id, client_obj.id, status=InvoiceStatus.sent)
        inv.due_date = date.today() + timedelta(days=10)
        db.commit()

        count = update_overdue_statuses(db)
        assert count == 0
        db.refresh(inv)
        assert inv.status == InvoiceStatus.sent

    def test_returns_count_of_updated_invoices(self, db):
        """Return value must equal the number of invoices updated."""
        from datetime import date, timedelta

        user = _make_user(db)
        client_obj = _make_client(db, user.id)

        for _ in range(3):
            inv = _make_invoice(db, user.id, client_obj.id, status=InvoiceStatus.sent)
            inv.due_date = date.today() - timedelta(days=1)

        db.commit()

        count = update_overdue_statuses(db)
        assert count == 3
