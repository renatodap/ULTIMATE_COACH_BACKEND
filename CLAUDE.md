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

## 📚 Activity Tracking Documentation (CRITICAL - READ BEFORE MODIFYING)

### **Comprehensive Documentation Available**

The activity tracking system has **comprehensive documentation** designed to achieve **ZERO BUGS**. Before working on any activity tracking feature, you MUST consult these documents.

### **Documentation Files**

**Location:** Project root directory (`/`)

1. **`ACTIVITY_TRACKING_SYSTEM.md`** (15,000+ words)
   - Complete system architecture
   - Database schema & all constraints
   - API contracts for all 6 endpoints
   - Type system (TypeScript + Pydantic sync requirements)
   - Data flow diagrams
   - Validation rules (3 layers)
   - Calculation formulas (duration, METs, calories)
   - Timezone handling (UTC ↔ local)
   - Critical code paths

2. **`ACTIVITY_TRACKING_BUG_PREVENTION.md`** (18,000+ words)
   - **50+ specific bug scenarios** with prevention strategies
   - 12 bug categories covering all common mistakes
   - Code examples: ✅ Correct vs ❌ Wrong
   - Mitigation checklists
   - Cross-references to system docs

3. **`ACTIVITY_TRACKING_DOCUMENTATION_SUMMARY.md`**
   - Executive summary
   - Documentation statistics
   - Quick reference guide

### **When to Use Each Document**

**Before Starting Development:**
```
1. Read ACTIVITY_TRACKING_SYSTEM.md relevant sections
   - Section 2: Database Schema (if changing database)
   - Section 3: API Contracts (if changing endpoints)
   - Section 4: Type System (if changing models)
   - Section 5: Data Flow (if changing business logic)
   - Section 8: Calculation Formulas (if changing math)
```

**While Coding:**
```
1. Refer to inline documentation in code files
   - app/models/activities.py (comprehensive docstrings)
   - app/services/activity_service.py (service layer docs)
   - All inline docs cross-reference main documentation

2. Check ACTIVITY_TRACKING_BUG_PREVENTION.md for your task
   - Bug 2.x: Timezone & Date Handling
   - Bug 3.x: Calculation & Formula Bugs
   - Bug 4.x: Type Safety & Validation
   - Bug 6.x: Database Integrity
   - Bug 12.x: Security & Authorization
```

**Before Submitting PR:**
```
1. Run through relevant mitigation checklists
2. Verify type sync (Pydantic ↔ TypeScript)
3. Check timezone handling is correct
4. Verify validation at all 3 layers
5. Ensure calculations match documented formulas
```

### **Critical Requirements**

**TYPE SYNCHRONIZATION (CRITICAL):**
```python
# Backend: app/models/activities.py
# Frontend: lib/types/activities.ts
# MUST stay in sync - documented in both files
# Last Sync Date: Check file headers
# Breaking changes require API versioning
```

**TIMEZONE HANDLING (CRITICAL):**
```python
# Database: Always UTC (TIMESTAMPTZ)
# API: Always send/receive ISO 8601 UTC strings
# Frontend: Convert to user's local timezone for display
# Grouping: NEVER use UTC date - use user's timezone
# See: ACTIVITY_TRACKING_SYSTEM.md Section 9
```

**VALIDATION LAYERS (CRITICAL):**
```python
# Layer 1: Pydantic models (app/models/activities.py)
# Layer 2: Service layer (app/services/activity_service.py)
# Layer 3: Database constraints (CHECK, FK, NOT NULL)
# All 3 layers must be consistent
```

**CALCULATION FORMULAS (CRITICAL):**
```python
# Duration: (end_time - start_time) / 60 seconds
# Calories: METs × weight_kg × (duration_minutes / 60)
# Goal %: (total_calories / daily_goal) × 100
# See: ACTIVITY_TRACKING_SYSTEM.md Section 8
```

### **Common Mistakes to Avoid**

❌ **DON'T:**
- Change Pydantic models without updating TypeScript types
- Use UTC date for grouping activities by day
- Skip validation at any layer
- Hardcode calculation formulas (use documented formulas)
- Ignore soft delete filtering (WHERE deleted_at IS NULL)
- Allow users to update other users' activities
- Use `any` type in TypeScript (strict type safety)

✅ **DO:**
- Check documentation before modifying
- Update all 3 layers when changing schema
- Use timezone-aware date comparisons
- Follow documented calculation formulas exactly
- Always verify ownership before mutations
- Add new bugs to bug prevention guide

### **Bug Prevention Strategy**

When implementing a feature:

1. **Read relevant documentation sections**
   - Understand the architecture
   - Review data flow diagrams
   - Check calculation formulas

2. **Check bug prevention guide**
   - Find similar scenarios
   - Review prevention strategies
   - Use provided code examples

