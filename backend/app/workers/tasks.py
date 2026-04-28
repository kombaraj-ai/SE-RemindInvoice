"""
Celery task definitions for RemindInvoice.

Tasks are registered with the Celery beat scheduler. Each task opens its
own database session, delegates to the relevant service layer, and closes
the session in a finally block to prevent connection leaks.
"""

import logging

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.tasks.check_reminders")
def check_reminders() -> dict[str, int]:
    """
    Evaluate all active reminder rules against eligible invoices and send
    any reminder emails that are due today.

    Delegates to ``reminder_service.process_all_rules`` which handles
    rule matching logic (before_due / on_due / after_due) and writes
    a ReminderLog record for every send attempt.

    :returns: ``{"sent": N}`` where N is the number of emails dispatched.
    """
    from app.database import SessionLocal
    from app.services.reminder_service import process_all_rules

    db = SessionLocal()
    try:
        result = process_all_rules(db)
        logger.info("check_reminders task complete: %s", result)
        return result
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.update_overdue_invoices")
def update_overdue_invoices() -> dict[str, int]:
    """
    Transition all SENT / VIEWED invoices whose due_date is in the past to
    OVERDUE status.

    Delegates to ``invoice_service.update_overdue_statuses`` which performs
    a targeted UPDATE and returns the count of rows affected.

    :returns: ``{"updated": N}`` where N is the number of invoices transitioned.
    """
    from app.database import SessionLocal
    from app.services.invoice_service import update_overdue_statuses

    db = SessionLocal()
    try:
        count = update_overdue_statuses(db)
        logger.info("update_overdue_invoices task complete: %d updated", count)
        return {"updated": count}
    finally:
        db.close()
