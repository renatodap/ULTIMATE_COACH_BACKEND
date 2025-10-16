-- Diagnostic Queries for PostgREST Worker Crash on Food Search
-- Date: 2025-10-16
-- Issue: PostgREST returns Cloudflare Error 1101 (Worker threw exception)
--        when querying foods table with ILIKE pattern
--
-- Run these queries ONE AT A TIME in Supabase SQL Editor
-- Record the results for each query

-- ============================================================================
-- QUERY 1: Check table size and public food count
-- ============================================================================
-- Expected: Should return counts
-- If this fails: Table is severely corrupted or doesn't exist
SELECT
  'Total foods' as metric,
  COUNT(*) as count
FROM foods
UNION ALL
SELECT
  'Public foods' as metric,
  COUNT(*) as count
FROM foods WHERE is_public = true
UNION ALL
SELECT
  'Private foods' as metric,
  COUNT(*) as count
FROM foods WHERE is_public = false OR is_public IS NULL;

-- ============================================================================
-- QUERY 2: Test simple SELECT (no ILIKE, no filters)
-- ============================================================================
-- Expected: Should return 10 rows
-- If this fails: Table has serious corruption
SELECT id, name, is_public, created_at
FROM foods
LIMIT 10;

-- ============================================================================
-- QUERY 3: Test SELECT with is_public filter (no ILIKE)
-- ============================================================================
-- Expected: Should return 10 public foods
-- If this fails: Problem with is_public column or index
SELECT id, name, is_public, usage_count, verified
FROM foods
WHERE is_public = true
ORDER BY usage_count DESC, verified DESC
LIMIT 10;

-- ============================================================================
-- QUERY 4: Test ILIKE on SMALL dataset (LIMIT 1)
-- ============================================================================
-- Expected: Should return 1 row matching 'banana'
-- If this fails: ILIKE itself is broken OR specific row causes crash
SELECT id, name, is_public
FROM foods
WHERE is_public = true
  AND name ILIKE '%banana%'
LIMIT 1;

-- ============================================================================
-- QUERY 5: Test ILIKE with broader pattern (LIMIT 5)
-- ============================================================================
-- Expected: Should return up to 5 rows
-- If QUERY 4 worked but this fails: Multiple matching rows cause cumulative issue
SELECT id, name, brand_name, is_public
FROM foods
WHERE is_public = true
  AND name ILIKE '%a%'
LIMIT 5;

-- ============================================================================
-- QUERY 6: Check for NULL/empty names
-- ============================================================================
-- Expected: 0 rows (all foods should have names)
-- If > 0: NULL names might cause ILIKE to crash
SELECT COUNT(*) as null_or_empty_names
FROM foods
WHERE name IS NULL OR name = '' OR TRIM(name) = '';

-- ============================================================================
-- QUERY 7: Check for special characters / encoding issues
-- ============================================================================
-- Expected: Small number or 0
-- If large number: Encoding issues might crash PostgREST
SELECT
  id,
  name,
  LENGTH(name) as name_length,
  OCTET_LENGTH(name) as name_bytes,
  name ~ '[^\x20-\x7E\x80-\xFF]' as has_special_chars
FROM foods
WHERE name ~ '[^\x20-\x7E\x80-\xFF]'
LIMIT 20;

-- ============================================================================
-- QUERY 8: Check index health
-- ============================================================================
-- Expected: List of indexes on foods table
-- Look for: Missing indexes or corrupted index definitions
SELECT
  schemaname,
  tablename,
  indexname,
  indexdef
FROM pg_indexes
WHERE tablename = 'foods'
ORDER BY indexname;

-- ============================================================================
-- QUERY 9: Check for VERY long text in columns
-- ============================================================================
-- Expected: All reasonable lengths
-- If huge lengths: Might cause PostgREST memory issues
SELECT
  id,
  name,
  LENGTH(name) as name_length,
  LENGTH(COALESCE(brand_name, '')) as brand_length,
  LENGTH(COALESCE(notes, '')) as notes_length