3. **Follow mitigation checklists**
   - Validation at all layers
   - Timezone handling correct
   - Type sync maintained
   - Security checks in place

4. **Test edge cases**
   - Null/undefined values
   - Timezone boundaries (midnight, DST)
   - Concurrent operations
   - Authorization failures

5. **Update documentation if needed**
   - Add new bug scenarios discovered
   - Update calculation formulas if changed
   - Update last sync dates

### **Quick Reference**

**File Locations:**
```
Backend Models:     app/models/activities.py
Backend Service:    app/services/activity_service.py
Backend Endpoints:  app/api/v1/activities.py
Frontend Types:     ../ULTIMATE_COACH_FRONTEND/lib/types/activities.ts
Frontend API:       ../ULTIMATE_COACH_FRONTEND/lib/api/activities.ts
```

**Documentation:**
```
System Docs:     /ACTIVITY_TRACKING_SYSTEM.md
Bug Prevention:  /ACTIVITY_TRACKING_BUG_PREVENTION.md
Summary:         /ACTIVITY_TRACKING_DOCUMENTATION_SUMMARY.md
```

**Key Sections to Bookmark:**
- Section 2.2: JSONB Metrics Schemas
- Section 3.4: Create Activity API
- Section 8: Calculation Formulas
- Section 9: Timezone Handling
- Bug 2.1: Activities Grouped Under Wrong Date
- Bug 3.1: Incorrect Calorie Calculation
- Bug 4.1: TypeScript Types Out of Sync

### **For AI Assistants Working on Activities**

**MANDATORY STEPS:**

1. **Read ACTIVITY_TRACKING_SYSTEM.md Section relevant to your task**
2. **Check ACTIVITY_TRACKING_BUG_PREVENTION.md for similar scenarios**
3. **Review inline documentation in code files**
4. **Verify type sync requirements**
5. **Test with timezone edge cases**
6. **Run mitigation checklists**

**If you discover a new bug:**
1. Document root cause
2. Add to ACTIVITY_TRACKING_BUG_PREVENTION.md
3. Add prevention strategy with code example
4. Create test to prevent regression

**Remember:** This system is designed for ZERO BUGS. The documentation is comprehensive. Use it.

---

## 🍽️ Nutrition Logging Documentation (CRITICAL - READ BEFORE MODIFYING)

### **Overview**
The nutrition logging system has comprehensive documentation to prevent bugs like the "100 banana" incident (where users could accidentally log 100 servings instead of 1). **ALWAYS read this documentation before modifying nutrition logging code.**

### **Documentation Files**

**Location:** Project root directory (`/`)

**📘 Complete Architecture:**
- **File:** `NUTRITION_LOGGING_ARCHITECTURE.md`
- **Length:** 800+ lines
- **Contents:**
  - System overview and design philosophy
  - Critical concepts (quantity semantic overload)
  - State management rules with 3 critical reset points
  - Complete data flow diagram
  - Frontend/backend contract specifications
  - Multi-layer validation requirements
  - Common bugs and prevention strategies
  - Testing checklist

**🚀 Quick Reference:**
- **File:** `NUTRITION_LOGGING_QUICK_REFERENCE.md`
- **Length:** 200+ lines
- **Contents:**
  - TL;DR of critical concepts
  - Three reset rules with code examples
  - Validation checklist
  - Testing scenarios
  - Code locations table

### **When to Read This Documentation**
- ✅ Before modifying `app/services/nutrition_service.py`
- ✅ Before changing `app/services/nutrition_calculator.py`
- ✅ Before updating meal/food API endpoints
- ✅ When debugging nutrition calculation issues
- ✅ When adding new food types or serving logic
- ✅ When a bug report mentions incorrect quantities or nutrition values

### **The Critical Concept: Quantity Semantic Overload**

The `quantity` field in meal items has **two different meanings** depending on context:

```python
# GRAMS MODE (serving_id = None)
quantity: 150  # = 150 grams of chicken breast

# SERVING MODE (serving_id = UUID)
quantity: 2    # = 2 servings of protein powder
```

**Why this is critical for backend:**
- Frontend sends `quantity` with different meanings
- Backend MUST understand which mode is active
- Backend MUST recalculate nutrition (never trust frontend values)
- Validation thresholds differ between modes

### **Backend Responsibilities**

#### **1. Multi-Layer Validation**

The backend implements the **final two layers** of a 4-layer validation system:

```python
# app/services/nutrition_service.py

# Layer 3: Backend Warning (line 735)
if serving_id and quantity > 10:
    logger.warning(
        "high_serving_quantity",
        user_id=user_id,
        quantity=quantity,
        food_id=item.food_id
    )

# Layer 4: Backend Hard Rejection (line 722)
if serving_id and quantity > 50:
    raise HTTPException(
        status_code=400,
        detail="Serving quantity cannot exceed 50"
    )
```

