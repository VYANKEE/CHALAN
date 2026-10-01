"""
Celery app - broker aur result backend dono Redis (ek hi service, simplest
setup, alag broker/backend chahiye hi nahi is scale ke liye). Worker alag
process me chalta hai (`celery -A src.api.celery_app worker`) taaki model
inference API request thread ko block na kare - upload turant job_id return
kar sake, actual processing background me ho.
"""
from celery import Celery

from src.api.config import settings

celery_app = Celery(
    "invoice_tasks",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["src.api.tasks"],
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
)
