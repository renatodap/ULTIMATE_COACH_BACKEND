-- Migration: Add Activity Tracking System
-- Date: 2025-10-12
-- Description: Adds missing columns to activities table and creates supporting tables for
--              template system, wearable integration, and GPS tracking

-- ============================================
-- STEP 1: Update activities table with missing columns
-- ============================================

-- Add core columns
ALTER TABLE activities
  ADD COLUMN IF NOT EXISTS end_time timestamptz,
  ADD COLUMN IF NOT EXISTS deleted_at timestamptz;

-- Add template system columns
ALTER TABLE activities
  ADD COLUMN IF NOT EXISTS template_id uuid,
  ADD COLUMN IF NOT EXISTS template_match_score numeric(5,2) CHECK (template_match_score >= 0 AND template_match_score <= 100),
  ADD COLUMN IF NOT EXISTS template_applied_at timestamptz;

-- Add wearable integration columns (nullable - feature flagged)
ALTER TABLE activities
  ADD COLUMN IF NOT EXISTS wearable_activity_id text,
  ADD COLUMN IF NOT EXISTS wearable_url text,
  ADD COLUMN IF NOT EXISTS device_name text,
  ADD COLUMN IF NOT EXISTS sync_timestamp timestamptz,
  ADD COLUMN IF NOT EXISTS raw_wearable_data jsonb;

-- Update source enum to include new values
ALTER TABLE activities DROP CONSTRAINT IF EXISTS activities_source_check;
ALTER TABLE activities ADD CONSTRAINT activities_source_check
  CHECK (source IN ('manual', 'ai_text', 'ai_voice', 'garmin', 'strava', 'apple_health', 'merged'));

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_activities_deleted ON activities(user_id, start_time DESC) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_activities_template ON activities(template_id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_activities_source ON activities(user_id, source) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_activities_wearable ON activities(wearable_activity_id) WHERE wearable_activity_id IS NOT NULL;

-- Add comments for documentation
COMMENT ON COLUMN activities.end_time IS 'Activity end time (optional - duration can be manual or calculated from start_time + duration_minutes)';
COMMENT ON COLUMN activities.deleted_at IS 'Soft delete timestamp (NULL = active, timestamptz = deleted)';
COMMENT ON COLUMN activities.template_id IS 'Reference to activity template if this activity was matched or user-applied a template';
COMMENT ON COLUMN activities.template_match_score IS 'Auto-match confidence score (0-100) if template was automatically applied';
COMMENT ON COLUMN activities.template_applied_at IS 'Timestamp when template was applied to this activity';
COMMENT ON COLUMN activities.wearable_activity_id IS 'Provider-specific activity ID (e.g., Garmin activity ID) for deduplication';
COMMENT ON COLUMN activities.wearable_url IS 'Deep link to activity on provider platform (Garmin Connect, Strava, etc.)';
COMMENT ON COLUMN activities.device_name IS 'Device that recorded the activity (e.g., "Garmin Forerunner 945")';
COMMENT ON COLUMN activities.sync_timestamp IS 'When this activity was synced from wearable provider';
COMMENT ON COLUMN activities.raw_wearable_data IS 'Full JSON payload from wearable provider for debugging/reprocessing';

-- ============================================
-- STEP 2: Create activity_templates table
-- ============================================

CREATE TABLE IF NOT EXISTS activity_templates (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Basic info
  template_name text NOT NULL,
  activity_type text NOT NULL,
  description text,
  icon text DEFAULT '🏃',

  -- Expected ranges for auto-matching
  expected_distance_m numeric CHECK (expected_distance_m > 0),
  distance_tolerance_percent integer DEFAULT 10 CHECK (distance_tolerance_percent >= 0 AND distance_tolerance_percent <= 100),
  expected_duration_minutes integer CHECK (expected_duration_minutes > 0),
  duration_tolerance_percent integer DEFAULT 15 CHECK (duration_tolerance_percent >= 0 AND duration_tolerance_percent <= 100),

  -- Pre-filled data for manual logs
  default_exercises jsonb DEFAULT '[]',
  default_metrics jsonb DEFAULT '{}',
  default_notes text,

  -- Auto-matching configuration
  auto_match_enabled boolean DEFAULT true,
  min_match_score integer DEFAULT 70 CHECK (min_match_score >= 0 AND min_match_score <= 100),
  require_gps_match boolean DEFAULT false,

  -- Time-based matching
  typical_start_time time,
  time_window_hours integer DEFAULT 2 CHECK (time_window_hours >= 0 AND time_window_hours <= 12),
  preferred_days integer[] CHECK (
    preferred_days IS NULL OR
    (array_length(preferred_days, 1) > 0 AND
     preferred_days <@ ARRAY[1,2,3,4,5,6,7])
  ),

  -- GPS route matching (feature flagged)
  gps_route_hash text,
  gps_track_id uuid,

  -- Workout goals
  target_zone text,
  goal_notes text,

  -- Usage statistics
  use_count integer DEFAULT 0 CHECK (use_count >= 0),
  last_used_at timestamptz,

  -- Metadata
  is_active boolean DEFAULT true,
  created_from_activity_id uuid REFERENCES activities(id) ON DELETE SET NULL,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),

  -- Constraints
  CONSTRAINT activity_templates_user_name_unique UNIQUE (user_id, template_name)
);

