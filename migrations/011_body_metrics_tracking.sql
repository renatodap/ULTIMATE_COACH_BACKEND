-- ============================================================================
-- ULTIMATE COACH - Body Metrics Tracking Migration
-- ============================================================================
-- Version: 4.0.0
-- Created: 2025-10-13
-- Description: Add body metrics tracking for weight and body composition history
--
-- PURPOSE:
-- - Track weight changes over time (historical data)
-- - Enable weight trend analysis and progress tracking
-- - Support body composition metrics (body fat %, future measurements)
-- - Provide data for dashboard weight progress visualization
--
-- NOTE: profiles.current_weight_kg still exists (single source of truth from onboarding)
--       This table tracks the HISTORY of weight measurements for trend analysis
-- ============================================================================

-- Create body_metrics table for tracking weight/body composition over time
CREATE TABLE IF NOT EXISTS body_metrics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Measurement Data
  recorded_at TIMESTAMPTZ NOT NULL,  -- When the measurement was taken
  weight_kg NUMERIC(5, 2) NOT NULL CHECK (weight_kg >= 30 AND weight_kg <= 300),

  -- Optional Body Composition (future feature)
  body_fat_percentage NUMERIC(4, 1) CHECK (body_fat_percentage >= 3 AND body_fat_percentage <= 60),

  -- User Notes
  notes TEXT,

  -- Metadata
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Primary query pattern: Get user's weight history sorted by date
CREATE INDEX IF NOT EXISTS idx_body_metrics_user_date
  ON body_metrics(user_id, recorded_at DESC);

-- Query pattern: Get latest weight for a user
CREATE INDEX IF NOT EXISTS idx_body_metrics_user_latest
  ON body_metrics(user_id, created_at DESC);

-- Prevent duplicate entries for same user at same time (within 1 minute)
CREATE UNIQUE INDEX IF NOT EXISTS idx_body_metrics_user_time_unique
  ON body_metrics(user_id, DATE_TRUNC('minute', recorded_at AT TIME ZONE 'UTC'));

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS on body_metrics table
ALTER TABLE body_metrics ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own body metrics
CREATE POLICY body_metrics_select_own
  ON body_metrics
  FOR SELECT
  USING (auth.uid() = user_id);

-- Policy: Users can only insert their own body metrics
CREATE POLICY body_metrics_insert_own
  ON body_metrics
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Policy: Users can only update their own body metrics
CREATE POLICY body_metrics_update_own
  ON body_metrics
  FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Policy: Users can only delete their own body metrics
CREATE POLICY body_metrics_delete_own
  ON body_metrics
  FOR DELETE
  USING (auth.uid() = user_id);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Trigger: Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_body_metrics_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER body_metrics_updated_at
  BEFORE UPDATE ON body_metrics
  FOR EACH ROW
  EXECUTE FUNCTION update_body_metrics_updated_at();

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE body_metrics IS 'Historical tracking of user weight and body composition measurements';
COMMENT ON COLUMN body_metrics.user_id IS 'User who recorded this measurement (FK to auth.users)';
COMMENT ON COLUMN body_metrics.recorded_at IS 'Timestamp when measurement was taken (user-specified, can be backdated)';
COMMENT ON COLUMN body_metrics.weight_kg IS 'Weight in kilograms (30-300 kg). Always stored metric.';
COMMENT ON COLUMN body_metrics.body_fat_percentage IS 'Optional body fat percentage (3-60%). For future body composition tracking.';
COMMENT ON COLUMN body_metrics.notes IS 'Optional user notes about this measurement (e.g., "morning weight", "after workout")';
COMMENT ON COLUMN body_metrics.created_at IS 'When this record was created in database';
COMMENT ON COLUMN body_metrics.updated_at IS 'When this record was last updated';

-- ============================================================================
-- MIGRATION NOTES
-- ============================================================================
--
-- RUNNING THIS MIGRATION:
-- 1. New table created with RLS enabled
-- 2. Existing users start with empty weight history
-- 3. They can optionally log their current weight from profiles.current_weight_kg
-- 4. Dashboard will show weight progress when they start logging
--
-- DATA SEEDING (optional):
-- For users who want to start tracking, seed initial weight from profile:
--
-- INSERT INTO body_metrics (user_id, recorded_at, weight_kg, notes)
-- SELECT
--   id,
--   NOW(),
--   current_weight_kg,
--   'Initial weight from profile'
-- FROM profiles
-- WHERE current_weight_kg IS NOT NULL
-- ON CONFLICT DO NOTHING;
--
-- ROLLBACK (if needed):
-- DROP TABLE IF EXISTS body_metrics CASCADE;
-- DROP FUNCTION IF EXISTS update_body_metrics_updated_at() CASCADE;
--
-- VERIFICATION QUERIES:
-- - Check table exists: \dt body_metrics
-- - Check RLS enabled: SELECT tablename, rowsecurity FROM pg_tables WHERE tablename = 'body_metrics';
-- - Check policies: SELECT policyname, cmd FROM pg_policies WHERE tablename = 'body_metrics';
-- - Check indexes: SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'body_metrics';
-- - Test insert: INSERT INTO body_metrics (user_id, recorded_at, weight_kg) VALUES (auth.uid(), NOW(), 75.0);
--
-- ============================================================================
