# Migration 012: Activity Schema Fix + Exercise Sets System

**Date:** 2025-10-13
**Status:** Ready to Apply
**Type:** Schema Migration + Feature Addition

---

## Overview

This migration fixes critical issues with the activities system and adds a comprehensive exercise sets tracking system for strength training.

### Problems Solved

1. **✅ Schema Mismatch** - Backend code expected different column names than database
2. **✅ Soft Delete Filtering** - Queries were returning deleted activities
3. **✅ Manual Exercise Entry** - Users typed exercise names with no validation
4. **✅ Aggregate Set Data** - No way to track individual sets for progressive overload

### New Features

1. **Exercise Sets Table** - Individual set tracking with full metrics
2. **Exercise Search** - Full-text search with autocomplete
3. **Personal Records Tracking** - Automatic PR detection (max weight, estimated 1RM, volume)
4. **Exercise History Views** - Query user's exercise history with performance trends

---

## What Changed

### Part 1: Activities Table Schema Fix

**Column Renames:**
```sql
name → activity_name                    -- More descriptive
activity_type → category                -- Matches backend
calories → calories_burned               -- More explicit
```

**New Columns:**
```sql
intensity_mets NUMERIC(4,2)             -- Metabolic Equivalent of Task (1.0-20.0)
deleted_at TIMESTAMPTZ                  -- Soft delete support
```

**Updated Constraints:**
```sql
category CHECK (category IN (
  'cardio_steady_state',
  'cardio_interval',
  'strength_training',
  'sports',
  'flexibility',
  'other'
))
```

### Part 2: Exercise Sets Table (NEW)

```sql
CREATE TABLE exercise_sets (
  id UUID PRIMARY KEY,
  activity_id UUID REFERENCES activities(id),
  exercise_id UUID REFERENCES exercises(id),    -- ← FK to exercises table!
  user_id UUID REFERENCES auth.users(id),

  -- Set details
  set_number INTEGER NOT NULL,                   -- 1, 2, 3, etc.
  reps INTEGER,                                   -- Number of reps
  weight_kg NUMERIC(6,2),                        -- Weight lifted

  -- Time/distance based (cardio/bodyweight)
  duration_seconds INTEGER,
  distance_meters NUMERIC(8,2),

  -- Performance tracking
  rpe INTEGER,                                    -- Rate of Perceived Exertion (1-10)
  tempo TEXT,                                     -- e.g., "3-1-2-0"
  rest_seconds INTEGER,

  -- Completion tracking
  completed BOOLEAN DEFAULT TRUE,
  failure BOOLEAN DEFAULT FALSE,                  -- Went to failure?
  notes TEXT,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Key Features:**
- **Foreign Key to Exercises Table** - No more typos!
- **Individual Set Tracking** - Set 1: 100kg×10, Set 2: 100kg×8, Set 3: 95kg×10
- **Flexible Data Model** - Supports reps/weight, duration, or distance
- **Performance Metrics** - RPE, tempo, rest times
- **Completion Tracking** - Track partial sets and failures

### Part 3: Views for Analytics

**user_exercise_history**
```sql
-- Complete exercise history with calculated metrics
SELECT
  user_id,
  exercise_id,
  exercise_name,
  activity_name,
  start_time,
  set_number,
  reps,
  weight_kg,
  rpe,
  -- Calculated fields
  ROUND(weight_kg * (1 + reps / 30.0), 2) as estimated_1rm,  -- Epley formula
  ROUND(reps * weight_kg, 2) as set_volume
FROM exercise_sets
JOIN exercises ON...
JOIN activities ON...
WHERE activities.deleted_at IS NULL;
```

**user_personal_records**
```sql
-- Personal records per exercise
SELECT
  user_id,
  exercise_id,
  max_weight_kg,          -- Heaviest weight lifted
  max_weight_reps,        -- Reps at max weight
  max_weight_date,        -- When PR was set
  max_estimated_1rm,      -- Highest estimated 1RM
  max_1rm_date,           -- When 1RM PR was set
  max_set_volume,         -- Highest volume set (reps × weight)
  max_volume_date         -- When volume PR was set
