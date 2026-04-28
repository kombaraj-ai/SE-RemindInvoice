"""
Celery application instance for RemindInvoice background tasks.

Start the worker with:
    celery -A app.workers.celery_app worker --loglevel=info

Start the beat scheduler with:
    celery -A app.workers.celery_app beat --loglevel=info
"""

from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "remindinvoice",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    beat_schedule={
        "check-reminders-daily": {
            "task": "app.workers.tasks.check_reminders",
            "schedule": crontab(hour=8, minute=0),  # 08:00 UTC daily
        },
        "update-overdue-invoices-daily": {
            "task": "app.workers.tasks.update_overdue_invoices",
            "schedule": crontab(hour=8, minute=0),  # 08:00 UTC daily
        },
    },
)
