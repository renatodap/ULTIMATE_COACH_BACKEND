-- ============================================================================
-- FIX: unique_default_per_food constraint
-- ============================================================================
-- The UNIQUE (food_id, is_default) constraint is incorrect.
-- It prevents multiple non-default servings per food.
--
-- PROBLEM:
-- - UNIQUE (food_id, is_default) means:
--   - Only ONE row where (food_id=X, is_default=TRUE) ✅ CORRECT
--   - Only ONE row where (food_id=X, is_default=FALSE) ❌ WRONG!
--
-- SOLUTION:
-- - Drop the constraint
-- - Add partial unique index that only applies when is_default=TRUE
-- ============================================================================

-- Drop the incorrect constraint
ALTER TABLE food_servings DROP CONSTRAINT IF EXISTS unique_default_per_food;

-- Add correct partial unique index
-- This ensures only ONE default per food, but allows many non-defaults
CREATE UNIQUE INDEX IF NOT EXISTS idx_food_servings_unique_default
  ON food_servings (food_id)
  WHERE is_default = TRUE;

-- Verify: This should now work:
-- INSERT INTO food_servings (food_id, ..., is_default) VALUES (X, ..., TRUE);  -- Only one allowed ✅
-- INSERT INTO food_servings (food_id, ..., is_default) VALUES (X, ..., FALSE); -- Many allowed ✅
-- INSERT INTO food_servings (food_id, ..., is_default) VALUES (X, ..., FALSE); -- Many allowed ✅
-- INSERT INTO food_servings (food_id, ..., is_default) VALUES (X, ..., FALSE); -- Many allowed ✅
