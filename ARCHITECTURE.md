# ULTIMATE COACH Backend Architecture

> **Last Updated:** 2025-10-12
> **Purpose:** Single source of truth for backend architecture, patterns, and standards

---

## Table of Contents

1. [Overview](#overview)
2. [Project Structure](#project-structure)
3. [Authentication Flow](#authentication-flow)
4. [API Endpoints](#api-endpoints)
5. [Database Schema](#database-schema)
6. [Logging Standards](#logging-standards)
7. [Error Handling](#error-handling)
8. [Testing Strategy](#testing-strategy)
9. [Deployment](#deployment)

---

## Overview

### Tech Stack

- **Framework:** FastAPI 0.104+
- **Database:** PostgreSQL via Supabase
- **Auth:** Supabase Auth (JWT tokens in httpOnly cookies)
- **Logging:** structlog (JSON structured logging)
- **Validation:** Pydantic v2
- **Task Queue:** Celery + Redis (future)
- **Monitoring:** Sentry (production)

### Core Principles

1. **Security First:** httpOnly cookies, RLS policies, validated inputs
2. **Type Safety:** Pydantic models for all requests/responses
3. **Observability:** Structured logging everywhere
4. **Consistency:** Standardized patterns across all endpoints
5. **Documentation:** Code is self-documenting with OpenAPI

---

## Project Structure

```
app/
├── api/
│   ├── dependencies.py          # FastAPI dependencies (auth, etc)
│   └── v1/
│       ├── auth.py              # Authentication endpoints
│       ├── users.py             # User profile endpoints
│       ├── health.py            # Health check endpoint
│       └── [future modules]
├── services/
│   ├── auth_service.py          # Auth business logic
│   ├── supabase_service.py      # Database operations
│   └── [future services]
├── config.py                    # Environment configuration
└── main.py                      # FastAPI app initialization

migrations/
└── 001_IMPROVED_schema.sql      # Database schema

tests/
└── [future test modules]
```

### File Organization Rules

- **`api/`**: HTTP layer only - route definitions, request/response models
- **`services/`**: Business logic - reusable, testable, no HTTP knowledge
- **`models/`** (future): Pydantic models for validation
- **One module per domain**: auth, users, nutrition, activities, coach

---

## Authentication Flow

### 1. Signup/Login Flow

```
Client                 Backend                 Supabase
  |                      |                        |
  |--POST /auth/signup-->|                        |
  |    (email, pwd)      |                        |
  |                      |--createUser---------->|
  |                      |<--user + tokens-------|
  |                      |                        |
  |                      |--createProfile------->|
  |                      |<--profile-------------|
  |                      |                        |
  |<--Set-Cookie---------|                        |
  |   (httpOnly cookies) |                        |
  |<--AuthResponse-------|                        |
```

### 2. Protected Route Flow

```
Client                 Backend                 Supabase
  |                      |                        |
  |--GET /users/me------>|                        |
  | (with cookies)       |                        |
  |                      |--get_current_user---->|
  |                      |   (validate token)     |
  |                      |<--user data-----------|
  |                      |                        |
  |                      |--getProfile---------->|
  |                      |<--profile data--------|
  |                      |                        |
  |<--ProfileResponse----|                        |
```

### 3. Token Storage

- **Access Token:** 7 days, httpOnly, secure, sameSite=lax
- **Refresh Token:** 30 days, httpOnly, secure, sameSite=lax
- **Never** stored in localStorage or exposed to JavaScript

### 4. Using Auth Middleware

```python
from app.api.dependencies import get_current_user

@router.get("/protected-route")
async def protected_route(user: dict = Depends(get_current_user)):
    # user is automatically injected and validated
    # user = { "id": "uuid", "email": "...", "full_name": "...", ... }
    return {"message": f"Hello {user['email']}"}
```

---

## API Endpoints

### Current Endpoints (v1)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/` | No | API info |
| GET | `/api/v1/health` | No | Health check |
| POST | `/api/v1/auth/signup` | No | Create account |
| POST | `/api/v1/auth/login` | No | Login |
| POST | `/api/v1/auth/logout` | Yes | Logout |
| POST | `/api/v1/auth/refresh` | No | Refresh token |
| GET | `/api/v1/users/me` | Yes | Get current user |
| PATCH | `/api/v1/users/me` | Yes | Update profile |

### Future Endpoints

```
/api/v1/nutrition/
  - foods/search          # Search food database
  - foods/custom          # Create custom food
  - meals                 # CRUD meals
  - meals/{id}/items      # Meal items

/api/v1/activities/
  - activities            # CRUD activities
  - activities/summary    # Daily/weekly stats

/api/v1/coach/
  - conversations         # CRUD conversations
  - conversations/{id}/messages  # Chat messages
  - stream                # SSE streaming endpoint
```

---

## Database Schema

### Core Tables

1. **profiles** - User profiles (1:1 with auth.users)
2. **foods** - Food database (public + user custom)
3. **food_servings** - Multiple serving sizes per food
4. **meals** - Meal logs
5. **meal_items** - Foods in meals (references serving_id)
6. **activities** - Activity logs with JSONB metrics
7. **coach_conversations** - Chat conversations
8. **coach_messages** - Chat messages
9. **embeddings** - RAG vectors for personalization

### Key Patterns

- **Food Servings:** Industry standard - foods stored per 100g, servings reference food_id
- **Activity Metrics:** Flexible JSONB for activity-type specific data
- **RLS Policies:** Every table has Row Level Security enabled
- **Soft Deletes:** Use `deleted_at` timestamp instead of hard deletes

See `migrations/001_IMPROVED_schema.sql` for full schema.

---

## Logging Standards

### Structured Logging with structlog

All logs are JSON-formatted with consistent fields:

```python
import structlog

logger = structlog.get_logger()

# ✅ GOOD - Structured with context
logger.info("user_login_success",
    user_id=user_id,
    email=email,
    ip=request.client.host
)

# ❌ BAD - Unstructured string
logger.info(f"User {email} logged in from {ip}")
```

### Log Levels

- **DEBUG:** Detailed diagnostic info (dev only)
- **INFO:** Normal operations (user actions, API calls)
- **WARNING:** Recoverable issues (rate limits, retries)
- **ERROR:** Failed operations (caught exceptions)
- **CRITICAL:** System failures (database down, etc)

### Standard Log Events

```python
# Auth events
logger.info("user_signup_success", user_id=..., email=...)
logger.info("user_login_success", user_id=..., email=...)
logger.warning("auth_missing_token", path=...)
logger.warning("auth_invalid_token", path=...)

# Database events
logger.info("profile_created", user_id=...)
logger.info("meal_created", user_id=..., meal_id=...)
logger.error("db_query_failed", table=..., error=...)

# API events
logger.info("api_request", method=..., path=..., status=...)
logger.error("api_error", method=..., path=..., error=...)
```

### Viewing Logs

```bash
# Development
python -m app.main

# Production (JSON logs for log aggregation)
# Logs automatically sent to stdout for Docker/K8s
```

---

## Error Handling

### Standard Error Response

All errors return consistent JSON:

```json
{
  "detail": "Human-readable error message",
  "status": 400,
  "type": "ValidationError"
}
```

### Error Hierarchy

1. **HTTP Exceptions** - `raise HTTPException(status_code=400, detail="...")`
2. **Validation Errors** - Pydantic automatically handles
3. **Database Errors** - Caught in services, logged, re-raised as HTTPException
4. **Unhandled Errors** - Global exception handler catches all

### Best Practices

```python
# ✅ GOOD - Specific error with context
if not user:
    logger.error("user_not_found", user_id=user_id)
    raise HTTPException(
        status_code=404,
        detail="User not found"
    )

# ❌ BAD - Generic error
if not user:
    raise Exception("Error")
```

---

## Testing Strategy

### Test Structure (Future)

```
tests/
├── test_auth.py         # Auth endpoints
├── test_users.py        # User endpoints
├── test_services/       # Service layer tests
└── test_integration/    # End-to-end tests
```

### Running Tests

```bash
pytest tests/ -v
pytest tests/ --cov=app  # With coverage
```

---

## Deployment

### Environment Variables

See `.env.example` for required variables.

**Critical:** Never commit `.env` to git!

### Production Checklist

- [ ] Set `ENVIRONMENT=production`
- [ ] Set `DEBUG=false`
- [ ] Configure `SENTRY_DSN`
- [ ] Use strong `JWT_SECRET`
- [ ] Set `CORS_ORIGINS` to frontend domain
- [ ] Enable SSL/TLS (secure=True for cookies)
- [ ] Set up log aggregation (Datadog, CloudWatch, etc)

### Running in Production

```bash
# Docker
docker build -t ultimate-coach-backend .
docker run -p 8000:8000 --env-file .env ultimate-coach-backend

# Direct
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## Adding New Endpoints

### Step-by-Step Guide

1. **Create route file** in `app/api/v1/[domain].py`
2. **Create service** in `app/services/[domain]_service.py`
3. **Use dependencies** for auth: `user = Depends(get_current_user)`
4. **Add structured logging** for all operations
5. **Register router** in `app/main.py`
6. **Add to this doc** in API Endpoints section

### Template

```python
# app/api/v1/example.py
import structlog
from fastapi import APIRouter, Depends, HTTPException
from app.api.dependencies import get_current_user

logger = structlog.get_logger()
router = APIRouter()

@router.get("/example")
async def example_endpoint(user: dict = Depends(get_current_user)):
    """Example endpoint with auth."""
    try:
        logger.info("example_action", user_id=user["id"])
        # Your logic here
        return {"message": "Success"}
    except Exception as e:
        logger.error("example_error", user_id=user["id"], error=str(e))
        raise HTTPException(500, "Operation failed")
```

---

## Questions?

If anything is unclear or inconsistent, update this document immediately.
This is the **single source of truth** - keep it current!
