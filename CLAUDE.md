# CLAUDE.md - AI Assistant Guide for SHARPENED Backend

> **Purpose:** Index the codebase and enforce development standards for AI coding assistants

---

## Project Overview

**SHARPENED Backend** - FastAPI REST API for fitness and nutrition coaching
- **Framework:** FastAPI
- **Language:** Python 3.12+
- **Database:** Supabase (PostgreSQL)
- **Auth:** httpOnly cookies (Supabase JWT)
- **LLM:** Anthropic Claude 3.5 Sonnet
- **Logging:** Structured logging (structlog)
- **Error Tracking:** Sentry
- **Deployment:** Docker + Railway/Fly.io

---

## Critical Rules - ALWAYS FOLLOW

### 1. **Use Structured Logging**
❌ BAD: `print(f"User {user_id} logged in")`
✅ GOOD: `logger.info("user_login", user_id=user_id, email=email)`

**Why:** JSON-formatted logs for production monitoring

**Logger:** `structlog.get_logger()`
- Levels: `debug()`, `info()`, `warning()`, `error()`
- Always include context as kwargs

### 2. **Auth via httpOnly Cookies Only**
❌ BAD: Bearer tokens, API keys in headers
✅ GOOD: JWT in httpOnly cookie

**Why:** XSS protection (JavaScript can't access cookies)

**Implementation:** `app/api/dependencies.py` → `get_current_user()`

### 3. **Service Layer for Business Logic**
❌ BAD: Business logic in route handlers
✅ GOOD: Route → Service → Database

**Why:** Testability, reusability, separation of concerns

**Pattern:**
```python
# app/api/v1/endpoint.py
@router.post("/")
async def create_item(data: ItemCreate, service: ItemService):
    return await service.create(data)

# app/services/item_service.py
class ItemService:
    async def create(self, data: ItemCreate) -> Item:
        # Business logic here
        pass
```

### 4. **Pydantic Models for Validation**
❌ BAD: Manual dict validation
✅ GOOD: Pydantic models

**Why:** Auto-validation, type safety, OpenAPI docs

**Models:** `app/models/` (request/response schemas)

### 5. **Row Level Security (RLS) Awareness**
✅ ALWAYS: Check if database has RLS enabled
⚠️ WARNING: Service role bypasses RLS - use with caution

**Why:** Data isolation between users

**Implementation:** Use user's JWT for database queries (not service role key)

---

## File Structure & Code Index

### **App Structure**

```
app/
├── api/
│   ├── dependencies.py      # FastAPI dependencies (auth, DB)
│   └── v1/                  # API version 1
│       ├── health.py        # Health check endpoint
│       ├── auth.py          # Auth endpoints (login, signup, logout)
│       ├── users.py         # User endpoints (profile, settings)
│       ├── onboarding.py    # Onboarding submission
│       ├── foods.py         # Food search & custom foods
│       ├── meals.py         # Meal logging
│       └── activities.py    # ⭐ Activity tracking (NEW)
├── services/
│   ├── supabase_service.py  # ⭐ Database abstraction layer
│   ├── auth_service.py      # Auth business logic
│   ├── activity_service.py  # ⭐ Activity tracking logic (NEW)
│   └── consultation_ai_service.py  # ⭐ LLM consultation (1000+ lines)
├── models/
│   ├── auth.py              # Auth request/response models
│   ├── user.py              # User data models
│   ├── onboarding.py        # Onboarding models
│   └── activities.py        # ⭐ Activity models (NEW)
├── config.py                # ⭐ Configuration & environment variables
├── main.py                  # ⭐ FastAPI app initialization
└── utils/
    └── logger.py            # Logging utilities
```

### **Database**

```
migrations/
├── README.md                # Migration guide
└── [SQL migration files]    # Database schema changes
```

---

## Key Files - What They Do

### **Core Configuration**

| File | Purpose | When to Edit |
|------|---------|--------------|
| `app/config.py` | Environment variables & settings | Adding new config |
| `app/main.py` | FastAPI app, CORS, middleware, Sentry | Startup logic, new routers |
| `app/api/dependencies.py` | Dependency injection (auth, DB) | Adding new dependencies |

### **API Endpoints**

| File | Purpose | Endpoints |
|------|---------|-----------|
| `app/api/v1/health.py` | Health checks | `GET /api/v1/health` |
| `app/api/v1/auth.py` | Authentication | `POST /api/v1/auth/signup`, `/login`, `/logout` |
| `app/api/v1/users.py` | User management | `GET /api/v1/users/me`, `PATCH /api/v1/users/me` |
| `app/api/v1/onboarding.py` | Onboarding | `POST /api/v1/onboarding` |
| `app/api/v1/foods.py` | Food database | `GET /api/v1/foods/search`, `POST /api/v1/foods/custom` |
| `app/api/v1/meals.py` | Meal logging | `GET /api/v1/meals`, `POST /api/v1/meals`, `DELETE /api/v1/meals/{id}` |
| `app/api/v1/activities.py` | ⭐ Activity tracking | `GET /api/v1/activities`, `POST /api/v1/activities`, `PATCH /api/v1/activities/{id}` |

### **Services (Business Logic)**

| File | Purpose | Key Methods |
|------|---------|-------------|
| `app/services/supabase_service.py` | Database queries | `get_user()`, `create_user()`, `update_user()` |
| `app/services/auth_service.py` | Auth logic | `signup()`, `login()`, `verify_password()` |
| `app/services/activity_service.py` | ⭐ Activity tracking | `get_user_activities()`, `get_daily_summary()`, `create_activity()` |
| `app/services/consultation_ai_service.py` | ⭐ LLM consultation | `process_message()`, `start_consultation()` |

---

## Architecture Patterns

### **Request Flow**
```
HTTP Request
  ↓
FastAPI Router (app/api/v1/*.py)
  ↓
Dependency Injection (auth check, DB connection)
  ↓
Service Layer (app/services/*.py)
  ↓
Supabase Service (app/services/supabase_service.py)
  ↓
Database (PostgreSQL via Supabase)
```

### **Auth Flow**
```
1. User sends credentials to /auth/login
2. AuthService verifies password
3. Generate Supabase JWT token
4. Set httpOnly cookie with JWT
5. Future requests: get_current_user() validates cookie
```

### **Error Handling**
```
Error Occurs
  ↓
Service raises HTTPException or custom exception
  ↓
FastAPI catches and formats as JSON
  ↓
Sentry captures error (if configured)
  ↓
Logger records with context
```

---

## Common Tasks - Code Examples

### **Creating a New Endpoint**

```python
# app/api/v1/items.py
from fastapi import APIRouter, Depends
from app.models.item import ItemCreate, ItemResponse
from app.services.item_service import ItemService
from app.api.dependencies import get_current_user
import structlog

router = APIRouter()
logger = structlog.get_logger()

@router.post("/items", response_model=ItemResponse)
async def create_item(
    data: ItemCreate,
    service: ItemService = Depends(),
    current_user = Depends(get_current_user)
):
    """Create a new item"""
    logger.info("create_item", user_id=current_user.id, item_name=data.name)

    try:
        item = await service.create(data, current_user.id)
        return item
    except Exception as e:
        logger.error("create_item_failed", error=str(e), user_id=current_user.id)
        raise
```

### **Database Queries via Supabase Service**

```python
# app/services/item_service.py
from app.services.supabase_service import SupabaseService
import structlog

logger = structlog.get_logger()

class ItemService:
    def __init__(self):
        self.db = SupabaseService()

    async def create(self, data: ItemCreate, user_id: str) -> Item:
        """Create item in database"""
        logger.info("creating_item", user_id=user_id, name=data.name)

        # Insert into database
        result = self.db.supabase.table('items').insert({
            'user_id': user_id,
            'name': data.name,
            'description': data.description,
        }).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create item")

        return Item(**result.data[0])
```

### **Structured Logging**

```python
import structlog

logger = structlog.get_logger()

# ✅ CORRECT - JSON-formatted with context
logger.info(
    "user_action",
    user_id=user.id,
    action="purchase",
    item_id=item.id,
    amount=49.99
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
```

### **Authentication Dependency**

```python
from app.api.dependencies import get_current_user
from app.models.user import User

# Protect endpoint - requires authentication
@router.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    return {"message": f"Hello {current_user.email}"}

# Optional authentication
from app.api.dependencies import get_current_user_optional

@router.get("/public")
async def public_route(current_user: User | None = Depends(get_current_user_optional)):
    if current_user:
        return {"message": f"Hello {current_user.email}"}
    return {"message": "Hello guest"}
```

---

## Environment Variables

### **Required**
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Service role key (full DB access)
- `SUPABASE_ANON_KEY` - Anonymous key (public operations)
- `SUPABASE_JWT_SECRET` - JWT signing secret

### **Optional**
- `SENTRY_DSN` - Sentry error tracking (highly recommended for prod)
- `ANTHROPIC_API_KEY` - For Claude AI consultation feature
- `ENVIRONMENT` - `development` or `production` (default: development)
- `LOG_LEVEL` - `DEBUG`, `INFO`, `WARNING`, `ERROR` (default: INFO)
- `CORS_ORIGINS` - Allowed frontend origins (comma-separated)

### **Development**
Create `.env` file:
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
SUPABASE_ANON_KEY=eyJ...
SUPABASE_JWT_SECRET=your-jwt-secret
ANTHROPIC_API_KEY=sk-ant-...
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

---

## LLM Consultation System (Advanced Feature)

### **Overview**
Premium feature that conducts AI-powered fitness consultations via natural conversation.

### **Key Components**
1. **`consultation_ai_service.py`** - 1000+ lines of Claude integration
2. **Gated by one-time use keys** - Cost control and quality control
3. **7-section system prompts** - Training, meals, goals, challenges, etc.
4. **Database tool calling** - AI searches and inserts user data (15 tools)
5. **Memory system** - Prevents duplicate questions

### **Status**
- ✅ Backend complete (service ready)
- ⚠️ Frontend incomplete (placeholder API endpoints)
- ⚠️ **DISABLED FOR MVP** (endpoints commented out in `main.py`)

### **Why Disabled?**
To reduce complexity for MVP launch:
- Frontend UI is incomplete (placeholder only)
- Premium feature (requires consultation keys)
- Not part of core MVP (activities + nutrition tracking)
- Reduces tool count from 27 → 12 tools (56% reduction)
- Unified Coach (12 tools) remains active for daily coaching

### **To Re-enable:**
1. Uncomment consultation import in `app/main.py` line 378
2. Uncomment router include in `app/main.py` line 403
3. Complete frontend UI at `/dashboard/consultation`
4. Test consultation key redemption flow

### **Documentation**
- `CONSULTATION_KEYS_GUIDE.md` - Key system explanation
- `CONSULTATION_SECURITY.md` - 5-layer security implementation
- `CONSULTATION_MEMORY_AND_SEEDING.md` - Memory system details

**Note:** This is a complex, production-ready feature. Read the consultation docs before modifying.

---

## Activity Tracking System (Production Feature)

### **Overview**
Full-featured activity tracking for workouts, cardio, strength training, sports, and flexibility activities.

### **Key Features**
1. **6 Activity Categories** - Cardio (steady/interval), Strength, Sports, Flexibility, Other
2. **Flexible JSONB Metrics** - Category-specific data (distance, exercises, score, etc.)
3. **Daily Summaries** - Aggregated calories, duration, intensity (METs)
4. **Smart Validation** - Category-specific METs ranges, duration calculations
5. **Soft Deletes** - Data preserved for audit trail

### **Architecture**

**Endpoints** (`app/api/v1/activities.py`):
```python
GET    /api/v1/activities              # List activities (with date filtering)
GET    /api/v1/activities/summary      # Daily summary (calories, duration, METs)
GET    /api/v1/activities/{id}         # Single activity
POST   /api/v1/activities              # Create activity
PATCH  /api/v1/activities/{id}         # Update activity
DELETE /api/v1/activities/{id}         # Soft delete activity
```

**Service Layer** (`app/services/activity_service.py`):
- `get_user_activities()` - Fetch with pagination & date filtering
- `get_daily_summary()` - Calculate aggregates (SUM calories, AVG METs)
- `create_activity()` - Validate & calculate duration
- `update_activity()` - Ownership verification + duration recalc
- `delete_activity()` - Soft delete (set deleted_at timestamp)

**Models** (`app/models/activities.py`):
- `ActivityBase` - Base fields with validators
- `CreateActivityRequest` - Create validation
- `UpdateActivityRequest` - Update validation (all optional)
- `Activity` - Full response model
- `DailySummary` - Aggregated stats

### **JSONB Metrics Pattern**

**Why JSONB?**
Different activities have wildly different data:
- Cardio → distance, pace, heart rate
- Strength → exercises, sets, reps, weight
- Sports → opponent, score, sport type

**Alternative would be:** Separate tables per activity type → massive complexity

**Example Metrics:**

**Cardio:**
```json
{
  "distance_km": 5.2,
  "avg_heart_rate": 145,
  "max_heart_rate": 168,
  "avg_pace": "5:47/km",
  "elevation_gain_m": 120
}
```

**Strength Training:**
```json
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
```

**Sports:**
```json
{
  "sport_type": "tennis",
  "opponent": "John Doe",
  "score": "6-4, 6-3"
}
```

### **Smart Validation**

**Category-Specific METs Ranges:**
```python
METS_RANGES = {
    'cardio_steady_state': (3.0, 15.0),  # Walking to running
    'cardio_interval': (5.0, 18.0),      # HIIT, sprints
    'strength_training': (3.0, 8.0),     # Weight lifting
    'sports': (4.0, 12.0),               # Tennis, basketball
    'flexibility': (1.5, 4.0),           # Yoga, stretching
}
```

**Duration Calculation:**
```python
# Automatically calculated from start_time + end_time
# OR manually entered
# Service layer recalculates if times change
duration_minutes = int((end_time - start_time).total_seconds() / 60)
```

### **Database Schema**

**activities table:**
```sql
CREATE TABLE activities (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id),

  category TEXT NOT NULL,           -- Activity category
  activity_name TEXT NOT NULL,      -- Custom name
  start_time TIMESTAMPTZ NOT NULL,
  end_time TIMESTAMPTZ,
  duration_minutes INTEGER,

  calories_burned INTEGER,
  intensity_mets NUMERIC(4,2),      -- 1.0=rest, 8.0=running

  metrics JSONB DEFAULT '{}',       -- Flexible category-specific data
  notes TEXT,

  deleted_at TIMESTAMPTZ,           -- Soft delete
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_activities_user_start ON activities(user_id, start_time DESC);
CREATE INDEX idx_activities_deleted ON activities(user_id, deleted_at) WHERE deleted_at IS NULL;
```

### **Math Accuracy**

**Daily Summary Calculations:**
```python
# Total calories burned
total_calories = SUM(calories_burned) WHERE user_id = ? AND DATE(start_time) = ?

# Average intensity
avg_intensity = AVG(intensity_mets)

# Goal progress
goal_percentage = (total_calories / daily_goal) * 100
```

**Duration:**
```python
# Option 1: From timestamps
duration = (end_time - start_time).total_seconds() / 60

# Option 2: Manual entry
duration = duration_minutes

# Service layer prioritizes calculated duration
```

### **Usage Example**

**Create Activity:**
```python
from app.services.activity_service import activity_service

activity = await activity_service.create_activity(
    user_id=user.id,
    category='cardio_steady_state',
    activity_name='Morning Run',
    start_time=datetime.now(),
    end_time=datetime.now() + timedelta(minutes=45),
    duration_minutes=None,  # Will be calculated
    calories_burned=285,
    intensity_mets=8.5,
    metrics={
        'distance_km': 5.2,
        'avg_heart_rate': 145,
        'avg_pace': '5:47/km'
    },
    notes='Felt great today!'
)
```

**Get Daily Summary:**
```python
summary = await activity_service.get_daily_summary(
    user_id=user.id,
    target_date=date.today()
)
# Returns: total_calories, total_duration, avg_intensity, activity_count, goal_percentage
```

### **Status**
- ✅ **Backend Complete** - All endpoints implemented
- ✅ **Frontend Complete** - Activities page with daily summary
- ✅ **Production Ready** - Validation, logging, error handling
- ⚠️ **TODO:** Activity logging form (placeholder exists at `/activities/log`)

---

## Database Schema

### **Key Tables**
- `users` - User accounts and profiles
- `onboarding_data` - Onboarding questionnaire responses
- `meal_logs` - Meal tracking data
- `activity_logs` - Workout/activity tracking
- `consultation_sessions` - LLM consultation sessions
- `consultation_keys` - One-time use consultation keys

**Migrations:** See `migrations/README.md` for schema management

**RLS:** All tables have Row Level Security enabled (users can only access their own data)

---

## CORS Configuration

**Current Settings (app/main.py):**
```python
allow_origins=settings.cors_origins_list  # From CORS_ORIGINS env var
allow_credentials=True
allow_methods=["*"]  # ⚠️ Too permissive for production
allow_headers=["*"]  # ⚠️ Too permissive for production
```

**TODO Before Production:**
Tighten CORS restrictions:
```python
allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
allow_headers=["Content-Type", "Authorization", "X-Requested-With"]
```

---

## Sentry Error Tracking

### **Configuration**
Sentry is configured in `app/main.py` lifespan:
- Automatically captures FastAPI exceptions
- Includes request context (URL, method, headers, user)
- Tags all events with `app: "sharpened-backend"`
- Disabled in development (only production)

### **Setup**
1. Create Sentry project at https://sentry.io
2. Add `SENTRY_DSN` to environment variables
3. Restart server

### **Manual Capture**
```python
import sentry_sdk

try:
    risky_operation()
except Exception as e:
    sentry_sdk.capture_exception(e)
    raise
```

---

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run with verbose output
pytest -v
```

**Test Structure:**
```
tests/
├── conftest.py           # Pytest fixtures
├── test_auth.py          # Auth endpoint tests
├── test_users.py         # User endpoint tests
└── test_services/        # Service layer tests
```

---

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run dev server (auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run with specific log level
LOG_LEVEL=DEBUG uvicorn app.main:app --reload

# Run tests
pytest

# Type checking
mypy app/

# Code formatting
black app/
isort app/

# API docs (when running)
# http://localhost:8000/docs (Swagger UI)
# http://localhost:8000/redoc (ReDoc)
```

---

## Current State & Known Issues

### **✅ Production Ready**
- Auth endpoints (signup, login, logout)
- User management (profile, update)
- Onboarding submission
- Health check endpoint
- Structured logging
- Sentry error tracking configured
- CORS configured (needs tightening)

### **⚠️ Incomplete Features**
- Consultation API endpoints (service exists, endpoints not exposed)
- Meal logging endpoints
- Activity logging endpoints
- AI coach chat endpoints
- Progress tracking endpoints

### **Known Issues**
- CORS too permissive (see comment in main.py)
- Missing API endpoints for frontend features
- Consultation feature complete but not exposed

---

## For AI Assistants (Claude, GPT, etc.)

When working on this codebase:

1. **ALWAYS** read this file first
2. **ALWAYS** use structured logging (no print statements)
3. **ALWAYS** follow service layer pattern (route → service → DB)
4. **ALWAYS** use Pydantic models for validation
5. **NEVER** use service role key for user queries (RLS bypass)
6. **ASK** if consultation system needs modification (complex feature)

**Common Mistakes to Avoid:**
- ❌ Using `print()` instead of `logger.info()`
- ❌ Business logic in route handlers (use services)
- ❌ Raw dict validation (use Pydantic models)
- ❌ Ignoring RLS (use user's JWT for queries)
- ❌ Not including error context in logs
- ❌ Exposing sensitive data in error messages

---

**Last Updated:** 2025-10-12
**Version:** 1.0.0