#### **2. Authoritative Calculations**

**Critical Principle:** "Calculate once, store forever"

```python
# app/services/nutrition_service.py:764-768

# WRONG - Trust frontend values
item_calories = item.calories  # From request

# CORRECT - Recalculate everything
nutrition = calculate_food_nutrition(
    food_data=food,
    quantity=item.quantity,
    unit='grams' if not item.serving_id else 'serving',
    serving_data=serving,
    get_food_by_id=lambda fid: get_food(fid)
)
item_calories = nutrition['calories']
```

**Why this is critical:**
- Frontend calculations are for preview/UX only
- Malicious users could send fake nutrition values
- Frontend bugs don't corrupt database
- Single source of truth for all stored values

#### **3. Complete Data Joins**

**Critical for frontend display:**

```python
# app/services/nutrition_service.py:889 and 941

# WRONG - Missing food names
.select("*, meal_items(*)")

# CORRECT - Join foods table
.select("*, meal_items(*, foods(name, brand_name))")
```

**Why this is critical:**
- Frontend needs food names for display
- Without JOIN, frontend shows blank food names
- Fixed in recent update to prevent "grams displayed twice" bug

### **Calculation Formulas**

The backend uses `nutrition_calculator.py` which mirrors frontend calculations:

```python
# app/services/nutrition_calculator.py

# Simple/Branded Foods
def calculate_simple_food_nutrition(food_data, grams):
    factor = grams / 100
    return {
        'calories': round(food_data['calories_per_100g'] * factor),
        'protein_g': round(food_data['protein_g_per_100g'] * factor, 1),
        'carbs_g': round(food_data['carbs_g_per_100g'] * factor, 1),
        'fat_g': round(food_data['fat_g_per_100g'] * factor, 1),
    }

# Composed Foods (Recipes)
def calculate_composed_food_nutrition(recipe_items, servings, get_food_by_id):
    # Recursively sum nutrition from all ingredients
    # Scale by servings multiplier
    # See nutrition_calculator.py:82-118
```

### **Type Safety Requirements**

**CRITICAL:** Backend Pydantic models must match frontend TypeScript types.

**Backend Models** (`app/models/meal.py` or similar):
```python
class CreateMealItemRequest(BaseModel):
    food_id: str
    quantity: float
    serving_id: str | None
    grams: float
    calories: int              # Rounded to int
    protein_g: float           # Rounded to 1 decimal
    carbs_g: float
    fat_g: float
    display_unit: str
    display_label: str | None
```

**Frontend Types** (`lib/types/nutrition.ts`):
```typescript
export interface CreateMealItemRequest {
  food_id: string
  quantity: number
  serving_id: string | null
  grams: number
  calories: number           // Must match backend int
  protein_g: number          // Must match backend float
  carbs_g: number
  fat_g: number
  display_unit: string
  display_label: string | null
}
```

**Synchronization checklist:**
- [ ] Field names match exactly (snake_case backend, camelCase frontend after transform)
- [ ] Types match (int/float vs number, str vs string)
- [ ] Nullability matches (Optional[str] vs string | null)
- [ ] Rounding rules match (calories: int, macros: 1 decimal)

### **Timezone Handling**

**Recent fix (2025-10-17):**

```python
# Frontend now sends logged_at timestamp
# app/api/v1/meals.py

@router.post("/meals")
async def create_meal(request: CreateMealRequest, ...):
    # Frontend sends: logged_at: "2025-10-17T15:30:00Z"
    # Backend stores as UTC in database
    # Queries use user's timezone for date grouping
```

**Why this was critical:**
- Before fix: Backend used `datetime.utcnow()` (current UTC time)
- Problem: For users behind UTC, meals appeared in the future
- Solution: Frontend sends user's current time converted to UTC
- See: NUTRITION_LOGGING_ARCHITECTURE.md Section on Timezone Handling

### **Code Locations**

| Feature | File | Key Functions/Lines |
|---------|------|---------------------|
| Backend validation | app/services/nutrition_service.py | Lines 722, 735 |
| Backend calculations | app/services/nutrition_service.py | Lines 764-768 |
| Calculator functions | app/services/nutrition_calculator.py | Full file |
| Food data joins | app/services/nutrition_service.py | Lines 889, 941 |
| Meal creation endpoint | app/api/v1/meals.py | create_meal() |
| Food search service | app/services/food_search.py | search_foods() |

### **Testing Checklist**

Before merging nutrition logging changes:

- [ ] Backend validates serving quantity >50 (HTTP 400)
- [ ] Backend logs warning for quantity >10 servings
- [ ] Backend recalculates ALL nutrition values (never trusts frontend)
- [ ] Backend includes food names in meal queries (JOIN foods table)
- [ ] logged_at timestamp properly stored in UTC
- [ ] Calculations match frontend preview (within rounding)
- [ ] Test case: Submit 60 servings → Backend rejects with 400
- [ ] Test case: Submit meal with frontend-calculated nutrition → Backend recalculates
- [ ] Test case: Query meals → Food names appear in response

