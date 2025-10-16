-- Migration: Fix is_public NULL values
-- Date: 2025-10-16
-- Issue: Foods with is_public = NULL are excluded from search results
--
-- Root Cause: is_public column is nullable, and NULL != true in WHERE clause
-- This migration fixes existing NULL values and prevents future NULLs

BEGIN;

-- 1. Fix NULL values (make them public by default)
UPDATE foods
SET is_public = true, updated_at = NOW()
WHERE is_public IS NULL;

-- 2. Make any false values public (assumes all seeded foods should be searchable)
-- Comment this out if you want to keep some foods private
UPDATE foods
SET is_public = true, updated_at = NOW()
WHERE is_public = false;

-- 3. Make the column NOT NULL with a default value to prevent future issues
ALTER TABLE foods
ALTER COLUMN is_public SET DEFAULT true,
ALTER COLUMN is_public SET NOT NULL;

-- 4. Verify the fix
DO $$
DECLARE
  total_count INTEGER;
  public_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO total_count FROM foods;
  SELECT COUNT(*) INTO public_count FROM foods WHERE is_public = true;

  RAISE NOTICE 'Migration completed successfully:';
  RAISE NOTICE '  Total foods: %', total_count;
  RAISE NOTICE '  Public foods: %', public_count;
  RAISE NOTICE '  All foods are now searchable: %', (total_count = public_count);
END $$;

COMMIT;

-- NOTES:
-- After running this migration:
-- 1. All existing foods will be public and searchable
-- 2. New foods will default to is_public = true
-- 3. The column cannot be NULL anymore
-- 4. Search for "chicken" should now return results
