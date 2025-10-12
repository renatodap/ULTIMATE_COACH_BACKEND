-- ============================================================================
-- ULTIMATE COACH - Onboarding Data Migration
-- ============================================================================
-- Version: 2.0.1
-- Created: 2025-10-12
-- Description: Add comprehensive onboarding fields to profiles table
--
-- PURPOSE:
-- - Collect all data needed for macro calculations (BMR, TDEE)
-- - Enable AI coach personalization
-- - Support metric/imperial unit systems
-- - Track dietary preferences and restrictions
-- ============================================================================

-- Add onboarding fields to profiles table
ALTER TABLE profiles
  -- Physical Stats (ALWAYS STORED IN METRIC - canonical)
  ADD COLUMN IF NOT EXISTS age INTEGER CHECK (age >= 13 AND age <= 120),
  ADD COLUMN IF NOT EXISTS biological_sex TEXT CHECK (biological_sex IN ('male', 'female')),
  ADD COLUMN IF NOT EXISTS height_cm NUMERIC(5, 2) CHECK (height_cm >= 100 AND height_cm <= 300),
  ADD COLUMN IF NOT EXISTS current_weight_kg NUMERIC(5, 2) CHECK (current_weight_kg >= 30 AND current_weight_kg <= 300),
  ADD COLUMN IF NOT EXISTS goal_weight_kg NUMERIC(5, 2) CHECK (goal_weight_kg >= 30 AND current_weight_kg <= 300),

  -- Activity & Lifestyle
  ADD COLUMN IF NOT EXISTS activity_level TEXT CHECK (activity_level IN ('sedentary', 'lightly_active', 'moderately_active', 'very_active', 'extremely_active')),
  ADD COLUMN IF NOT EXISTS workout_frequency INTEGER CHECK (workout_frequency >= 0 AND workout_frequency <= 7),
  ADD COLUMN IF NOT EXISTS sleep_hours NUMERIC(3, 1) CHECK (sleep_hours >= 4 AND sleep_hours <= 12),
  ADD COLUMN IF NOT EXISTS stress_level TEXT CHECK (stress_level IN ('low', 'medium', 'high')) DEFAULT 'medium',

  -- Dietary Profile
  ADD COLUMN IF NOT EXISTS dietary_preference TEXT CHECK (dietary_preference IN ('none', 'vegetarian', 'vegan', 'pescatarian', 'keto', 'paleo')) DEFAULT 'none',
  ADD COLUMN IF NOT EXISTS food_allergies TEXT[] DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS foods_to_avoid TEXT[] DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS meals_per_day INTEGER CHECK (meals_per_day >= 1 AND meals_per_day <= 8) DEFAULT 3,
  ADD COLUMN IF NOT EXISTS cooks_regularly BOOLEAN DEFAULT TRUE,

  -- Macro Calculation Metadata
  ADD COLUMN IF NOT EXISTS macros_last_calculated_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS macros_calculation_reason TEXT;

-- Add index for onboarding status (helps middleware queries)
CREATE INDEX IF NOT EXISTS idx_profiles_onboarding
  ON profiles (onboarding_completed)
  WHERE onboarding_completed = FALSE;

-- Add index for user queries (common pattern)
CREATE INDEX IF NOT EXISTS idx_profiles_id_onboarding
  ON profiles (id, onboarding_completed);

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON COLUMN profiles.age IS 'User age (13-120). Used for BMR calculation.';
COMMENT ON COLUMN profiles.biological_sex IS 'Male or female. Used for BMR calculation (different formulas).';
COMMENT ON COLUMN profiles.height_cm IS 'Height in centimeters (canonical). Always stored metric, displayed per user preference.';
COMMENT ON COLUMN profiles.current_weight_kg IS 'Current weight in kilograms (canonical). Always stored metric, displayed per user preference.';
COMMENT ON COLUMN profiles.goal_weight_kg IS 'Goal weight in kilograms. Determines calorie deficit/surplus.';
COMMENT ON COLUMN profiles.activity_level IS 'Activity multiplier for TDEE: sedentary (1.2), lightly_active (1.375), moderately_active (1.55), very_active (1.725), extremely_active (1.9)';
COMMENT ON COLUMN profiles.workout_frequency IS 'Workouts per week (0-7). For AI coach context.';
COMMENT ON COLUMN profiles.sleep_hours IS 'Average sleep per night (4-12). Affects recovery recommendations.';
COMMENT ON COLUMN profiles.stress_level IS 'Low/Medium/High. Affects cortisol considerations in recommendations.';
COMMENT ON COLUMN profiles.dietary_preference IS 'Dietary restriction type. Used for meal/food filtering.';
COMMENT ON COLUMN profiles.food_allergies IS 'Array of allergen strings (e.g., ["dairy", "nuts"]). Critical for safety.';
COMMENT ON COLUMN profiles.foods_to_avoid IS 'Array of disliked foods (e.g., ["broccoli", "mushrooms"]). For meal recommendations.';
COMMENT ON COLUMN profiles.meals_per_day IS 'Preferred eating frequency (1-8). For meal planning.';
COMMENT ON COLUMN profiles.cooks_regularly IS 'Whether user cooks. Affects meal complexity recommendations.';
COMMENT ON COLUMN profiles.macros_last_calculated_at IS 'Timestamp of last macro calculation. For showing "last updated X days ago".';
COMMENT ON COLUMN profiles.macros_calculation_reason IS 'Why macros were recalculated: "initial_onboarding", "weight_update", "activity_update", etc.';

-- ============================================================================
-- MIGRATION NOTES
-- ============================================================================
--
-- RUNNING THIS MIGRATION:
-- 1. Existing users will have NULL for new fields
-- 2. They will be redirected to onboarding on next login (middleware check)
-- 3. New users will complete onboarding before accessing app
--
-- ROLLBACK (if needed):
-- ALTER TABLE profiles
--   DROP COLUMN IF EXISTS age,
--   DROP COLUMN IF EXISTS biological_sex,
--   ... (drop all added columns)
--
-- VERIFICATION QUERIES:
-- - Check column exists: SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'profiles';
-- - Check constraints: SELECT conname, contype, consrc FROM pg_constraint WHERE conrelid = 'profiles'::regclass;
-- - Check indexes: SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'profiles';
--
-- ============================================================================
