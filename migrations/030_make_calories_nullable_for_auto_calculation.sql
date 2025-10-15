-- Migration 030: Make calories_burned nullable for auto-calculation
-- Date: 2025-10-14
-- Description: Allow calories_burned to be NULL so backend can auto-calculate using METs database

-- ============================================
-- STEP 1: Remove NOT NULL constraint from calories_burned
-- ============================================

-- Drop the NOT NULL constraint
-- Note: PostgreSQL doesn't have a direct "DROP CONSTRAINT NOT NULL" for columns
-- We use ALTER COLUMN to change the constraint
ALTER TABLE activities
  ALTER COLUMN calories_burned DROP NOT NULL;

-- Add comment explaining the change
COMMENT ON COLUMN activities.calories_burned IS
  'Total calories burned during activity. Can be NULL on creation - will be calculated automatically using METs × weight × duration if not provided by user.';

-- ============================================
-- STEP 2: Verify intensity_mets is already nullable
-- ============================================

-- intensity_mets should already be nullable from migration 012
-- This is just a verification comment
COMMENT ON COLUMN activities.intensity_mets IS
  'Metabolic Equivalent of Task (1.0 = resting, 8.0 = running). Can be NULL on creation - will be looked up automatically from activity name if not provided by user.';

-- ============================================
-- VERIFICATION
-- ============================================

DO $$
DECLARE
  calories_nullable BOOLEAN;
  mets_nullable BOOLEAN;
BEGIN
  -- Check if calories_burned is nullable
  SELECT is_nullable = 'YES' INTO calories_nullable
  FROM information_schema.columns
  WHERE table_name = 'activities'
    AND column_name = 'calories_burned';

  -- Check if intensity_mets is nullable
  SELECT is_nullable = 'YES' INTO mets_nullable
  FROM information_schema.columns
  WHERE table_name = 'activities'
    AND column_name = 'intensity_mets';

  IF NOT calories_nullable THEN
    RAISE EXCEPTION 'Migration failed: calories_burned is still NOT NULL';
  END IF;

  IF NOT mets_nullable THEN
    RAISE EXCEPTION 'Migration failed: intensity_mets is still NOT NULL';
  END IF;

  RAISE NOTICE '===========================================';
  RAISE NOTICE 'Migration 030 completed successfully! ✓';
  RAISE NOTICE '===========================================';
  RAISE NOTICE 'Changes:';
  RAISE NOTICE '  - calories_burned: Now nullable ✓';
  RAISE NOTICE '  - intensity_mets: Already nullable ✓';
  RAISE NOTICE '';
  RAISE NOTICE 'System behavior:';
  RAISE NOTICE '  - If calories_burned is NULL: Calculate automatically using METs formula';
  RAISE NOTICE '  - If intensity_mets is NULL: Look up automatically from activity name';
  RAISE NOTICE '  - Users only need to provide: activity name, category, duration';
  RAISE NOTICE '===========================================';
END $$;
