# Food Search Fix Guide - Complete Solution

## Problem Summary
Food search returns 0 results despite database being "seeded". User searches for "chicken" and sees no results in the UI.

## Root Cause
**The database has no public foods.** Backend works correctly (uses service role, bypasses RLS, has fallback logic), frontend works correctly (handles response properly), but the database is empty or all foods have `is_public = false`.

---

## Quick Fix (5 Minutes)

If you just want it working NOW:

### Option A: Make All Foods Public
```sql
-- Run in Supabase SQL Editor
UPDATE foods SET is_public = true WHERE is_public = false OR is_public IS NULL;
```

### Option B: Run Seed Migrations
Apply migrations in order: `007`, `012`, `013`, `014`, `015`, `016`, `017`, `018`, `019`, `020`, `021`, `022`, `023`, `024`, `025`, `026`, `027`, `028`

---

## Complete Fix (20 Minutes - Recommended)

### Step 1: Run Diagnostics (5 minutes)

1. Open Supabase Dashboard → Your Project → SQL Editor
2. Click "New Query"
3. Copy contents of `FOOD_SEARCH_DIAGNOSTIC.sql`
4. Run each query section individually
5. Note the results for each query

**Key Questions:**
- Query 1: Does database have ANY foods? (If 0 → Run seeds)
- Query 2: Are any foods public? (If all false → Run Fix 1)
- Query 4: Are any chicken foods public? (If 0 → Run Fix 1)
- Query 10: Does simulated backend query return results? (If yes → Backend issue, if no → Database issue)

### Step 2: Apply Appropriate Fix (5 minutes)

Based on diagnostic results, run ONE of these:

#### Fix 1: Make Foods Public (Most Common)
```sql
-- From FOOD_SEARCH_FIX.sql - FIX 1
BEGIN;
UPDATE foods
SET is_public = true, updated_at = NOW()
WHERE is_public = false OR is_public IS NULL;
COMMIT;
```

#### Fix 2: Database is Empty (Run Seeds)
```bash
# In Supabase SQL Editor, run these migrations in order:
# 007_seed_common_foods.sql
# 012_seed_proteins_extended.sql
# 013_seed_carbs_grains.sql
# (... continue through 028)

# Or use Supabase CLI:
cd ULTIMATE_COACH_BACKEND/migrations
supabase db push
```

#### Fix 3: Add Default Servings (If Query 8 shows foods without servings)
```sql
-- From FOOD_SEARCH_FIX.sql - FIX 5
BEGIN;
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT f.id, 100, 'g', '100 grams', 100, true, 0
FROM foods f
WHERE NOT EXISTS (SELECT 1 FROM food_servings fs WHERE fs.food_id = f.id);
COMMIT;
```

#### Fix 4: Data Corruption (If Query 7 shows corrupted data)
```sql
-- From 039_fix_food_search_corruption_simple.sql
-- Run the entire migration
```

### Step 3: Verify Fix (2 minutes)

Run this test query:
```sql
SELECT
  id,
  name,
  brand_name,
  calories_per_100g,
  is_public,
  verified
FROM foods
WHERE is_public = true
  AND name ILIKE '%chicken%'
ORDER BY usage_count DESC, verified DESC
LIMIT 10;
```

**Expected Result:** Should return 5-10 chicken foods

### Step 4: Test in Application (3 minutes)

1. Restart backend if you applied logging changes:
   ```bash
   cd ULTIMATE_COACH_BACKEND
   # If running locally:
   uvicorn app.main:app --reload
   ```

2. Open frontend application
3. Navigate to Nutrition → Log Meal
4. Search for "chicken"
5. **Expected:** List of chicken foods appears

### Step 5: Check Enhanced Logs (2 minutes)

With the new logging, check backend console for:
```
search_foods_query_starting: query="chicken", limit=20
search_foods_query_completed: results_count=10, sample_results=[...]
```

If `results_count=0`, database still has issues. Re-run diagnostics.

---

## Troubleshooting

### Issue: Still Getting 0 Results After Fix 1

**Possible Causes:**
1. Wrong Supabase project (verify `SUPABASE_URL` in backend `.env`)
2. Column name mismatch (run Query 13 from diagnostics)
3. RLS blocking queries (unlikely with service role, but run Query 11)

**Solution:**
```sql
-- Check if foods actually got updated
SELECT is_public, COUNT(*) FROM foods GROUP BY is_public;
-- If still shows false, update didn't work - check transaction

-- Try direct update with explicit transaction
BEGIN;
UPDATE foods SET is_public = true;
SELECT is_public, COUNT(*) FROM foods GROUP BY is_public;
-- Should show all true now
COMMIT;
```

### Issue: Foods Appear But Have No Servings

**Symptoms:** Foods show in search but can't be added to meal

**Solution:**
```sql
-- Run Fix 5 from FOOD_SEARCH_FIX.sql
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT f.id, 100, 'g', '100 grams', 100, true, 0
FROM foods f
WHERE NOT EXISTS (SELECT 1 FROM food_servings fs WHERE fs.food_id = f.id);
```

### Issue: Backend Logs Show Results But Frontend Shows Nothing

**Symptoms:**
- Backend logs: `results_count=10`
- Frontend: Empty results

