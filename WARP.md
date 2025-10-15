# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

---

## Project Overview

**ULTIMATE COACH Backend** (also known as SHARPENED) - FastAPI REST API for AI-powered fitness and nutrition coaching.

**Tech Stack:**
- **Framework:** FastAPI 0.109+
- **Language:** Python 3.11+
- **Database:** Supabase (PostgreSQL)
- **Auth:** httpOnly cookies (Supabase JWT)
- **AI Providers:** Anthropic Claude, OpenAI, Groq, OpenRouter
- **Background Jobs:** Celery + Redis
- **Logging:** structlog (JSON-formatted)
- **Monitoring:** Sentry
- **Deployment:** Docker + Railway/Fly.io

---

## Development Commands

### Server

```bash
# Development server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# With specific log level
LOG_LEVEL=DEBUG uvicorn app.main:app --reload

# Production server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**API Documentation:** http://localhost:8000/docs (Swagger UI)

### Testing

```bash
# Run all tests
pytest

# Run unit tests only
pytest -m unit

# Run integration tests only
pytest -m integration

# Run with coverage (requires 80%)
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_nutrition_service.py

# Verbose output
pytest -v
```

### Code Quality

```bash
# Type checking
mypy app/

# Code formatting
black app/
ruff app/

# Linting
ruff check app/
```

### Dependencies

```bash
# With Poetry (preferred - see Dockerfile)
poetry install

# With pip
pip install -r requirements.txt
```

---

## Architecture Patterns

### Service Layer Pattern

**CRITICAL:** All business logic belongs in services, not routes.

```
HTTP Request
  ↓