-- Indexes for templates
CREATE INDEX idx_templates_user_active ON activity_templates(user_id, is_active);
CREATE INDEX idx_templates_type ON activity_templates(user_id, activity_type) WHERE is_active = true;
CREATE INDEX idx_templates_gps ON activity_templates(gps_route_hash) WHERE gps_route_hash IS NOT NULL;
CREATE INDEX idx_templates_usage ON activity_templates(user_id, use_count DESC, last_used_at DESC) WHERE is_active = true;

-- Add foreign key constraint to activities.template_id (now that table exists)
ALTER TABLE activities
  ADD CONSTRAINT fk_activities_template
  FOREIGN KEY (template_id) REFERENCES activity_templates(id) ON DELETE SET NULL;

-- Comments
COMMENT ON TABLE activity_templates IS 'User-defined templates for recurring workouts with auto-matching capability';
COMMENT ON COLUMN activity_templates.gps_route_hash IS 'Hash of GPS route for matching similar routes (requires GPS feature flag)';
COMMENT ON COLUMN activity_templates.preferred_days IS 'Array of day numbers (1=Monday, 7=Sunday) when this activity typically happens';

-- ============================================
-- STEP 3: Create GPS tracks table (feature flagged)
-- ============================================

CREATE TABLE IF NOT EXISTS gps_tracks (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  activity_id uuid REFERENCES activities(id) ON DELETE CASCADE,
  template_id uuid REFERENCES activity_templates(id) ON DELETE CASCADE,

  -- Track data (array of {lat, lng, elevation, timestamp, hr})
  track_data jsonb NOT NULL,

  -- Computed metrics
  total_distance_m numeric CHECK (total_distance_m >= 0),
  elevation_gain_m numeric CHECK (elevation_gain_m >= 0),
  elevation_loss_m numeric CHECK (elevation_loss_m >= 0),

  -- Route identification for matching
  route_hash text NOT NULL,
  route_signature text, -- Simplified version for faster matching

  -- Privacy controls
  start_location_hidden boolean DEFAULT true,
  end_location_hidden boolean DEFAULT true,

  created_at timestamptz DEFAULT now(),

  -- Constraint: must belong to either activity or template
  CONSTRAINT gps_tracks_owner_check CHECK (
    (activity_id IS NOT NULL AND template_id IS NULL) OR
    (activity_id IS NULL AND template_id IS NOT NULL)
  )
);

-- Indexes for GPS tracks
CREATE INDEX idx_gps_route_hash ON gps_tracks(route_hash);
CREATE INDEX idx_gps_activity ON gps_tracks(activity_id) WHERE activity_id IS NOT NULL;
CREATE INDEX idx_gps_template ON gps_tracks(template_id) WHERE template_id IS NOT NULL;

