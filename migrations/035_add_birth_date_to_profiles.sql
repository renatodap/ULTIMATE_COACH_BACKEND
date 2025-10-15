-- ============================================================================
-- Migration 035: Add birth_date to profiles (nullable)
-- Date: 2025-10-15
-- Description:
--   Store user birth date rather than static age. Column is nullable for
--   backwards compatibility. Age can be derived at runtime.
-- ============================================================================

ALTER TABLE IF EXISTS profiles
  ADD COLUMN IF NOT EXISTS birth_date DATE;

COMMENT ON COLUMN profiles.birth_date IS 'User birth date (used to derive age)';

