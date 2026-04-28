"""
Business logic for Reminder Rules, Reminder Logs, and the daily reminder check.

All user-facing functions accept an explicit user_id so that every database
query is scoped to the authenticated user — no cross-user data leakage is
possible. The process_all_rules function is intended to be called from the
Celery beat scheduler task.
"""

import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session, joinedload

from app.exceptions import ConflictError, NotFoundError
from app.models.invoice import Invoice, InvoiceStatus
from app.models.reminder import ReminderLog, ReminderRule, ReminderStatus, TriggerType
from app.schemas.reminder import ReminderRuleCreate, ReminderRuleUpdate

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# ReminderRule CRUD
# ---------------------------------------------------------------------------


def get_rules(db: Session, user_id: int) -> list[ReminderRule]:
    """Return all reminder rules owned by the given user, ordered by creation time."""
    return (
        db.query(ReminderRule)
        .filter(ReminderRule.user_id == user_id)
        .order_by(ReminderRule.created_at)
        .all()
    )


def get_rule(db: Session, rule_id: int, user_id: int) -> ReminderRule:
    """
    Return a single reminder rule by ID, scoped to the given user.

    :raises NotFoundError: if the rule does not exist or belongs to a different user.
    """
    rule = (
        db.query(ReminderRule)
        .filter(ReminderRule.id == rule_id, ReminderRule.user_id == user_id)
        .first()
    )
    if not rule:
        raise NotFoundError("Reminder rule")
    return rule


