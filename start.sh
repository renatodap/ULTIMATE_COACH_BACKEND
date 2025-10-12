#!/bin/bash
# Railway startup script - ensures PORT environment variable is properly expanded

exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
