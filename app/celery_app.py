from celery import Celery

from app.settings import settings


celery_app = Celery(
    "calculation",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.calculate_pi"],
)

celery_app.conf.update(
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    timezone="Europe/Berlin",
)
