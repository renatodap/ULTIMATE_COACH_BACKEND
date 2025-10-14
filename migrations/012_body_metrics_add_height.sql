-- ============================================================================
-- ULTIMATE COACH - Body Metrics: Add height_cm
-- ============================================================================
-- Version: 4.0.1
-- Created: 2025-10-14
-- Description: Add height_cm to body_metrics for height tracking alongside weight
--
-- PURPOSE:
-- - Allow logging height changes over time (in centimeters, metric storage)
-- - Keep consistent with onboarding and profile units strategy
-- ============================================================================

-- Add height_cm column (optional)
ALTER TABLE body_metrics
  ADD COLUMN IF NOT EXISTS height_cm NUMERIC(5, 2) CHECK (height_cm >= 100 AND height_cm <= 300);

-- Comment for documentation
COMMENT ON COLUMN body_metrics.height_cm IS 'Height in centimeters (100-300 cm). Always stored metric.';

-- Optional backfill: seed an initial height entry from profiles for users with known height
-- NOTE: This only seeds a metric log if there is already a body_metrics record at the current timestamp.
-- To avoid creating duplicate body_metrics rows, this example only updates rows where height_cm is NULL.
-- If you prefer to INSERT a new metric row when none exists, do so in application logic.
--
-- UPDATE body_metrics bm
-- SET height_cm = p.height_cm
-- FROM profiles p
-- WHERE bm.user_id = p.id AND bm.height_cm IS NULL AND p.height_cm IS NOT NULL;

-- Verification:
-- \d+ body_metrics  -- confirm height_cm column exists with constraint
-- SELECT COUNT(*) FROM body_metrics WHERE height_cm IS NOT NULL;

