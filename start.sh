#!/usr/bin/env sh
set -e

CMD=${APP_PROCESS:-api}

echo "[start] APP_PROCESS=$CMD"

if [ "$CMD" = "worker" ]; then
  exec celery -A app.core.celery_app.celery_app worker --loglevel="${CELERY_LOG_LEVEL:-INFO}"
elif [ "$CMD" = "beat" ]; then
  exec celery -A app.core.celery_app.celery_app beat --loglevel="${CELERY_LOG_LEVEL:-INFO}"
else
  # api (default)
  exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
fi