FastAPI Route (app/api/v1/*.py)
  ↓
Dependency Injection (auth, DB connection)
  ↓
Service Layer (app/services/*.py)
  ↓
Supabase Service
  ↓
PostgreSQL Database
```

**Example:**
```python
# ✅ GOOD: Route delegates to service
@router.post("/meals")
async def create_meal(
    data: MealCreate,
    service: MealService = Depends(),
    user = Depends(get_current_user)
):
    return await service.create_meal(user.id, data)

# ❌ BAD: Business logic in route
@router.post("/meals")
async def create_meal(data: MealCreate):
    # Direct database calls, calculations, etc.
```

### Multi-AI Provider Architecture

**Cost Optimization:** $0.01-$0.15 per interaction (average $0.035 with smart routing)

The system uses **3-tier intelligent routing** to optimize cost and speed:

1. **Canned Responses** (0ms, $0.00) - Pattern-matched common queries
2. **Groq (Llama 3.1)** (~500ms, $0.01) - Simple/medium complexity
3. **Claude 3.5 Sonnet** (~1500ms, $0.10-$0.15) - Complex reasoning, tool calling

**Routing Logic:**
```python
# services/unified_coach_service.py
1. Classify message: CHAT vs LOG (Groq)
2. Detect language (langdetect)
3. Analyze complexity: trivial/simple/complex (Groq)
4. Route to model:
   - Trivial → Canned response
   - Simple → Groq
   - Complex → Claude
5. Execute tools on-demand (agentic)
6. Format response (i18n)
7. Vectorize in background (Celery)
```

**Key Services:**
- `unified_coach_service.py` - Main orchestrator
- `message_classifier_service.py` - CHAT vs LOG classification
- `complexity_analyzer_service.py` - AI model routing
- `tool_service.py` - Agentic tool calling (database queries)
- `conversation_memory_service.py` - RAG-based context retrieval
- `security_service.py` - Prompt injection protection
- `consultation_ai_service.py` - Advanced consultation (1000+ lines)

### Authentication: httpOnly Cookies Only

**CRITICAL:** Never use Bearer tokens or API keys in headers.

```python
# ✅ GOOD: JWT in httpOnly cookie
from app.api.dependencies import get_current_user

@router.get("/protected")
async def protected_route(user = Depends(get_current_user)):
    return {"user_id": user.id}

# ❌ BAD: Bearer token in Authorization header
# Never implement this pattern
```

**Why:** XSS protection - JavaScript cannot access httpOnly cookies.

**Auth Flow:**
1. User sends credentials to `/api/v1/auth/login`
2. `AuthService` verifies password
3. Generate Supabase JWT token
4. Set httpOnly cookie with JWT
5. Future requests: `get_current_user()` validates cookie

### Background Tasks with Celery

**Workers:** `workers/coach_tasks.py`

```python
# Task types:
- vectorize_message() - Generate embeddings for RAG ($0.000002/message)
- update_conversation_analytics() - Cache message counts
- archive_old_embeddings() - Cleanup old vectors (90 days)
```

**Running Workers:**
```bash
celery -A workers.coach_tasks worker --loglevel=info
```

**Redis:** Required for Celery broker and result backend.

### Database with Supabase RLS

**CRITICAL:** Row Level Security is enabled on all user tables.

```python
# ⚠️ Service role key bypasses RLS
# Use with caution - only for admin operations

# ✅ GOOD: Use user's JWT for queries
from app.services.supabase_service import SupabaseService

service = SupabaseService()
service.supabase.table('meals').select('*').eq('user_id', user.id).execute()

# ❌ BAD: Service role for user queries
# This bypasses RLS and can leak data across users
```

**Tables:**
- `profiles` - User profiles (1:1 with auth.users)
- `foods` / `food_servings` - Nutrition database (per 100g pattern)
- `meals` / `meal_items` - Meal logging
- `activities` - Workout logs with JSONB metrics
- `activity_templates` - Auto-matching workout templates
- `body_metrics` - Weight, body composition tracking
- `coach_conversations` / `coach_messages` - AI chat
- `coach_message_embeddings` - RAG vectors
- `consultation_sessions` / `consultation_keys` - Gated consultations

### JSONB Activity Metrics

**Why JSONB?** Different activities have wildly different data requirements.

```python
# Cardio
{
    "distance_km": 5.2,
    "avg_heart_rate": 145,
    "avg_pace": "5:47/km",
    "elevation_gain_m": 120
}

# Strength Training
{
    "exercises": [
        {
            "name": "Bench Press",
            "sets": 3,
            "reps": 5,
            "weight_kg": 102,
            "rpe": 8
        }
    ],
    "total_volume_kg": 2500
}

# Sports
{
    "sport_type": "tennis",
    "opponent": "John Doe",
    "score": "6-4, 6-3"
}
```

**Alternative:** Separate tables per activity type → massive complexity ❌

### Structured Logging with structlog

**CRITICAL:** Never use `print()` statements.

```python
import structlog

logger = structlog.get_logger()

# ✅ GOOD: JSON-formatted with context
logger.info(
    "user_action",
    user_id=user.id,
    action="meal_created",
    meal_id=meal.id,
    calories=450
)

# ✅ Error logging with exception
try:
    risky_operation()
except Exception as e:
    logger.error(
        "operation_failed",
        error=str(e),
        error_type=type(e).__name__,
        user_id=user.id,
        exc_info=True  # Includes stack trace
    )
    raise

# ❌ BAD: Unstructured string
print(f"User {user.id} created meal")
logger.info(f"Error: {e}")
```

**Output:**
```json
{
  "event": "user_action",
  "user_id": "123",
  "action": "meal_created",
  "meal_id": "456",
  "calories": 450,
  "timestamp": "2025-10-14T06:00:00Z",
  "level": "info"
}
```

---

## Critical Development Rules

### 1. Use Structured Logging
❌ BAD: `print(f"User {user_id} logged in")`  
✅ GOOD: `logger.info("user_login", user_id=user_id, email=email)`

### 2. Service Layer for Business Logic
❌ BAD: Database calls in route handlers  
✅ GOOD: Route → Service → Database

### 3. Pydantic Models for Validation
❌ BAD: Manual dict validation  
✅ GOOD: Pydantic models in `app/models/`

### 4. httpOnly Cookies Only
❌ BAD: Bearer tokens, API keys in headers  
✅ GOOD: JWT in httpOnly cookie

### 5. RLS Awareness
⚠️ WARNING: Service role bypasses RLS  
✅ GOOD: Use user's JWT for queries

---

## API Endpoints

**Base URL:** http://localhost:8000

### Authentication
- `POST /api/v1/auth/signup` - Create account
- `POST /api/v1/auth/login` - Login (sets httpOnly cookie)
- `POST /api/v1/auth/logout` - Logout (clears cookie)
- `POST /api/v1/auth/refresh` - Refresh token

### Users
- `GET /api/v1/users/me` - Get current user profile
- `PATCH /api/v1/users/me` - Update profile

### Dashboard
- `GET /api/v1/dashboard` - Daily summary (nutrition + activity)

### Nutrition
- `GET /api/v1/foods/search` - Search food database
- `POST /api/v1/foods/custom` - Create custom food
- `GET /api/v1/meals` - List meals (date filtering)
- `POST /api/v1/meals` - Log meal
- `DELETE /api/v1/meals/{id}` - Delete meal
- `POST /api/v1/quick-meals` - Log quick meal from template

### Activities
- `GET /api/v1/activities` - List activities (date filtering)
- `POST /api/v1/activities` - Log activity
- `PATCH /api/v1/activities/{id}` - Update activity
- `DELETE /api/v1/activities/{id}` - Soft delete activity
- `GET /api/v1/activities/summary` - Daily summary (calories, METs)

### Activity Templates
- `GET /api/v1/templates` - List user templates
- `POST /api/v1/templates` - Create template
- `PUT /api/v1/templates/{id}` - Update template
- `DELETE /api/v1/templates/{id}` - Delete template

### Body Metrics
- `GET /api/v1/body-metrics` - List body metrics
- `POST /api/v1/body-metrics` - Log body metric
- `DELETE /api/v1/body-metrics/{id}` - Delete metric

### Exercise Sets
- `GET /api/v1/exercise-sets` - List exercise sets
- `POST /api/v1/exercise-sets` - Log exercise set

### AI Coach
- `GET /api/v1/coach/conversations` - List conversations
- `POST /api/v1/coach/conversations` - Create conversation
- `POST /api/v1/coach/conversations/{id}/messages` - Send message
- `GET /api/v1/coach/conversations/{id}/messages` - Get messages

### Health
- `GET /api/v1/health` - Health check
- `GET /api/v1/health/db` - Database health

---

## Environment Variables

### Required

```bash
# Database (Supabase)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
JWT_SECRET=your-jwt-secret

# Security
JWT_SECRET=your-secret-key
```

### AI Providers

**Note:** User prefers OpenRouter exclusively.

```bash
# AI APIs (at least one required for coach features)
OPENAI_API_KEY=sk-...          # For embeddings ($0.02/M tokens)
ANTHROPIC_API_KEY=sk-ant-...   # For Claude 3.5 Sonnet
GROQ_API_KEY=gsk_...           # For Llama routing
OPENROUTER_API_KEY=sk-or-...   # Preferred by user
```

### Optional

```bash
# Environment
ENVIRONMENT=development  # or "production"
DEBUG=True
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
ALLOW_ALL_ORIGINS=False

# Background Jobs
REDIS_URL=redis://localhost:6379
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Monitoring
SENTRY_DSN=https://...@sentry.io/...

# Security (webhooks, cron jobs)
CRON_SECRET=your-secret
WEBHOOK_SECRET=your-secret
```

---

## Database Migrations

**Location:** `migrations/` directory

### Applying Migrations

**Option 1: Supabase Dashboard (Recommended)**
1. Navigate to SQL Editor
2. Copy migration file contents
3. Paste and run
4. Verify success

**Option 2: Supabase CLI**
```bash
supabase link --project-ref YOUR_PROJECT_REF
supabase db push
```

**Option 3: Direct PostgreSQL**
```bash
psql "postgresql://postgres:[PASSWORD]@db.PROJECT_REF.supabase.co:5432/postgres" \
  -f migrations/001_IMPROVED_schema.sql
```

### Migration Rules

- **Never modify applied migrations** - Create new ones instead
- **Test locally first** - Use test project if possible
- **Apply in order** - Migrations are numbered sequentially
- **Document changes** - Update migration status in `migrations/README.md`

**See:** `migrations/README.md` for detailed migration guide.

---

## Testing

**Directory Structure:**
```
tests/
├── conftest.py           # Pytest fixtures
├── unit/                 # Unit tests
│   ├── test_health.py
│   └── test_nutrition_service.py
└── integration/          # Integration tests
    └── test_nutrition_api.py
```

**Markers:**
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow tests

**Coverage Requirement:** 80% (enforced by pytest.ini)

---

## Advanced Features

### Consultation System

**Status:** Backend complete, frontend integration pending

- **Gating:** One-time use consultation keys for cost control
- **Features:** Natural conversation, 7-section system prompts, progress tracking
- **Service:** `app/services/consultation_ai_service.py` (1000+ lines)
- **Documentation:** 
  - `CONSULTATION_KEYS_GUIDE.md` - Key system
  - `CONSULTATION_SECURITY.md` - 5-layer security
  - `CONSULTATION_MEMORY_AND_SEEDING.md` - Memory system

**Warning:** This is a complex, production-ready feature. Read docs before modifying.

### Activity Templates

**Auto-matching workout templates:**
- User creates templates (e.g., "Morning Run")
- System auto-matches future activities by name/category
- Template suggestions pre-fill metrics
- Learning from match history

**Tables:**
- `activity_templates` - Template definitions
- `activity_template_matches` - Match history for learning
- `activity_duplicates` - Duplicate detection & resolution

### GPS Tracking

**Status:** Feature flagged (optional)

- **Table:** `gps_tracks` - GPS route data with PostGIS LINESTRING
- **Feature Flag:** `GPS_TRACKING` environment variable
- **Use Case:** Running/cycling route visualization

### Wearable Integration

**Status:** Feature flagged (optional)

- **Providers:** Garmin, Strava, Apple Health, Fitbit
- **Table:** `wearable_connections` - OAuth connections
- **Sync:** Background import of activities/metrics
- **Duplicate Detection:** Prevents duplicate logs from multiple sources

### Multi-language i18n Support

**Service:** `app/services/i18n_service.py`

- Auto-detects user language (langdetect)
- Translates AI responses
- Stores preferred language in user profile
- Error codes for frontend translation

**Supported Languages:**
- English (default)
- Portuguese (Brazilian)
- Spanish
- (Extensible)

### Quick Meal Templates

**Fast meal logging:**
- Pre-configured meals (e.g., "Protein Shake")
- One-click logging with adjustable serving sizes
- Stored in `quick_meals` table

---

## File Structure

```
app/
├── api/
│   ├── dependencies.py          # Auth, DB injection
│   └── v1/                      # API v1 endpoints
│       ├── health.py            # Health check
│       ├── auth.py              # Authentication
│       ├── users.py             # User profile
│       ├── onboarding.py        # Onboarding
│       ├── dashboard.py         # Dashboard summary
│       ├── foods.py             # Food search
│       ├── meals.py             # Meal logging
│       ├── quick_meals.py       # Quick meal templates
│       ├── activities.py        # Activity logging
│       ├── templates.py         # Activity templates
│       ├── body_metrics.py      # Body tracking
│       ├── exercise_sets.py     # Exercise logging
│       └── coach.py             # AI coach chat
├── services/
│   ├── supabase_service.py      # Database abstraction
│   ├── auth_service.py          # Auth business logic
│   ├── unified_coach_service.py # AI orchestrator (main)
│   ├── message_classifier_service.py  # CHAT vs LOG
│   ├── complexity_analyzer_service.py # Model routing
│   ├── tool_service.py          # Agentic tools
│   ├── conversation_memory_service.py # RAG context
│   ├── security_service.py      # Prompt injection protection
│   ├── consultation_ai_service.py # Advanced consultation (1000+ lines)
│   ├── activity_service.py      # Activity logic
│   ├── nutrition_service.py     # Nutrition logic
│   ├── i18n_service.py          # Multi-language
│   ├── cache_service.py         # Redis caching
│   └── [many more services]
├── models/
│   ├── auth.py                  # Auth models
│   ├── nutrition.py             # Food/meal models
│   ├── activities.py            # Activity models
│   ├── activity_templates.py    # Template models
│   ├── body_metrics.py          # Body tracking models
│   ├── consultation.py          # Consultation models
│   └── errors.py                # Error models
├── config.py                    # Environment config
├── main.py                      # FastAPI app initialization
└── utils/
    ├── logger.py                # Logging utilities
    └── sdk_validator.py         # SDK validation

migrations/                      # Database migrations (SQL)
workers/                         # Celery background tasks
tests/                           # Unit and integration tests
```

---

## Key Documentation References

- **`CLAUDE.md`** - Complete codebase index + development rules (AI assistants must read this)
- **`ARCHITECTURE.md`** - System architecture and patterns
- **`README.md`** - Quick start guide
- **`CONSULTATION_KEYS_GUIDE.md`** - Consultation system explanation
- **`CONSULTATION_SECURITY.md`** - Security implementation
- **`CONSULTATION_MEMORY_AND_SEEDING.md`** - Memory system
- **`migrations/README.md`** - Database migration guide

---

## For AI Assistants

When working on this codebase:

1. **READ `CLAUDE.md` FIRST** - Contains complete rules and patterns
2. **ALWAYS use structured logging** - No print statements
3. **ALWAYS follow service layer pattern** - Route → Service → DB
4. **ALWAYS use Pydantic models** - No manual validation
5. **NEVER use service role for user queries** - Bypasses RLS
6. **ASK before modifying consultation system** - Complex feature

---

**Last Updated:** 2025-10-14