### **Common Backend Mistakes**

❌ **Mistake 1:** Trusting frontend-calculated nutrition
```python
# WRONG - Uses values from request
item_calories = item.calories
item_protein = item.protein_g

# CORRECT - Recalculates from food data
nutrition = calculate_food_nutrition(food, item.quantity, ...)
item_calories = nutrition['calories']
```

❌ **Mistake 2:** Missing validation
```python
# WRONG - No serving quantity check
await create_meal_item(item)

# CORRECT - Validate first
if item.serving_id and item.quantity > 50:
    raise HTTPException(400, "Serving quantity too high")
```

❌ **Mistake 3:** Incomplete data joins
```python
# WRONG - Frontend gets no food names
.select("*, meal_items(*)")

# CORRECT - Include food data
.select("*, meal_items(*, foods(name, brand_name))")
```

❌ **Mistake 4:** Using current UTC time for logged_at
```python
# WRONG - Ignores user's timezone
logged_at = datetime.utcnow()

# CORRECT - Use timestamp from request
logged_at = request.logged_at  # Frontend sends proper UTC time
```

### **Security Considerations**

**Never trust client data:**

```python
# ALWAYS recalculate nutrition
# ALWAYS validate ownership (user_id check)
# ALWAYS validate serving quantities
# ALWAYS use parameterized queries (Supabase handles this)
# ALWAYS log suspicious activity (e.g., quantity > 10)
```

**Example secure implementation:**

```python
@router.post("/meals")
async def create_meal(
    request: CreateMealRequest,
    current_user = Depends(get_current_user)
):
    # Validate ownership - use current_user.id, not request.user_id
    # Recalculate nutrition - don't trust request values
    # Validate quantities - reject suspicious values
    # Log activity - for audit trail
```

### **When in Doubt**

1. **Read the full documentation:** `NUTRITION_LOGGING_ARCHITECTURE.md`
2. **Check the quick reference:** `NUTRITION_LOGGING_QUICK_REFERENCE.md`
3. **Review inline comments in code files**
4. **Ask:** Does `quantity` mean grams or servings here?
5. **Verify:** Am I recalculating or trusting frontend values?
6. **Test:** Does backend reject invalid serving quantities?

### **Key Backend Principles**

> **"Never trust the client. Always recalculate. Always validate."**

> **"The backend is the source of truth. Frontend is for preview only."**

> **"Calculate once, store forever. Database values are immutable."**

### **For AI Assistants Working on Nutrition**

**MANDATORY STEPS:**

1. **Read NUTRITION_LOGGING_ARCHITECTURE.md Section relevant to your task**
2. **Review NUTRITION_LOGGING_QUICK_REFERENCE.md for critical concepts**
3. **Check inline documentation in code files**
4. **Verify backend recalculates all nutrition values**
5. **Verify validation at all backend layers**
6. **Test with edge cases (high quantities, missing fields)**

**If you discover a new bug:**
1. Document root cause
2. Add to documentation with prevention strategy
3. Add code example: ✅ Correct vs ❌ Wrong
4. Create test to prevent regression

**Remember:** The "100 banana" bug was caused by forgetting quantity reset in frontend. The backend must protect against ALL client bugs with proper validation and recalculation.

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
7. **CRITICAL:** Before modifying activity tracking, read:
   - `../ACTIVITY_TRACKING_SYSTEM.md` (15,000+ words)
   - `../ACTIVITY_TRACKING_BUG_PREVENTION.md` (18,000+ words)
   - See "📚 Activity Tracking Documentation" section above
8. **CRITICAL:** Before modifying nutrition logging, read:
   - `../NUTRITION_LOGGING_ARCHITECTURE.md` (800+ lines)
   - `../NUTRITION_LOGGING_QUICK_REFERENCE.md` (200+ lines)
   - See "🍽️ Nutrition Logging Documentation" section above

**Common Mistakes to Avoid:**
- ❌ Using `print()` instead of `logger.info()`
- ❌ Business logic in route handlers (use services)
- ❌ Raw dict validation (use Pydantic models)
- ❌ Ignoring RLS (use user's JWT for queries)
- ❌ Not including error context in logs
- ❌ Exposing sensitive data in error messages
- ❌ Modifying activity/nutrition code without reading documentation
- ❌ Trusting frontend nutrition calculations (always recalculate)
- ❌ Missing validation for serving quantities
- ❌ Using UTC dates for activity grouping (use user's timezone)

---

**Last Updated:** 2025-10-12
**Version:** 1.0.0