**Solution:**
1. Open browser console (F12)
2. Go to Network tab
3. Search for "chicken"
4. Find request to `/api/v1/foods/search?q=chicken`
5. Check response JSON

**If response has foods:** Frontend issue
- Verify `searchResults` state is being set
- Check if results are being filtered out
- Verify rendering logic

**If response is empty:** Backend issue
- Check if authentication is working
- Verify `current_user["id"]` is valid
- Check backend logs for errors

### Issue: Seed Migrations Won't Apply

**Possible Causes:**
1. Migration already applied (check `supabase_migrations` table)
2. SQL syntax error in migration
3. Missing dependencies (UUID extension, etc.)

**Solution:**
```sql
-- Check which migrations have been applied
SELECT * FROM supabase_migrations ORDER BY version;

-- If 007 is missing, apply it manually:
-- Copy contents of 007_seed_common_foods.sql into SQL Editor
-- Run it

-- If it fails, check error message
-- Common issues:
-- - "foods table does not exist" → Run schema migrations first
-- - "duplicate key value" → Seeds already exist, skip
-- - "uuid_generate_v4 does not exist" → Run: CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

---

## Prevention

To prevent this issue in the future:

### 1. Add Verification Test

Create `ULTIMATE_COACH_BACKEND/tests/test_food_seeding.py`:
```python
import pytest
from app.services.supabase_service import supabase_service

def test_public_foods_exist():
    """Verify database has public foods"""
    response = supabase_service.client.table("foods")\
        .select("id", count="exact")\
        .eq("is_public", True)\
        .limit(1)\
        .execute()

    assert response.count > 0, "No public foods in database!"

def test_chicken_foods_exist():
    """Verify specific seed foods exist"""
    response = supabase_service.client.table("foods")\
        .select("id", count="exact")\
        .eq("is_public", True)\
        .ilike("name", "%chicken%")\
        .limit(1)\
        .execute()

    assert response.count > 0, "No public chicken foods in database!"
```

### 2. Add Health Check Endpoint

In `app/api/v1/health.py`:
```python
@router.get("/health/db-seeds")
async def check_db_seeds():
    """Verify critical seed data exists"""
    response = supabase_service.client.table("foods")\
        .select("id", count="exact")\
        .eq("is_public", True)\
        .limit(1)\
        .execute()

    public_foods_count = response.count

    return {
        "public_foods_exist": public_foods_count > 0,
        "public_foods_count": public_foods_count,
        "status": "healthy" if public_foods_count > 0 else "unhealthy"
    }
```

### 3. Document Seed Order

Create `migrations/SEED_ORDER.md`:
```markdown
# Seed Migration Order

Run these in order to populate the database:

1. 007_seed_common_foods.sql - Core foods (80 items)
2. 012_seed_proteins_extended.sql - More proteins
3. 013_seed_carbs_grains.sql - Carbs and grains
4. 014_seed_fats_dairy.sql - Fats and dairy
5. ... (continue through 028)

## Verification
After running seeds, verify:
SELECT COUNT(*) FROM foods WHERE is_public = true;
-- Expected: > 100
```

---

## Files Created

### Diagnostic Tools
- **`FOOD_SEARCH_DIAGNOSTIC.sql`** - 13 diagnostic queries with interpretation guide
- **`FOOD_SEARCH_FIX.sql`** - 7 fix scripts for common issues
- **`FOOD_SEARCH_FIX_GUIDE.md`** - This file (step-by-step guide)

### Code Changes
- **`app/services/nutrition_service.py`** - Enhanced logging for diagnostics
- **`migrations/039_fix_food_search_corruption.sql`** - Data cleanup migration
- **`migrations/039_fix_food_search_corruption_simple.sql`** - Simplified cleanup

### Documentation
- **`FOOD_SEARCH_FIX_SUMMARY.md`** - Original root cause analysis
- **`migrations/README_FIX_FOOD_SEARCH.md`** - Migration application guide

---

## Success Criteria Checklist

- [ ] Diagnostic Query 1: `COUNT(*) > 0` (foods exist)
- [ ] Diagnostic Query 2: Some foods have `is_public = true`
- [ ] Diagnostic Query 4: Chicken foods have `is_public = true`
- [ ] Diagnostic Query 10: Simulated backend query returns results
- [ ] Backend logs show: `results_count > 0`
- [ ] Frontend search displays results
- [ ] User can select food and add to meal
- [ ] Food has servings (can complete meal logging)

---

## Time Estimates

| Task | Time | Notes |
|------|------|-------|
| Run diagnostics | 5 min | Just copy/paste queries |
| Apply Fix 1 (make public) | 1 min | Single UPDATE query |
| Apply Fix 2 (run seeds) | 10 min | Multiple migrations |
| Restart backend | 1 min | If logging added |
| Test in UI | 2 min | Search + add food |
| Verify logs | 1 min | Check backend console |
| **Total (Quick Fix)** | **10 min** | Diagnostics + Fix 1 + Test |
| **Total (Complete)** | **20 min** | Diagnostics + Any Fix + Test + Verify |

---

## Contact

If issues persist after following this guide:
- Check backend logs for errors
- Verify Supabase project URL is correct
- Ensure backend is using SERVICE_KEY (not ANON_KEY)
- Check if RLS policies are too restrictive (unlikely)

---

**Last Updated:** 2025-10-16
**Version:** 1.0.0