-- Add foreign key to templates
ALTER TABLE activity_templates
  ADD CONSTRAINT fk_templates_gps_track
  FOREIGN KEY (gps_track_id) REFERENCES gps_tracks(id) ON DELETE SET NULL;

COMMENT ON TABLE gps_tracks IS 'GPS track data for activities and templates (requires GPS_TRACKING feature flag)';
COMMENT ON COLUMN gps_tracks.route_hash IS 'Full hash of route for exact matching';
COMMENT ON COLUMN gps_tracks.route_signature IS 'Simplified signature for fuzzy matching (e.g., major waypoints only)';

-- ============================================
-- STEP 4: Create template match history table
-- ============================================

CREATE TABLE IF NOT EXISTS activity_template_matches (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  activity_id uuid NOT NULL REFERENCES activities(id) ON DELETE CASCADE,
  template_id uuid NOT NULL REFERENCES activity_templates(id) ON DELETE CASCADE,
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Match details
  match_score numeric(5,2) NOT NULL CHECK (match_score >= 0 AND match_score <= 100),
  match_method text NOT NULL CHECK (match_method IN (
    'auto_high_confidence',  -- 90%+ confidence, auto-applied
    'auto_suggested',        -- 70-89% confidence, user clicked "Apply"
    'manual_selected',       -- User manually chose template from list
    'user_rejected'          -- User explicitly rejected this suggestion
  )),
  match_reasons jsonb NOT NULL DEFAULT '[]', -- Array of reason strings

  -- User action tracking
  user_action text CHECK (user_action IN ('applied', 'rejected', 'ignored')),
  action_timestamp timestamptz,

  created_at timestamptz DEFAULT now()
);

-- Indexes for match history
CREATE INDEX idx_template_matches_activity ON activity_template_matches(activity_id);
CREATE INDEX idx_template_matches_template ON activity_template_matches(template_id);
CREATE INDEX idx_template_matches_user ON activity_template_matches(user_id, created_at DESC);

COMMENT ON TABLE activity_template_matches IS 'History of template matching attempts for learning and analytics';
COMMENT ON COLUMN activity_template_matches.match_reasons IS 'JSON array of reasons why template matched (e.g., ["Same activity type", "Distance match (±5%)", "Same time of day"])';

-- ============================================
-- STEP 5: Create duplicate detection table
-- ============================================

CREATE TABLE IF NOT EXISTS activity_duplicates (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  activity_1_id uuid NOT NULL REFERENCES activities(id) ON DELETE CASCADE,
  activity_2_id uuid NOT NULL REFERENCES activities(id) ON DELETE CASCADE,
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Similarity analysis
  similarity_score numeric(5,2) NOT NULL CHECK (similarity_score >= 0 AND similarity_score <= 100),
  similarity_reasons jsonb NOT NULL DEFAULT '[]',

  -- User resolution
  user_action text CHECK (user_action IN (
    'merged',       -- User merged both into one
    'kept_both',    -- User confirmed they are different activities
    'deleted_1',    -- User deleted activity_1
    'deleted_2',    -- User deleted activity_2
    'ignored'       -- User dismissed without action
  )),
  merged_into_id uuid REFERENCES activities(id) ON DELETE SET NULL,
  resolved_at timestamptz,

  created_at timestamptz DEFAULT now(),

  -- Constraints
  CONSTRAINT no_self_duplicates CHECK (activity_1_id != activity_2_id)
);

-- Create unique index for duplicate pairs (order-independent using expression)
CREATE UNIQUE INDEX unique_duplicate_pair_idx ON activity_duplicates (
  LEAST(activity_1_id, activity_2_id),
  GREATEST(activity_1_id, activity_2_id)
);

-- Indexes for duplicates
CREATE INDEX idx_duplicates_unresolved ON activity_duplicates(user_id, created_at DESC)
  WHERE user_action IS NULL;
CREATE INDEX idx_duplicates_activity_1 ON activity_duplicates(activity_1_id);
CREATE INDEX idx_duplicates_activity_2 ON activity_duplicates(activity_2_id);