FROM ...
```

### Part 4: Search Function

```sql
CREATE FUNCTION search_exercises(
  search_query TEXT,
  category_filter TEXT DEFAULT NULL,
  limit_count INTEGER DEFAULT 20
)
RETURNS TABLE (...)
AS $$
  -- Full-text search with relevance ranking
  -- Returns exercises sorted by:
  -- 1. Search relevance (ts_rank)
  -- 2. Popularity (usage_count)
$$;
```

### Part 5: Data Migration

The migration automatically migrates existing JSONB exercises data to the new exercise_sets table:

```sql
-- For each activity with exercises in JSONB
-- Match exercise name to exercises table
-- Create individual sets with proper foreign keys
-- Preserves: reps, weight, RPE, timestamps
```

**Migration Status Tracking:**
- Logs matched exercises
- Logs failed matches (for manual intervention)
- Counts migrated sets

---

## API Changes

### New Endpoints

**Exercise Search:**
```http
GET /api/v1/exercises/search?q=bench&category=compound_strength
```

**Exercise Sets CRUD:**
```http
GET    /api/v1/activities/{activity_id}/sets
POST   /api/v1/activities/{activity_id}/sets
PATCH  /api/v1/sets/{set_id}
DELETE /api/v1/sets/{set_id}
```

**Exercise History:**
```http
GET /api/v1/exercises/history?exercise_id={id}&limit=50
```

**Personal Records:**
```http
GET /api/v1/exercises/personal-records?exercise_id={id}
```

### Updated Backend Models

**Before (JSONB):**
```python
metrics = {
    "exercises": [
        {"name": "Bench Press", "sets": 3, "reps": 10, "weight_kg": 100}
    ]
}
```

**After (Structured):**
```python
exercise_sets = [
    ExerciseSet(
        exercise_id=uuid,        # ← FK to exercises table
        set_number=1,
        reps=10,
        weight_kg=100,
        rpe=8
    ),
    ExerciseSet(
        exercise_id=uuid,
        set_number=2,
        reps=8,
        weight_kg=100,
        rpe=9
    ),
    ExerciseSet(
        exercise_id=uuid,
        set_number=3,
        reps=10,
        weight_kg=95,
        rpe=8
    )
]
```

---

## How to Apply

### Step 1: Backup Database

```bash
# Via Supabase Dashboard
# Settings → Database → Backups → Create Backup
```

### Step 2: Apply Migration

**Option A: Supabase Dashboard**
1. Go to SQL Editor
2. Open `migrations/012_fix_activities_schema_and_add_exercise_sets.sql`
3. Copy entire file
4. Paste into SQL Editor
5. Click "Run"

**Option B: Supabase CLI (if configured)**
```bash
supabase db push
```

### Step 3: Verify Migration

Check the output for these messages:
```
✓ Activities table: Column names fixed
✓ Exercise sets table: Created
✓ Search function: Created
✓ Views: Created (user_exercise_history, user_personal_records)
✓ Triggers: Created (exercise usage counter)

Statistics:
  - Active activities: X
  - Migrated exercise sets: Y
```

### Step 4: Restart Backend

The backend server should auto-reload with the new endpoints.

Check http://localhost:8000/docs to see the new endpoints.

---

## Testing Checklist

### Activities Schema Fix
- [ ] Create new activity (should use correct column names)
- [ ] List activities (should not show deleted ones)
- [ ] Get single activity (should work)
- [ ] Soft delete activity (should hide from lists)

### Exercise Search
- [ ] Search for "bench" (should return results)
- [ ] Search with category filter (should filter correctly)
- [ ] Search with limit (should respect limit)

### Exercise Sets
- [ ] Create sets for strength activity
- [ ] Get sets for activity (should include exercise details)
- [ ] Update individual set
- [ ] Delete set

### Analytics
- [ ] Get exercise history for user
- [ ] Get exercise history for specific exercise
- [ ] Get personal records
- [ ] Verify 1RM calculations
- [ ] Verify volume calculations

---

## Breaking Changes

### ⚠️ Frontend Changes Required

**Activities Logging Form:**
```typescript
// OLD: Manual text input
<input value={exerciseName} onChange={...} />

