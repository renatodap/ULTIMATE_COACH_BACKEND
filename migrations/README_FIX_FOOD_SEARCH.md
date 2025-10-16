# Food Search Fix - Quick Guide

## Problem
Food search returns 500 error: "JSON could not be generated, code 5"

## Root Cause
Corrupted data in the `foods` table (JSONB, ARRAY, or numeric columns) prevents PostgREST from serializing results to JSON.

## Solution
Apply the `039_fix_food_search_corruption.sql` migration to clean up the data.

---

## How to Apply (Via Supabase Dashboard)

### Step 1: Open Supabase SQL Editor
1. Go to your Supabase dashboard: https://supabase.com/dashboard
2. Select your project
3. Click "SQL Editor" in the left sidebar
4. Click "New query"

### Step 2: Copy the Migration SQL
1. Open `migrations/039_fix_food_search_corruption.sql`
2. Copy the entire contents

### Step 3: Execute the Migration
1. Paste the SQL into the SQL Editor
2. Click "Run" button (or press Ctrl+Enter)
3. Wait for completion (should take a few seconds)
4. Check for any error messages

### Step 4: Verify the Fix
1. Go to your frontend application
2. Navigate to the nutrition log page
3. Try searching for "chicken"
4. The search should now return results without errors

---

## What the Migration Does

1. **Cleans up JSONB data**: Removes NULL or invalid JSON in `recipe_items`
2. **Fixes ARRAY columns**: Ensures `dietary_flags` has valid array data
3. **Text encoding cleanup**: Removes special characters that can't be serialized
4. **Orphaned data cleanup**: Removes `food_servings` without valid `food_id`
5. **Numeric validation**: Fixes NaN/Infinity values in nutrition columns
6. **Creates safe view**: Adds `foods_search_safe` view excluding problematic columns
7. **Performance indexes**: Adds indexes for faster text search

---

## Alternative: Test Without Migration

If you want to test without applying the migration, the backend already has fallback logic that should work:

1. The first query tries: `SELECT *, food_servings(*)`
2. If that fails, it falls back to: `SELECT id, name, brand_name, ...` (without servings)
3. Then it fetches servings separately for each food

However, applying the migration is recommended for best performance and data integrity.

---

## Verification Queries

After applying the migration, you can verify the cleanup:

```sql
-- Check for any remaining NULL arrays
SELECT COUNT(*) FROM foods WHERE dietary_flags IS NULL;
-- Expected: 0

-- Check for invalid JSONB
SELECT COUNT(*) FROM foods
WHERE recipe_items IS NOT NULL
AND recipe_items::text IN ('null', '', '""');
-- Expected: 0

-- Check for NaN/Infinity in numeric columns
SELECT COUNT(*) FROM foods
WHERE calories_per_100g::text IN ('NaN', 'Infinity', '-Infinity');
-- Expected: 0

-- Test the search directly
SELECT id, name, brand_name, calories_per_100g
FROM foods
WHERE is_public = true
AND name ILIKE '%chicken%'
ORDER BY usage_count DESC, verified DESC
LIMIT 10;
-- Expected: Should return results without error
```

---

## Troubleshooting

### If migration fails:
1. Check the error message
2. Run the verification queries above to identify problematic rows
3. Manually fix those rows before re-running the migration

### If search still fails after migration:
1. Check backend logs for specific error details
2. Try restarting the backend server
3. Clear any Redis/cache if you have caching enabled
4. Check Supabase logs in the dashboard

### If you see specific food IDs causing issues:
```sql
-- Delete specific problematic foods (replace UUID with actual ID)
DELETE FROM food_servings WHERE food_id = 'problematic-uuid';
DELETE FROM foods WHERE id = 'problematic-uuid';
```

---

## Need Help?
1. Check backend logs for detailed error messages
2. Check Supabase logs in dashboard > Logs
3. Run the verification queries above
4. If all else fails, you can temporarily disable public foods and only use custom foods:
   ```sql
   UPDATE foods SET is_public = false WHERE is_public = true;
   ```