COMMENT ON TABLE activity_duplicates IS 'Detected duplicate activities (e.g., manual log + wearable sync of same activity)';
COMMENT ON INDEX unique_duplicate_pair_idx IS 'Ensures we only detect each pair once (order-independent using LEAST/GREATEST)';

-- ============================================
-- STEP 6: Create wearable connections table (feature flagged)
-- ============================================

CREATE TABLE IF NOT EXISTS wearable_connections (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Provider info
  provider text NOT NULL CHECK (provider IN ('garmin', 'strava', 'apple_health', 'fitbit', 'whoop')),
  provider_user_id text,

  -- OAuth tokens (will be encrypted at application level)
  access_token text,
  refresh_token text,
  token_expires_at timestamptz,

  -- Sync state
  last_sync_at timestamptz,
  last_activity_id text, -- Provider's activity ID of last synced activity
  total_synced integer DEFAULT 0 CHECK (total_synced >= 0),
  sync_errors jsonb DEFAULT '[]',

  -- User preferences
  is_active boolean DEFAULT true,
  auto_sync_enabled boolean DEFAULT true,
  sync_settings jsonb DEFAULT '{}', -- {auto_match: true, import_historical: false, etc}

  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),

  -- Constraint: one connection per provider per user
  CONSTRAINT unique_user_provider UNIQUE (user_id, provider)
);

-- Indexes for wearable connections
CREATE INDEX idx_wearable_connections_user_active ON wearable_connections(user_id, is_active);
CREATE INDEX idx_wearable_connections_provider ON wearable_connections(provider, is_active);

COMMENT ON TABLE wearable_connections IS 'User connections to wearable data providers (requires WEARABLES_ENABLED feature flag)';
COMMENT ON COLUMN wearable_connections.access_token IS 'OAuth access token (encrypted at application level before storage)';
COMMENT ON COLUMN wearable_connections.sync_errors IS 'Array of recent sync errors for debugging: [{timestamp, error, details}]';

-- ============================================
-- STEP 7: Update profiles table with activity fields
-- ============================================

-- Add activity-related fields to profiles if they don't exist
ALTER TABLE profiles
  ADD COLUMN IF NOT EXISTS daily_calorie_burn_goal integer DEFAULT 500 CHECK (daily_calorie_burn_goal >= 0 AND daily_calorie_burn_goal <= 10000),
  ADD COLUMN IF NOT EXISTS max_heart_rate integer CHECK (max_heart_rate >= 60 AND max_heart_rate <= 250),
  ADD COLUMN IF NOT EXISTS resting_heart_rate integer CHECK (resting_heart_rate >= 30 AND resting_heart_rate <= 150),
  ADD COLUMN IF NOT EXISTS hr_zone_1_max integer CHECK (hr_zone_1_max >= 60 AND hr_zone_1_max <= 250),
  ADD COLUMN IF NOT EXISTS hr_zone_2_max integer CHECK (hr_zone_2_max >= 60 AND hr_zone_2_max <= 250),
  ADD COLUMN IF NOT EXISTS hr_zone_3_max integer CHECK (hr_zone_3_max >= 60 AND hr_zone_3_max <= 250),
  ADD COLUMN IF NOT EXISTS hr_zone_4_max integer CHECK (hr_zone_4_max >= 60 AND hr_zone_4_max <= 250),
  ADD COLUMN IF NOT EXISTS hr_zone_5_max integer CHECK (hr_zone_5_max >= 60 AND hr_zone_5_max <= 250);

