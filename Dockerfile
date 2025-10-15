FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==1.7.1

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root --only main

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Entrypoint switches between API / Celery worker / Celery beat via APP_PROCESS env
COPY start.sh ./
RUN chmod +x ./start.sh \
    && groupadd -g 10001 app || true \
    && useradd -m -u 10001 -g 10001 app \
    && chown -R app:app /app

# Run as non-root user to avoid privilege warnings
USER app
CMD ["sh", "./start.sh"]
