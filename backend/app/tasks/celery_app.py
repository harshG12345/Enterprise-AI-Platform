"""Celery Application and Asynchronous Task Configuration."""

import os

from celery import Celery

from app.config.settings import get_settings

settings = get_settings()

# Initialize Celery app
celery_app = Celery(
    "enterprise_ai_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.training_tasks",
        "app.tasks.eda_tasks",
        "app.tasks.prediction_tasks",
    ],
)

# Celery Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max for training
    task_soft_time_limit=3300,
    worker_prefetch_multiplier=1,
    worker_concurrency=int(os.getenv("CELERY_CONCURRENCY", "4")),
    result_expires=86400,  # 24 hours
    task_always_eager=os.getenv("CELERY_TASK_ALWAYS_EAGER", "false").lower() in ("true", "1", "yes"),
)