COMMENT ON COLUMN profiles.daily_calorie_burn_goal IS 'User target for daily calories burned through activities (used in activity dashboard)';
COMMENT ON COLUMN profiles.max_heart_rate IS 'User max heart rate (220 - age or measured), used for HR zone calculations';
COMMENT ON COLUMN profiles.resting_heart_rate IS 'User resting heart rate, used for fitness tracking and zone calculations';
COMMENT ON COLUMN profiles.hr_zone_1_max IS 'Heart rate zone 1 upper limit (60-70% max HR, recovery zone)';
COMMENT ON COLUMN profiles.hr_zone_2_max IS 'Heart rate zone 2 upper limit (70-80% max HR, aerobic/base zone)';
COMMENT ON COLUMN profiles.hr_zone_3_max IS 'Heart rate zone 3 upper limit (80-90% max HR, tempo zone)';
COMMENT ON COLUMN profiles.hr_zone_4_max IS 'Heart rate zone 4 upper limit (90-95% max HR, threshold zone)';
COMMENT ON COLUMN profiles.hr_zone_5_max IS 'Heart rate zone 5 upper limit (95-100% max HR, max effort zone)';

-- ============================================
-- STEP 8: Create helper function for HR zone calculation
-- ============================================

CREATE OR REPLACE FUNCTION calculate_hr_zones(user_max_hr integer)
RETURNS TABLE(
  zone_1_max integer,
  zone_2_max integer,
  zone_3_max integer,
  zone_4_max integer,
  zone_5_max integer
) AS $$
BEGIN
  RETURN QUERY SELECT
    (user_max_hr * 0.70)::integer AS zone_1_max,
    (user_max_hr * 0.80)::integer AS zone_2_max,
    (user_max_hr * 0.90)::integer AS zone_3_max,
    (user_max_hr * 0.95)::integer AS zone_4_max,
    user_max_hr AS zone_5_max;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION calculate_hr_zones IS 'Helper function to calculate 5-zone heart rate model from max HR';

-- ============================================
-- VERIFICATION QUERIES
-- ============================================

-- Verify activities table columns
DO $$
DECLARE
  missing_columns text[] := ARRAY[]::text[];
  col text;
BEGIN
  FOR col IN SELECT unnest(ARRAY[
    'end_time', 'deleted_at', 'template_id', 'template_match_score',
    'template_applied_at', 'wearable_activity_id', 'wearable_url',
    'device_name', 'sync_timestamp', 'raw_wearable_data'
  ])
  LOOP
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_name = 'activities' AND column_name = col
    ) THEN
      missing_columns := array_append(missing_columns, col);
    END IF;
  END LOOP;

  IF array_length(missing_columns, 1) > 0 THEN
    RAISE EXCEPTION 'Migration incomplete: activities table missing columns: %', missing_columns;
  END IF;

  RAISE NOTICE 'Activities table: All required columns present ✓';
END $$;

-- Verify new tables exist
DO $$
DECLARE
  missing_tables text[] := ARRAY[]::text[];
  tbl text;
BEGIN
  FOR tbl IN SELECT unnest(ARRAY[
    'activity_templates', 'gps_tracks', 'activity_template_matches',
    'activity_duplicates', 'wearable_connections'
  ])
  LOOP
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.tables
      WHERE table_name = tbl
    ) THEN
      missing_tables := array_append(missing_tables, tbl);
    END IF;
  END LOOP;

  IF array_length(missing_tables, 1) > 0 THEN
    RAISE EXCEPTION 'Migration incomplete: missing tables: %', missing_tables;
  END IF;

  RAISE NOTICE 'New tables: All tables created ✓';
END $$;

-- Verify profiles columns
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'profiles' AND column_name = 'daily_calorie_burn_goal'
  ) THEN
    RAISE EXCEPTION 'Migration incomplete: profiles table missing activity columns';
  END IF;

  RAISE NOTICE 'Profiles table: Activity columns added ✓';
END $$;

-- Final success message
DO $$
BEGIN
  RAISE NOTICE '===========================================';
  RAISE NOTICE 'Migration completed successfully! ✓';
  RAISE NOTICE '===========================================';
  RAISE NOTICE 'Next steps:';
  RAISE NOTICE '1. Test activity creation with template_id';
  RAISE NOTICE '2. Test soft deletes with deleted_at';
  RAISE NOTICE '3. Create activity templates';
  RAISE NOTICE '4. Test template matching';
  RAISE NOTICE '===========================================';
END $$;
