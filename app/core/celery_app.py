"""
Celery application factory for Ultimate Coach.

Configured via environment variables:
  - CELERY_BROKER_URL / REDIS_URL
  - CELERY_RESULT_BACKEND / REDIS_URL

Tasks are discovered from workers.coach_tasks.
"""

from __future__ import annotations

import os
from celery import Celery


broker_url = os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://localhost:6379/0"))
result_backend = os.getenv("CELERY_RESULT_BACKEND", os.getenv("REDIS_URL", "redis://localhost:6379/1"))

celery_app = Celery(
    "ultimate_coach",
    broker=broker_url,
    backend=result_backend,
    include=["workers.coach_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    result_expires=3600,
)

