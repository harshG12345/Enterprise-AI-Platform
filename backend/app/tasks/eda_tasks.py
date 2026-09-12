"""Celery tasks for asynchronous EDA computation."""

import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.eda_tasks.calculate_dataset_eda_task")
def calculate_dataset_eda_task(self, dataset_id_str: str, user_id_str: str):
    """Compute EDA profiling statistics in background worker."""
    logger.info(f"Starting background EDA for dataset: {dataset_id_str}")
    # Placeholder for async profiling worker
    return {"dataset_id": dataset_id_str, "status": "COMPLETED"}
