#!/usr/bin/env sh
set -e

CMD=${APP_PROCESS:-api}

echo "[start] APP_PROCESS=$CMD"

if [ "$CMD" = "worker" ]; then
  # Run Celery worker. Avoid privilege dropping flags (can fail on PaaS)
  # Allow tuning via env: CELERY_WORKER_CONCURRENCY, CELERY_POOL
  exec celery -A app.core.celery_app.celery_app worker \
    --loglevel="${CELERY_LOG_LEVEL:-INFO}" \
    --concurrency="${CELERY_WORKER_CONCURRENCY:-2}" \
    --pool="${CELERY_POOL:-prefork}"
elif [ "$CMD" = "beat" ]; then
  # Celery beat scheduler
  exec celery -A app.core.celery_app.celery_app beat --loglevel="${CELERY_LOG_LEVEL:-INFO}"
else
  # api (default)
  exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
fi