FROM foods
WHERE
  LENGTH(name) > 200
  OR LENGTH(COALESCE(brand_name, '')) > 200
  OR LENGTH(COALESCE(notes, '')) > 1000
LIMIT 20;

-- ============================================================================
-- QUERY 10: Check food_servings join integrity
-- ============================================================================
-- Expected: Foods with serving counts
-- If this fails but previous queries work: JOIN is the problem
SELECT
  f.id,
  f.name,
  COUNT(fs.id) as servings_count
FROM foods f
LEFT JOIN food_servings fs ON f.id = fs.food_id
WHERE f.is_public = true
GROUP BY f.id, f.name
ORDER BY servings_count DESC
LIMIT 10;

-- ============================================================================
-- QUERY 11: Test exact PostgREST query pattern
-- ============================================================================
-- Expected: Should return foods with servings
-- If this works in SQL Editor but fails via PostgREST: PostgREST-specific issue
SELECT
  f.*,
  json_agg(
    json_build_object(
      'id', fs.id,
      'food_id', fs.food_id,
      'serving_size', fs.serving_size,
      'serving_unit', fs.serving_unit,
      'grams_per_serving', fs.grams_per_serving,
      'is_default', fs.is_default
    )
  ) FILTER (WHERE fs.id IS NOT NULL) as food_servings
FROM foods f
LEFT JOIN food_servings fs ON f.id = fs.food_id
WHERE f.is_public = true
  AND f.name ILIKE '%banana%'
GROUP BY f.id
ORDER BY f.usage_count DESC, f.verified DESC
LIMIT 5;

-- ============================================================================
-- QUERY 12: Check for JSONB corruption in recipe_items
-- ============================================================================
-- Expected: All valid JSONB or NULL
-- If errors: JSONB corruption causes PostgREST serialization failure
SELECT
  id,
  name,
  recipe_items,
  CASE
    WHEN recipe_items IS NULL THEN 'NULL'
    WHEN jsonb_typeof(recipe_items) = 'array' THEN 'valid_array'
    ELSE 'invalid_type'
  END as recipe_items_status
FROM foods
WHERE recipe_items IS NOT NULL
LIMIT 20;

-- ============================================================================
-- QUERY 13: Check table statistics (freshness)
-- ============================================================================
-- Expected: Recent stats
-- If stale: Run ANALYZE foods; to refresh
SELECT
  schemaname,
  tablename,
  last_vacuum,
  last_autovacuum,
  last_analyze,
  last_autoanalyze,
  n_live_tup as live_rows,
  n_dead_tup as dead_rows
FROM pg_stat_user_tables
WHERE tablename = 'foods';

-- ============================================================================
-- INTERPRETATION GUIDE
-- ============================================================================
--
-- IF Query 1-3 work BUT Query 4 fails:
--   → ILIKE pattern matching is broken (possibly index corruption)
--   → FIX: Rebuild indexes OR use full-text search instead
--
-- IF Query 4 works BUT Query 5 fails:
--   → Multiple result rows cause cumulative issue (memory/serialization)
--   → FIX: Add stricter LIMIT, paginate results
--
-- IF Query 1-10 work BUT Query 11 fails:
--   → JSON aggregation causes crash
--   → FIX: Use RPC function with manual JSON building
--
-- IF Query 11 works in SQL Editor BUT fails via PostgREST:
--   → PostgREST-specific bug or configuration issue
--   → FIX: Bypass PostgREST with RPC function
--
-- IF Query 13 shows stale statistics:
--   → Run: ANALYZE foods;
--   → Run: VACUUM ANALYZE foods;
--
-- ============================================================================
-- NEXT STEPS
-- ============================================================================
-- 1. Run queries 1-13 in order
-- 2. Note which query first fails (if any)
-- 3. Check Supabase logs for specific error messages
-- 4. Apply appropriate fix based on interpretation guide
-- 5. Deploy workaround function (see migration 041)
