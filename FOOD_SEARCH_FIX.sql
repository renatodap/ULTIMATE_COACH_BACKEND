-- ============================================================================
-- FOOD SEARCH FIX SCRIPT
-- ============================================================================
-- Apply fixes based on diagnostic results
-- Date: 2025-10-16
-- IMPORTANT: Run diagnostics first (FOOD_SEARCH_DIAGNOSTIC.sql)
-- ============================================================================

-- ============================================================================
-- FIX 1: Make all foods public (if all are private)
-- ============================================================================
-- Use if: Query 2 shows all is_public = false

BEGIN;

UPDATE foods
SET is_public = true,
    updated_at = NOW()
WHERE is_public = false
  OR is_public IS NULL;

-- Verify fix
SELECT
  'After Fix 1' as status,
  COUNT(*) as total_foods,
  COUNT(*) FILTER (WHERE is_public = true) as public_foods,
  COUNT(*) FILTER (WHERE is_public = false) as private_foods
FROM foods;

COMMIT;

-- ============================================================================
-- FIX 2: Make all foods verified (if none are verified)
-- ============================================================================
-- Use if: Query 6 shows verified = false for all foods

BEGIN;

UPDATE foods
SET verified = true,
    updated_at = NOW()
WHERE verified = false
  OR verified IS NULL;

-- Verify fix
SELECT
  'After Fix 2' as status,
  COUNT(*) as total_foods,
  COUNT(*) FILTER (WHERE verified = true) as verified_foods
FROM foods;

COMMIT;

-- ============================================================================
-- FIX 3: Fix NULL is_public values
-- ============================================================================
-- Use if: Query 2 shows NULL values

BEGIN;

UPDATE foods
SET is_public = true,
    updated_at = NOW()
WHERE is_public IS NULL;

-- Verify fix
SELECT
  'After Fix 3' as status,
  COUNT(*) as total_foods,
  COUNT(*) FILTER (WHERE is_public IS NULL) as null_public
FROM foods;

COMMIT;

-- ============================================================================
-- FIX 4: Reset usage_count (if all are 0)
-- ============================================================================
-- Use if: Foods have usage_count = 0 (affects search ranking)

BEGIN;

-- Set default usage counts based on food type
UPDATE foods
SET usage_count = CASE
  WHEN food_type = 'ingredient' AND verified = true THEN 100
  WHEN food_type = 'dish' AND verified = true THEN 50
  WHEN food_type = 'branded' THEN 25
  WHEN food_type = 'restaurant' THEN 25
  ELSE 10
END,
updated_at = NOW()
WHERE usage_count = 0 OR usage_count IS NULL;

-- Verify fix
SELECT
  'After Fix 4' as status,
  food_type,
  AVG(usage_count) as avg_usage,
  MIN(usage_count) as min_usage,
  MAX(usage_count) as max_usage
FROM foods
GROUP BY food_type;

COMMIT;

-- ============================================================================
-- FIX 5: Add default servings to foods without any
-- ============================================================================
-- Use if: Query 8 shows foods with 0 servings

BEGIN;

-- Add 100g serving to foods that have no servings
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT
  f.id,
  100,
  'g',
  '100 grams',
  100,
  true,
  0
FROM foods f
WHERE NOT EXISTS (
  SELECT 1 FROM food_servings fs WHERE fs.food_id = f.id
);

-- Verify fix
SELECT
  'After Fix 5' as status,
  COUNT(DISTINCT f.id) as total_foods,
  COUNT(DISTINCT fs.food_id) as foods_with_servings,
  COUNT(DISTINCT f.id) - COUNT(DISTINCT fs.food_id) as foods_without_servings
FROM foods f
LEFT JOIN food_servings fs ON f.id = fs.food_id;

COMMIT;

-- ============================================================================
-- FIX 6: Remove orphaned servings
-- ============================================================================
-- Use if: Query 9 shows orphaned servings > 0

BEGIN;

DELETE FROM food_servings
WHERE food_id NOT IN (SELECT id FROM foods);

-- Verify fix
SELECT
  'After Fix 6' as status,
  COUNT(*) as orphaned_servings
FROM food_servings fs
WHERE NOT EXISTS (SELECT 1 FROM foods f WHERE f.id = fs.food_id);

COMMIT;

-- ============================================================================
-- FIX 7: Fix corrupted data (from original migration)
-- ============================================================================
-- Apply the cleanup migration if not already done

BEGIN;

-- Fix NULL arrays in dietary_flags
UPDATE foods
SET dietary_flags = '{}'::text[]
WHERE dietary_flags IS NULL;

-- Remove NULL elements from dietary_flags
UPDATE foods
SET dietary_flags = array_remove(dietary_flags, NULL)
WHERE dietary_flags @> ARRAY[NULL];

-- Fix invalid JSONB in recipe_items
UPDATE foods
SET recipe_items = NULL
WHERE recipe_items IS NOT NULL
  AND recipe_items::text IN ('null', '', '""');

-- Fix NaN/Infinity in numeric columns
UPDATE foods
SET calories_per_100g = 0
WHERE calories_per_100g IS NULL
   OR calories_per_100g::text IN ('NaN', 'Infinity', '-Infinity');

UPDATE foods
SET protein_g_per_100g = 0
WHERE protein_g_per_100g IS NULL
   OR protein_g_per_100g::text IN ('NaN', 'Infinity', '-Infinity');

UPDATE foods
SET carbs_g_per_100g = 0
WHERE carbs_g_per_100g IS NULL
   OR carbs_g_per_100g::text IN ('NaN', 'Infinity', '-Infinity');

UPDATE foods
SET fat_g_per_100g = 0
WHERE fat_g_per_100g IS NULL
   OR fat_g_per_100g::text IN ('NaN', 'Infinity', '-Infinity');

-- Verify fix
SELECT
  'After Fix 7' as status,
  COUNT(*) FILTER (WHERE dietary_flags IS NULL) as null_dietary_flags,
  COUNT(*) FILTER (WHERE calories_per_100g::text IN ('NaN', 'Infinity', '-Infinity')) as nan_calories
FROM foods;

COMMIT;

-- ============================================================================
-- COMPREHENSIVE VERIFICATION
-- ============================================================================
-- Run this after applying fixes to verify everything works

SELECT
  'Final Status' as check_name,
  COUNT(*) as total_foods,
  COUNT(*) FILTER (WHERE is_public = true) as public_foods,
  COUNT(*) FILTER (WHERE verified = true) as verified_foods,
  COUNT(*) FILTER (WHERE name ILIKE '%chicken%' AND is_public = true) as public_chicken,
  (SELECT COUNT(DISTINCT food_id) FROM food_servings) as foods_with_servings,
  AVG(usage_count) as avg_usage_count
FROM foods;

-- Test the actual search query
SELECT
  'Search Test: chicken' as test_name,
  COUNT(*) as result_count
FROM foods f
WHERE f.is_public = true
  AND f.name ILIKE '%chicken%';

-- If result_count > 0, the search should work!

-- ============================================================================
-- ROLLBACK SCRIPT (If fixes cause issues)
-- ============================================================================
-- ONLY use if fixes made things worse

/*
BEGIN;

-- Rollback Fix 1 (revert all to private - NOT RECOMMENDED)
UPDATE foods SET is_public = false WHERE is_public = true;

-- Rollback Fix 2 (revert verified)
UPDATE foods SET verified = false WHERE verified = true;

ROLLBACK; -- or COMMIT if you really want to rollback
*/
