-- ============================================================================
-- FOOD SEARCH DIAGNOSTIC QUERIES
-- ============================================================================
-- Run these queries in Supabase SQL Editor to diagnose why no foods show up
-- Date: 2025-10-16
-- ============================================================================

-- ============================================================================
-- STEP 1: Check if foods table exists and has data
-- ============================================================================

-- Query 1: Count total foods
SELECT COUNT(*) as total_foods FROM foods;
-- EXPECTED: > 0 (should have at least some foods)
-- IF 0: Database is empty - need to run seed migrations

-- Query 2: Check foods by is_public status
SELECT
  is_public,
  COUNT(*) as count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM foods
GROUP BY is_public
ORDER BY is_public DESC;
-- EXPECTED: Some rows with is_public = true
-- IF ALL false: Need to fix is_public column

-- Query 3: Check if any foods match "chicken"
SELECT COUNT(*) as chicken_count
FROM foods
WHERE name ILIKE '%chicken%';
-- EXPECTED: > 0 (seeds include chicken foods)
-- IF 0: Either no seeds OR wrong column name

-- Query 4: Check public chicken foods specifically
SELECT COUNT(*) as public_chicken_count
FROM foods
WHERE name ILIKE '%chicken%' AND is_public = true;
-- EXPECTED: > 0
-- IF 0 but Query 3 > 0: is_public is false for all chickens

-- ============================================================================
-- STEP 2: Examine actual food data
-- ============================================================================

-- Query 5: Show sample of existing foods with all relevant columns
SELECT
  id,
  name,
  brand_name,
  is_public,
  verified,
  usage_count,
  created_by,
  created_at
FROM foods
ORDER BY created_at DESC
LIMIT 10;
-- CHECK:
-- - Are names readable?
-- - Is is_public true or false?
-- - Are created_by values NULL (public foods) or UUID (custom foods)?

-- Query 6: Find chicken foods specifically
SELECT
  id,
  name,
  brand_name,
  is_public,
  verified,
  calories_per_100g,
  protein_g_per_100g
FROM foods
WHERE name ILIKE '%chicken%'
ORDER BY usage_count DESC, verified DESC
LIMIT 10;
-- CHECK:
-- - Do chicken foods exist?
-- - What is their is_public value?
-- - Are they verified?

-- ============================================================================
-- STEP 3: Check food_servings relationship
-- ============================================================================

-- Query 7: Check if food_servings exist
SELECT COUNT(*) as total_servings FROM food_servings;
-- EXPECTED: > 0
-- IF 0: Foods have no servings (will cause issues when adding to meal)

-- Query 8: Check foods without servings
SELECT
  f.id,
  f.name,
  f.is_public,
  COUNT(fs.id) as serving_count
FROM foods f
LEFT JOIN food_servings fs ON f.id = fs.food_id
GROUP BY f.id, f.name, f.is_public
HAVING COUNT(fs.id) = 0
LIMIT 10;
-- CHECK: Are there foods with 0 servings?

-- Query 9: Check orphaned servings (servings without foods)
SELECT COUNT(*) as orphaned_servings
FROM food_servings fs
WHERE NOT EXISTS (SELECT 1 FROM foods f WHERE f.id = fs.food_id);
-- EXPECTED: 0
-- IF > 0: Data integrity issue

-- ============================================================================
-- STEP 4: Test the exact query the backend uses
-- ============================================================================

-- Query 10: Simulate backend search query for "chicken"
SELECT
  f.id,
  f.name,
  f.brand_name,
  f.calories_per_100g,
  f.protein_g_per_100g,
  f.is_public,
  f.verified,
  f.usage_count,
  COUNT(fs.id) as servings_count
FROM foods f
LEFT JOIN food_servings fs ON f.id = fs.food_id
WHERE f.is_public = true
  AND f.name ILIKE '%chicken%'
GROUP BY f.id, f.name, f.brand_name, f.calories_per_100g,
         f.protein_g_per_100g, f.is_public, f.verified, f.usage_count
ORDER BY f.usage_count DESC, f.verified DESC
LIMIT 20;
-- This is exactly what the backend should return
-- IF EMPTY: Problem is in the database, not the backend

-- ============================================================================
-- STEP 5: Check RLS policies
-- ============================================================================

-- Query 11: View RLS policies on foods table
SELECT
  schemaname,
  tablename,
  policyname,
  permissive,
  roles,
  cmd,
  qual,
  with_check
FROM pg_policies
WHERE tablename = 'foods';
-- CHECK:
-- - Is there a policy for SELECT?
-- - Does it check is_public = TRUE?

-- Query 12: Check if RLS is enabled
SELECT
  schemaname,
  tablename,
  rowsecurity
FROM pg_tables
WHERE tablename = 'foods';
-- rowsecurity should be TRUE
-- NOTE: Service role BYPASSES RLS anyway

-- ============================================================================
-- STEP 6: Check column names and types
-- ============================================================================

-- Query 13: Verify column names and types
SELECT
  column_name,
  data_type,
  is_nullable,
  column_default
FROM information_schema.columns
WHERE table_name = 'foods'
  AND column_name IN ('id', 'name', 'is_public', 'verified', 'calories_per_100g',
                       'protein_g_per_100g', 'carbs_g_per_100g', 'fat_g_per_100g')
ORDER BY ordinal_position;
-- CHECK:
-- - Is it "is_public" or "ispublic" or "public"?
-- - Is data_type correct (boolean for is_public)?

-- ============================================================================
-- INTERPRETATION GUIDE
-- ============================================================================
/*
SCENARIO 1: Query 1 returns 0
→ Database is empty
→ FIX: Run seed migrations 007-028

SCENARIO 2: Query 1 > 0 but Query 2 shows all is_public = false
→ All foods are private
→ FIX: UPDATE foods SET is_public = true WHERE is_public = false;

SCENARIO 3: Query 4 returns 0 but Query 3 > 0
→ Chicken foods exist but are not public
→ FIX: UPDATE foods SET is_public = true WHERE name ILIKE '%chicken%';

SCENARIO 4: Query 10 returns results but frontend shows nothing
→ Backend or frontend issue, not database
→ FIX: Check backend logs, add logging to nutrition_service.py

SCENARIO 5: All queries return 0
→ Either wrong table name OR wrong database
→ FIX: Verify SUPABASE_URL in backend .env

SCENARIO 6: Query 8 shows foods without servings
→ Foods exist but no serving sizes defined
→ FIX: Run seed migrations OR manually add servings

SCENARIO 7: Query 13 shows different column name
→ Column name mismatch
→ FIX: Update backend query to use correct column name
*/
