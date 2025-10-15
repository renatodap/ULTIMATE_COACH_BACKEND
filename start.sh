#!/usr/bin/env sh
set -e

CMD=${APP_PROCESS:-api}

echo "[start] APP_PROCESS=$CMD"

if [ "$CMD" = "worker" ]; then
  # Run Celery worker. If container runs as root, drop privileges; otherwise run as current user.
  if [ "$(id -u)" = "0" ]; then
    exec celery -A app.core.celery_app.celery_app worker --loglevel="${CELERY_LOG_LEVEL:-INFO}" --uid=10001 --gid=10001
  else
    exec celery -A app.core.celery_app.celery_app worker --loglevel="${CELERY_LOG_LEVEL:-INFO}"
  fi
elif [ "$CMD" = "beat" ]; then
  if [ "$(id -u)" = "0" ]; then
    exec celery -A app.core.celery_app.celery_app beat --loglevel="${CELERY_LOG_LEVEL:-INFO}" --uid=10001 --gid=10001
  else
    exec celery -A app.core.celery_app.celery_app beat --loglevel="${CELERY_LOG_LEVEL:-INFO}"
  fi
else
  # api (default)
  exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
fi
