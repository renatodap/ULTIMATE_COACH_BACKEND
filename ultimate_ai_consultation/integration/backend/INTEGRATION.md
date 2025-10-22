# Backend Integration Guide

Complete guide to integrate the adaptive program system into `ULTIMATE_COACH_BACKEND`.

---

## Table of Contents

1. [Overview](#overview)
2. [File Structure](#file-structure)
3. [Installation Steps](#installation-steps)
4. [Database Migration](#database-migration)
5. [Code Integration](#code-integration)
6. [Testing](#testing)
7. [Deployment](#deployment)
8. [Troubleshooting](#troubleshooting)

---

## Overview

This integration adds:
- **Program generation** from consultation data
- **Adaptive reassessments** every 14 days
- **Conversational logging** (extract meals/workouts from chat)
- **Progress tracking** and dashboards
- **Automatic adjustments** using PID controllers

**Integration time**: ~4 hours
**Lines of code changed in existing backend**: ~20 lines
**New endpoints added**: 7
**Database tables added**: 3

---

## File Structure

### Where to Copy Files

```
ULTIMATE_COACH_BACKEND/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── programs.py              ← COPY FROM integration/backend/app/api/v1/
│   ├── models/
│   │   └── program.py                   ← COPY FROM integration/backend/app/models/
│   ├── services/
│   │   └── unified_coach_enhancements.py ← COPY FROM integration/backend/app/services/
│   └── tasks/
│       ├── __init__.py                  ← COPY FROM integration/backend/app/tasks/
│       └── scheduled_tasks.py           ← COPY FROM integration/backend/app/tasks/
├── database/
│   └── functions.sql                    ← COPY FROM integration/backend/database/
├── requirements.txt                     ← APPEND FROM integration/backend/requirements_additions.txt
├── .env                                 ← APPEND FROM integration/backend/.env.additions
└── main.py                              ← MODIFY (3 lines added)
```

---

## Installation Steps

### Step 1: Copy Files

```bash
# From ultimate_ai_consultation directory
cd integration/backend

# Copy API routes
cp app/api/v1/programs.py /path/to/ULTIMATE_COACH_BACKEND/app/api/v1/

# Copy models
cp app/models/program.py /path/to/ULTIMATE_COACH_BACKEND/app/models/

# Copy services
cp app/services/unified_coach_enhancements.py /path/to/ULTIMATE_COACH_BACKEND/app/services/

# Copy tasks
cp -r app/tasks/ /path/to/ULTIMATE_COACH_BACKEND/app/

# Copy database functions
cp database/functions.sql /path/to/ULTIMATE_COACH_BACKEND/database/
```

### Step 2: Install Dependencies

```bash
cd /path/to/ULTIMATE_COACH_BACKEND

# Append new requirements
cat /path/to/ultimate_ai_consultation/integration/backend/requirements_additions.txt >> requirements.txt

# Install
pip install -r requirements.txt
```

### Step 3: Environment Variables

```bash
# Add to .env
cat /path/to/ultimate_ai_consultation/integration/backend/.env.additions >> .env

# Edit .env and update paths
nano .env
```

**Critical variables to set:**
```bash
ULTIMATE_AI_CONSULTATION_PATH=/absolute/path/to/ultimate_ai_consultation
ANTHROPIC_API_KEY=sk-ant-api03-...
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

---

## Database Migration

### Step 1: Run Main Migration

```bash
cd /path/to/ultimate_ai_consultation

# Run the main adaptive system migration
psql $DATABASE_URL < integration/migrations/001_adaptive_system.sql
```

This creates:
- `plan_versions` table
- `feasibility_checks` table
- `plan_adjustments` table
- `reassessment_queue` table

### Step 2: Run Helper Functions

```bash
cd /path/to/ULTIMATE_COACH_BACKEND

psql $DATABASE_URL < database/functions.sql
```

This creates PostgreSQL functions:
- `get_active_plan(user_id)`
- `calculate_today_plan_details(user_id, date)`
- `get_progress_metrics(user_id, days)`
- `get_users_due_for_reassessment()`
- And 6 more helper functions

### Step 3: Verify Migration

```sql
-- Check tables exist
SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE 'plan%';

-- Should return:
-- plan_versions
-- plan_adjustments
-- feasibility_checks

-- Check functions exist
SELECT proname FROM pg_proc WHERE proname LIKE 'get_%';
```

---

## Code Integration

### 1. Register Program Routes

**File:** `ULTIMATE_COACH_BACKEND/app/main.py`

```python
# Add to imports
from app.api.v1 import programs

# Add after existing router registrations
app.include_router(
    programs.router,
    prefix="/api/v1/programs",
    tags=["programs"]
)
```

### 2. Initialize Scheduler

**File:** `ULTIMATE_COACH_BACKEND/app/main.py`

```python
# Add to imports
from app.tasks import init_scheduler, shutdown_scheduler

# Add startup event
@app.on_event("startup")
async def startup():
    # ... existing startup code ...

    # NEW: Initialize scheduler for automatic reassessments
    init_scheduler()
    print("✅ Scheduler initialized")

# Add shutdown event
@app.on_event("shutdown")
async def shutdown():
    # ... existing shutdown code ...

    # NEW: Shutdown scheduler
    shutdown_scheduler()
    print("✅ Scheduler shutdown")
```

### 3. Enhance UnifiedCoachService

**File:** `ULTIMATE_COACH_BACKEND/app/services/unified_coach_service.py`

```python
# Add to imports
from app.services.unified_coach_enhancements import (
    process_message_for_structured_data,
    build_acknowledgment_message,
)

# In your process_user_message method:
async def process_user_message(self, user_id: str, message: str):
    # ... existing conversation logic ...

    # NEW: Extract structured data from message
    extraction_result = await process_message_for_structured_data(
        user_message=message,
        user_id=user_id,
        supabase_client=self.supabase,
        active_plan=None,  # Optional: fetch active plan for context
    )

    # If data was extracted, acknowledge it
    if extraction_result["should_acknowledge"]:
        acknowledgment = build_acknowledgment_message(extraction_result)
        # Add acknowledgment to response or store as system message

    # ... continue with conversation ...
```

That's it! Only 3 files modified in existing backend (main.py twice, unified_coach_service.py once).

---

## Testing

### Unit Tests

```bash
cd /path/to/ultimate_ai_consultation

# Test Phase 1 (program generation)
pytest tests/unit/test_programmer/ -v

# Test Phase 2 (adaptive loop)
pytest tests/unit/test_adaptive/ -v
```

### Integration Tests

**File:** `integration/backend/test_integration.py` (included)

```bash
cd /path/to/ULTIMATE_COACH_BACKEND

# Run integration tests
pytest integration/backend/test_integration.py -v
```

Tests include:
- ✅ Generate initial program from consultation
- ✅ Get today's plan
- ✅ Log meals via API
- ✅ Trigger reassessment
- ✅ Verify adjustments applied

### Manual Testing

1. **Generate Program**:
```bash
curl -X POST http://localhost:8000/api/v1/programs/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-uuid",
    "consultation_data": {
      "goal": "muscle_gain",
      "age": 28,
      "biological_sex": "male",
      "weight_kg": 82,
      "height_cm": 180,
      "activity_level": "moderately_active",
      "training_experience": "intermediate",
      "workouts_per_week": 5,
      "equipment_access": ["full_gym"]
    }
  }'
```

2. **Get Today's Plan**:
```bash
curl http://localhost:8000/api/v1/programs/test-user-uuid/today
```

3. **Trigger Reassessment**:
```bash
curl -X POST http://localhost:8000/api/v1/programs/test-user-uuid/reassess
```

---

## Deployment

### Production Checklist

- [ ] Environment variables set correctly
- [ ] Database migrations run
- [ ] PostgreSQL functions installed
- [ ] Scheduler enabled (`ENABLE_SCHEDULER=true`)
- [ ] Service role key configured (for cron jobs)
- [ ] Rate limits configured
- [ ] Monitoring alerts set up
- [ ] Cost tracking enabled

### Environment-Specific Settings

**Development:**
```bash
ENABLE_SCHEDULER=false  # Test manually
LOG_LEVEL=DEBUG
```

**Staging:**
```bash
ENABLE_SCHEDULER=true
REASSESSMENT_CRON_HOUR=3  # Off-peak
LOG_LEVEL=INFO
```

**Production:**
```bash
ENABLE_SCHEDULER=true
REASSESSMENT_CRON_HOUR=2  # 2 AM UTC
MAX_REASSESSMENTS_PER_HOUR=100
ENABLE_COST_TRACKING=true
LOG_LEVEL=WARNING
```

### Scaling Considerations

**For <1000 users:**
- APScheduler (included) is sufficient
- Single server can handle all reassessments

**For >1000 users:**
- Switch to Celery + Redis
- Distribute reassessments across workers
- See `scheduled_tasks.py` comments for Celery setup

---

## Troubleshooting

### Issue: "No module named 'services.adaptive'"

**Cause:** `ULTIMATE_AI_CONSULTATION_PATH` not set correctly

**Fix:**
```bash
# In .env, set absolute path
ULTIMATE_AI_CONSULTATION_PATH=/home/user/ultimate_ai_consultation

# Verify path exists
ls $ULTIMATE_AI_CONSULTATION_PATH/services/adaptive
```

### Issue: "Table 'plan_versions' does not exist"

**Cause:** Migration not run

**Fix:**
```bash
psql $DATABASE_URL < integration/migrations/001_adaptive_system.sql
```

### Issue: Reassessments not running automatically

**Cause:** Scheduler not initialized or disabled

**Fix:**
```bash
# Check .env
ENABLE_SCHEDULER=true

# Check logs for scheduler initialization
# Should see: "✅ Scheduler initialized - automatic reassessments enabled"

# Manually trigger to test
curl -X POST http://localhost:8000/api/v1/programs/{user_id}/reassess?force=true
```

### Issue: "Permission denied" on database functions

**Cause:** Functions not granted to authenticated role

**Fix:**
```sql
-- Run as superuser
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO authenticated;
```

### Issue: High API costs

**Cause:** Too many extraction calls

**Fix:**
```bash
# Reduce extraction frequency
ENABLE_CONVERSATIONAL_LOGGING=false  # Disable if not needed

# Or use only quick logging
ENABLE_QUICK_LOGGING=true
```

---

## API Endpoints Reference

### Programs API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/programs/generate` | Generate initial program |
| GET | `/api/v1/programs/{user_id}/active` | Get active plan details |
| GET | `/api/v1/programs/{user_id}/today` | Get today's workout/meals |
| POST | `/api/v1/programs/{user_id}/reassess` | Trigger reassessment |
| GET | `/api/v1/programs/{user_id}/progress` | Get progress metrics |
| GET | `/api/v1/programs/{user_id}/grocery-list` | Get shopping list |
| GET | `/api/v1/programs/{user_id}/plan-history` | Get version history |

---

## Database Schema Reference

### plan_versions

Stores complete plans as JSONB.

```sql
CREATE TABLE plan_versions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    version INTEGER NOT NULL,
    status TEXT NOT NULL,  -- 'active', 'superseded', 'archived'
    plan_data JSONB NOT NULL,  -- Complete plan with workouts, meals, etc.
    valid_from DATE NOT NULL,
    valid_until DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### plan_adjustments

Tracks all adjustments made during reassessments.

```sql
CREATE TABLE plan_adjustments (
    id UUID PRIMARY KEY,
    plan_id UUID REFERENCES plan_versions(id),
    from_version INTEGER,
    to_version INTEGER,
    adjustment_type TEXT,
    adjustment_reason TEXT,
    changes_json JSONB,
    progress_data_json JSONB,
    rationale TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Next Steps

1. **Frontend Integration**: See `integration/frontend/INTEGRATION.md`
2. **Add Consultation Flow**: Connect ConsultationAIService → generate_program
3. **Customize Templates**: Add more workout protocols in `services/programmer/templates/`
4. **Add Monitoring**: Set up alerts for failed reassessments

---

## Support

- **Documentation**: `docs/` in ultimate_ai_consultation
- **Examples**: `examples/` for working demos
- **Tests**: `tests/` for reference implementations
- **Issues**: Check README.md for contact info

---

## Summary

**Files copied**: 7
**Files modified**: 3
**Database migrations**: 2
**New API endpoints**: 7
**Total integration time**: ~4 hours

The system is now fully integrated and ready to:
- Generate evidence-based programs
- Track user progress automatically
- Adjust plans every 14 days based on data
- Extract structured logs from conversations
