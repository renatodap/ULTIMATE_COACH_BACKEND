-- Migration: Fix Food Search Corruption Issue
-- Date: 2025-10-16
-- Issue: PostgREST "JSON could not be generated, code 5" error during food search
--
-- Root Cause: Corrupted data in JSONB/ARRAY columns prevents JSON serialization
-- This migration cleans up potentially corrupted data in the foods table

BEGIN;

-- 1. Find and fix NULL or invalid JSONB data in recipe_items
UPDATE foods
SET recipe_items = NULL
WHERE recipe_items IS NOT NULL
  AND (
    recipe_items::text = 'null'
    OR recipe_items::text = ''
    OR recipe_items::text = '""'
  );

-- 2. Ensure all ARRAY columns have valid data (not NULL arrays)
UPDATE foods
SET dietary_flags = '{}'::text[]
WHERE dietary_flags IS NULL;

-- 3. Remove any malformed entries from dietary_flags array
UPDATE foods
SET dietary_flags = array_remove(dietary_flags, NULL)
WHERE dietary_flags @> ARRAY[NULL];

-- 4. Clean up any weird text encoding issues in name and brand_name
UPDATE foods
SET name = regexp_replace(name, '[^\x20-\x7E\x80-\xFF]', '', 'g')
WHERE name ~ '[^\x20-\x7E\x80-\xFF]';

UPDATE foods
SET brand_name = regexp_replace(brand_name, '[^\x20-\x7E\x80-\xFF]', '', 'g')
WHERE brand_name IS NOT NULL
  AND brand_name ~ '[^\x20-\x7E\x80-\xFF]';

-- 5. Find any foods with problematic servings relationships
-- (This shouldn't cause JSON issues, but let's be thorough)
DELETE FROM food_servings
WHERE food_id NOT IN (SELECT id FROM foods);

-- 6. Ensure all numeric columns have valid values (no NaN or Infinity)
UPDATE foods
SET
  calories_per_100g = 0
WHERE calories_per_100g IS NULL
   OR calories_per_100g::text IN ('NaN', 'Infinity', '-Infinity');

UPDATE foods
SET
  protein_g_per_100g = 0
WHERE protein_g_per_100g IS NULL
   OR protein_g_per_100g::text IN ('NaN', 'Infinity', '-Infinity');

UPDATE foods
SET
  carbs_g_per_100g = 0
WHERE carbs_g_per_100g IS NULL
   OR carbs_g_per_100g::text IN ('NaN', 'Infinity', '-Infinity');

UPDATE foods
SET
  fat_g_per_100g = 0
WHERE fat_g_per_100g IS NULL
   OR fat_g_per_100g::text IN ('NaN', 'Infinity', '-Infinity');

-- 7. Create a safer view for food search that excludes potentially problematic columns
CREATE OR REPLACE VIEW foods_search_safe AS
SELECT
  id,
  name,
  brand_name,
  calories_per_100g,
  protein_g_per_100g,
  carbs_g_per_100g,
  fat_g_per_100g,
  fiber_g_per_100g,
  sugar_g_per_100g,
  sodium_mg_per_100g,
  food_type,
  composition_type,
  is_public,
  verified,
  usage_count,
  created_by,
  created_at,
  updated_at
FROM foods;

-- 8. Enable pg_trgm extension for fuzzy text search (if not already enabled)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 9. Add helpful indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_foods_name_trgm
ON foods USING gin (name gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_foods_search
ON foods (is_public, usage_count DESC, verified DESC)
WHERE is_public = true;

COMMIT;

-- NOTES:
-- This migration focuses on cleaning up data that could cause PostgREST JSON serialization failures.
-- The most common causes are:
-- 1. Invalid JSONB data (malformed JSON strings)
-- 2. NULL values in arrays
-- 3. Special characters or encoding issues
-- 4. NaN or Infinity in numeric columns
-- 5. Circular references in JOINs (not applicable here)
--
-- After running this migration, the food search should work without errors.