def create_rule(db: Session, user_id: int, data: ReminderRuleCreate) -> ReminderRule:
    """Create a new reminder rule for the given user."""
    rule = ReminderRule(user_id=user_id, **data.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    logger.info("Reminder rule created: id=%d user_id=%d", rule.id, user_id)
    return rule


def update_rule(
    db: Session, rule_id: int, user_id: int, data: ReminderRuleUpdate
) -> ReminderRule:
    """
    Partially update a reminder rule.

    Only fields explicitly provided in `data` are modified (None fields are skipped).

    :raises NotFoundError: if the rule does not exist or belongs to a different user.
    """
    rule = get_rule(db, rule_id, user_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(rule, field, value)
    db.commit()
    db.refresh(rule)
    logger.info("Reminder rule updated: id=%d user_id=%d", rule.id, user_id)
    return rule


def delete_rule(db: Session, rule_id: int, user_id: int) -> None:
    """
    Permanently delete a reminder rule.

    :raises NotFoundError: if the rule does not exist or belongs to a different user.
    """
    rule = get_rule(db, rule_id, user_id)
    db.delete(rule)
    db.commit()
    logger.info("Reminder rule deleted: id=%d user_id=%d", rule_id, user_id)


# ---------------------------------------------------------------------------
# Internal send helper
# ---------------------------------------------------------------------------


def _send_reminder(
    db: Session,
    invoice: Invoice,
    rule_id: int | None,
    subject: str,
) -> bool:
    """
    Attempt to send a reminder email and write an immutable ReminderLog record.

    :param db: Active database session.
    :param invoice: The invoice to remind about (must have .client eager-loaded).
    :param rule_id: The ReminderRule that triggered this send, or None for manual.
    :param subject: Email subject line.
    :returns: True if the email was accepted by the mail provider, False otherwise.
    """
    from app.services.email import send_reminder_email

    client_email: str = invoice.client.email or ""
    client_name: str = invoice.client.name

    try:
        send_reminder_email(
            to_email=client_email,
            client_name=client_name,
            invoice_number=invoice.invoice_number,
            amount=f"{invoice.currency} {invoice.total}",
            due_date=str(invoice.due_date),
            public_token=invoice.public_token,
        )
        log = ReminderLog(
            invoice_id=invoice.id,
            rule_id=rule_id,
            sent_at=datetime.now(timezone.utc),
            status=ReminderStatus.sent,
            email_to=client_email,
            subject=subject,
        )
        db.add(log)
        db.commit()
        logger.info(
            "Reminder sent for invoice %s to %s",
            invoice.invoice_number,
            client_email,
        )
        return True
    except Exception as exc:
        log = ReminderLog(
            invoice_id=invoice.id,
            rule_id=rule_id,
            sent_at=datetime.now(timezone.utc),
            status=ReminderStatus.failed,
            email_to=client_email,
            subject=subject,
            error_message=str(exc),
        )
        db.add(log)
        db.commit()
        logger.error(
            "Reminder failed for invoice %s: %s",
            invoice.invoice_number,
            exc,
        )
        return False


# ---------------------------------------------------------------------------
# Manual reminder
# ---------------------------------------------------------------------------


def send_manual_reminder(db: Session, invoice_id: int, user_id: int) -> bool:
    """
    Immediately send a one-off reminder for a specific invoice.

    :raises NotFoundError: if the invoice does not exist or belongs to a different user.
    :raises ConflictError: if the invoice is already paid or cancelled.
    :returns: True if the email was delivered successfully, False otherwise.
    """
    invoice = (
        db.query(Invoice)
        .options(joinedload(Invoice.client))
        .filter(Invoice.id == invoice_id, Invoice.user_id == user_id)
        .first()
    )
    if not invoice:
        raise NotFoundError("Invoice")
    if invoice.status in (InvoiceStatus.paid, InvoiceStatus.cancelled):
        raise ConflictError("Cannot send reminder for paid or cancelled invoices")

    subject = f"Payment Reminder: Invoice {invoice.invoice_number}"
    return _send_reminder(db, invoice, None, subject)


# ---------------------------------------------------------------------------
# Reminder logs
# ---------------------------------------------------------------------------


def get_logs(
    db: Session,
    user_id: int,
    invoice_id: int | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[ReminderLog]:
    """
    Return reminder logs for invoices owned by the given user.

    Optionally filter by a specific invoice. Results are ordered newest-first.
    """
    q = (
        db.query(ReminderLog)
        .join(Invoice)
        .filter(Invoice.user_id == user_id)
    )
    if invoice_id is not None:
        q = q.filter(ReminderLog.invoice_id == invoice_id)
    return q.order_by(ReminderLog.sent_at.desc()).offset(skip).limit(limit).all()


# ---------------------------------------------------------------------------
# Scheduled batch processing
# ---------------------------------------------------------------------------


def process_all_rules(db: Session) -> dict[str, int]:
    """
    Evaluate all active reminder rules against eligible invoices and send
    any reminders that are due today.

    This function is designed to be called once per day from the Celery beat
    scheduler task ``check_reminders``.

    Rule matching logic:
        before_due: fire when due_date == today + days_offset
        on_due:     fire when due_date == today
        after_due:  fire when due_date == today - days_offset

    Only invoices in statuses sent / viewed / overdue are eligible — draft,
    paid, and cancelled invoices are excluded.

    :returns: A summary dict e.g. ``{"sent": 5}``.
    """
    today: date = date.today()
    eligible_statuses = [InvoiceStatus.sent, InvoiceStatus.viewed, InvoiceStatus.overdue]

    rules: list[ReminderRule] = (
        db.query(ReminderRule)
        .filter(ReminderRule.is_active == True)  # noqa: E712
        .all()
    )

    sent_count: int = 0

    for rule in rules:
        if rule.trigger_type == TriggerType.before_due:
            target_date = today + timedelta(days=rule.days_offset)
        elif rule.trigger_type == TriggerType.on_due:
            target_date = today
        else:  # after_due
            target_date = today - timedelta(days=rule.days_offset)

        invoices: list[Invoice] = (
            db.query(Invoice)
            .options(joinedload(Invoice.client))
            .filter(
                Invoice.user_id == rule.user_id,
                Invoice.due_date == target_date,
                Invoice.status.in_(eligible_statuses),
            )
            .all()
        )

        for invoice in invoices:
            subject = f"Payment Reminder: Invoice {invoice.invoice_number}"
            if _send_reminder(db, invoice, rule.id, subject):
                sent_count += 1

    logger.info("Reminder check complete: %d reminder(s) sent", sent_count)
    return {"sent": sent_count}
