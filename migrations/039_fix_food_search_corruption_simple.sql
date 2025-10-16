-- Migration: Fix Food Search Corruption Issue (SIMPLIFIED VERSION)
-- Date: 2025-10-16
-- Note: This version skips the trigram index if pg_trgm extension cannot be enabled

BEGIN;

-- 1. Fix NULL or invalid JSONB data in recipe_items
UPDATE foods
SET recipe_items = NULL
WHERE recipe_items IS NOT NULL
  AND (
    recipe_items::text = 'null'
    OR recipe_items::text = ''
    OR recipe_items::text = '""'
  );

-- 2. Ensure all ARRAY columns have valid data
UPDATE foods
SET dietary_flags = '{}'::text[]
WHERE dietary_flags IS NULL;

-- 3. Remove malformed entries from dietary_flags
UPDATE foods
SET dietary_flags = array_remove(dietary_flags, NULL)
WHERE dietary_flags @> ARRAY[NULL];

-- 4. Clean up text encoding issues in name
UPDATE foods
SET name = regexp_replace(name, '[^\x20-\x7E\x80-\xFF]', '', 'g')
WHERE name ~ '[^\x20-\x7E\x80-\xFF]';

-- 5. Clean up text encoding issues in brand_name
UPDATE foods
SET brand_name = regexp_replace(brand_name, '[^\x20-\x7E\x80-\xFF]', '', 'g')
WHERE brand_name IS NOT NULL
  AND brand_name ~ '[^\x20-\x7E\x80-\xFF]';

-- 6. Remove orphaned food_servings
DELETE FROM food_servings
WHERE food_id NOT IN (SELECT id FROM foods);

-- 7. Fix NaN/Infinity in calories_per_100g
UPDATE foods
SET calories_per_100g = 0
WHERE calories_per_100g IS NULL
   OR calories_per_100g::text IN ('NaN', 'Infinity', '-Infinity');

-- 8. Fix NaN/Infinity in protein_g_per_100g
UPDATE foods
SET protein_g_per_100g = 0
WHERE protein_g_per_100g IS NULL
   OR protein_g_per_100g::text IN ('NaN', 'Infinity', '-Infinity');

-- 9. Fix NaN/Infinity in carbs_g_per_100g
UPDATE foods
SET carbs_g_per_100g = 0
WHERE carbs_g_per_100g IS NULL
   OR carbs_g_per_100g::text IN ('NaN', 'Infinity', '-Infinity');

-- 10. Fix NaN/Infinity in fat_g_per_100g
UPDATE foods
SET fat_g_per_100g = 0
WHERE fat_g_per_100g IS NULL
   OR fat_g_per_100g::text IN ('NaN', 'Infinity', '-Infinity');

-- 11. Create safe view for food search
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

-- 12. Add basic index for search (no trigram needed)
CREATE INDEX IF NOT EXISTS idx_foods_search
ON foods (is_public, usage_count DESC, verified DESC)
WHERE is_public = true;

COMMIT;

-- NOTES:
-- This simplified version skips the trigram index
-- The ILIKE search will still work, just slightly slower on large datasets
-- All data corruption cleanup is still performed