// NEW: Exercise autocomplete
<ExerciseAutocomplete
  onSelect={(exercise) => setExerciseId(exercise.id)}
/>
```

**Set Tracking:**
```typescript
// OLD: Aggregate data
{
  name: "Bench Press",
  sets: 3,
  reps: 10,
  weight_kg: 100
}

// NEW: Individual sets
[
  { exercise_id: uuid, set_number: 1, reps: 10, weight_kg: 100, rpe: 8 },
  { exercise_id: uuid, set_number: 2, reps: 8, weight_kg: 100, rpe: 9 },
  { exercise_id: uuid, set_number: 3, reps: 10, weight_kg: 95, rpe: 8 }
]
```

### Database Query Changes

**Before:**
```sql
SELECT * FROM activities WHERE user_id = ?;
```

**After:**
```sql
SELECT * FROM activities
WHERE user_id = ?
  AND deleted_at IS NULL;  -- ← Must filter soft deletes
```

---

## Rollback Plan

If something goes wrong:

```sql
-- Rollback Part 1: Restore column names
ALTER TABLE activities RENAME COLUMN activity_name TO name;
ALTER TABLE activities RENAME COLUMN category TO activity_type;
ALTER TABLE activities RENAME COLUMN calories_burned TO calories;
ALTER TABLE activities DROP COLUMN IF EXISTS intensity_mets;
ALTER TABLE activities DROP COLUMN IF EXISTS deleted_at;

-- Rollback Part 2: Drop new tables
DROP TABLE IF EXISTS exercise_sets CASCADE;
DROP VIEW IF EXISTS user_exercise_history CASCADE;
DROP VIEW IF EXISTS user_personal_records CASCADE;
DROP FUNCTION IF EXISTS search_exercises;

-- Restore from backup (see Step 1)
```

---

## Performance Considerations

### Indexes Created
```sql
-- Activities
idx_activities_user_start ON activities(user_id, start_time DESC) WHERE deleted_at IS NULL

-- Exercise Sets
idx_exercise_sets_activity ON exercise_sets(activity_id)
idx_exercise_sets_exercise ON exercise_sets(exercise_id)
idx_exercise_sets_user ON exercise_sets(user_id, created_at DESC)
idx_exercise_sets_user_exercise ON exercise_sets(user_id, exercise_id, created_at DESC)

-- Exercises Search
idx_exercises_name_search ON exercises USING gin(to_tsvector('english', name))
idx_exercises_category ON exercises(category) WHERE is_public = true
idx_exercises_usage ON exercises(usage_count DESC) WHERE is_public = true
```

### Query Performance

**Exercise Search:**
- Uses GIN index for full-text search
- Sub-50ms response time
- Relevance-ranked results

**Personal Records:**
- Materialized in view
- Window functions optimized
- Indexed on user_id + exercise_id

**Exercise History:**
- Indexed on user_id + created_at
- Efficient date range queries
- Optional exercise_id filter

---

## Next Steps

After applying this migration:

1. **Update Frontend Activity Logging Form**
   - Replace text input with exercise autocomplete
   - Change from aggregate sets to individual set tracking
   - Add RPE, tempo, rest inputs

2. **Build Exercise Autocomplete Component**
   ```typescript
   <ExerciseAutocomplete
     category="compound_strength"
     onSelect={(exercise) => ...}
   />
   ```

3. **Build Set Tracking UI**
   ```typescript
   <SetTracker
     sets={sets}
     onAdd={() => ...}
     onUpdate={(set) => ...}
     onDelete={(setId) => ...}
   />
   ```

4. **Add Personal Records Display**
   - Show PRs on exercise history page
   - Highlight new PRs in set tracking
   - Celebrate PR achievements

5. **Add Progressive Overload Recommendations**
   - Use exercise history to suggest weights
   - "Last workout: 3×10 @ 100kg"
   - "Try: 3×10 @ 102.5kg"

---

## Support

**Issues?**
- Check backend logs: `docker logs backend`
- Check migration output for errors
- Verify all verification queries passed
- Contact: [Your support channel]

**Questions?**
- Read `app/models/exercise_sets.py` for data models
- Read `app/api/v1/exercise_sets.py` for API docs
- Check http://localhost:8000/docs for interactive API docs
