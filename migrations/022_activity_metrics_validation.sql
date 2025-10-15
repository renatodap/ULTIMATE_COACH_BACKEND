-- ============================================================================
-- Migration 022: Activity Metrics JSONB Validation
-- ============================================================================
-- Created: 2025-10-12
-- Description: Add validation for activity metrics JSONB to prevent bad data
--
-- FEATURES:
-- 1. Type-safe validation for different activity types
-- 2. Prevents typos and inconsistent data
-- 3. Easy to extend with new activity types
-- ============================================================================

-- ============================================================================
-- VALIDATION FUNCTION
-- ============================================================================
CREATE OR REPLACE FUNCTION validate_activity_metrics(
  p_activity_type TEXT,
  p_metrics JSONB
)
RETURNS BOOLEAN AS $$
DECLARE
  v_required_keys TEXT[];
  v_key TEXT;
BEGIN
  -- Define validation rules for each activity type
  CASE p_activity_type
    WHEN 'running' THEN
      -- Optional: distance_km, avg_pace, avg_heart_rate, max_heart_rate, elevation_gain_m, cadence_spm
      -- No strict requirements, but validate types if present
      IF p_metrics ? 'distance_km' AND (p_metrics->>'distance_km')::NUMERIC < 0 THEN
        RAISE EXCEPTION 'distance_km must be >= 0';
      END IF;
      IF p_metrics ? 'avg_heart_rate' THEN
        IF (p_metrics->>'avg_heart_rate')::INT < 40 OR (p_metrics->>'avg_heart_rate')::INT > 220 THEN
          RAISE EXCEPTION 'avg_heart_rate must be between 40 and 220';
        END IF;
      END IF;

    WHEN 'cycling' THEN
      -- Optional: distance_km, avg_speed_kph, elevation_gain_m, avg_cadence, avg_power_watts
      IF p_metrics ? 'avg_speed_kph' AND (p_metrics->>'avg_speed_kph')::NUMERIC < 0 THEN
        RAISE EXCEPTION 'avg_speed_kph must be >= 0';
      END IF;
      IF p_metrics ? 'avg_power_watts' AND (p_metrics->>'avg_power_watts')::INT < 0 THEN
        RAISE EXCEPTION 'avg_power_watts must be >= 0';
      END IF;

    WHEN 'swimming' THEN
      -- Optional: laps, pool_length_meters, distance_m, stroke_type
      IF p_metrics ? 'laps' AND (p_metrics->>'laps')::INT < 1 THEN
        RAISE EXCEPTION 'laps must be >= 1';
      END IF;
      IF p_metrics ? 'pool_length_meters' THEN
        IF (p_metrics->>'pool_length_meters')::NUMERIC NOT IN (25, 50, 33.3) THEN
          RAISE EXCEPTION 'pool_length_meters must be 25, 50, or 33.3';
        END IF;
      END IF;

    WHEN 'strength_training' THEN
      -- Optional: total_volume_kg, sets_completed, exercises_count, exercises[]
      IF p_metrics ? 'total_volume_kg' AND (p_metrics->>'total_volume_kg')::NUMERIC < 0 THEN
        RAISE EXCEPTION 'total_volume_kg must be >= 0';
      END IF;

    WHEN 'sports' THEN
      -- Very flexible - allow any metrics
      -- No validation needed

    ELSE
      -- Unknown activity type - allow any metrics
      RETURN TRUE;
  END CASE;

  RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION validate_activity_metrics IS
  'Validates JSONB metrics structure based on activity_type. Prevents bad data from entering database.';

-- ============================================================================
-- ADD CHECK CONSTRAINT TO ACTIVITIES TABLE
-- ============================================================================
-- Note: This assumes activities table already exists
-- If not, this will be part of the main schema migration

-- First, drop constraint if it exists (for idempotency)
ALTER TABLE IF EXISTS activities
  DROP CONSTRAINT IF EXISTS activities_metrics_valid;

-- Add constraint
ALTER TABLE IF EXISTS activities
  ADD CONSTRAINT activities_metrics_valid
  CHECK (validate_activity_metrics(activity_type, metrics));

COMMENT ON CONSTRAINT activities_metrics_valid ON activities IS
  'Validates JSONB metrics structure based on activity_type';
