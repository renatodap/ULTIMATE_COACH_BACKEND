-- Migration 012: Fix Activities Schema + Add Exercise Sets System
-- Date: 2025-10-13
-- Description:
--   1. Fix column name mismatches between database and backend code
--   2. Add exercise_sets table for individual set tracking
--   3. Add exercise search/autocomplete support
--   4. Add soft delete filtering

-- ============================================
-- PART 1: Fix Activities Table Column Names
-- ============================================

-- Rename columns to match backend expectations
ALTER TABLE activities RENAME COLUMN name TO activity_name;
ALTER TABLE activities RENAME COLUMN activity_type TO category;
ALTER TABLE activities RENAME COLUMN calories TO calories_burned;

-- Add missing intensity_mets column
ALTER TABLE activities ADD COLUMN IF NOT EXISTS intensity_mets NUMERIC(4,2)
  CHECK (intensity_mets >= 1.0 AND intensity_mets <= 20.0);

-- Add soft delete column if not exists (from migration 20251012_230748)
ALTER TABLE activities ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;

-- Update category constraint to match backend validation
ALTER TABLE activities DROP CONSTRAINT IF EXISTS activities_category_check;
ALTER TABLE activities ADD CONSTRAINT activities_category_check
  CHECK (category IN (
    'cardio_steady_state',
    'cardio_interval',
    'strength_training',
    'sports',
    'flexibility',
    'other'
  ));

-- Add comments for documentation
COMMENT ON COLUMN activities.activity_name IS 'User-defined name for the activity (e.g., "Morning Run", "Leg Day")';
COMMENT ON COLUMN activities.category IS 'Activity category: cardio_steady_state, cardio_interval, strength_training, sports, flexibility, other';
COMMENT ON COLUMN activities.calories_burned IS 'Total calories burned during activity';
COMMENT ON COLUMN activities.intensity_mets IS 'Metabolic Equivalent of Task (1.0 = resting, 8.0 = running)';

-- Update index to use new column name
DROP INDEX IF EXISTS idx_activities_user_start;
CREATE INDEX IF NOT EXISTS idx_activities_user_start ON activities(user_id, start_time DESC) WHERE deleted_at IS NULL;

-- ============================================
-- PART 2: Create Exercise Sets Table
-- ============================================

CREATE TABLE IF NOT EXISTS exercise_sets (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  activity_id UUID NOT NULL REFERENCES activities(id) ON DELETE CASCADE,
  exercise_id UUID NOT NULL REFERENCES exercises(id) ON DELETE RESTRICT,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Set details
  set_number INTEGER NOT NULL CHECK (set_number >= 1 AND set_number <= 50),
  reps INTEGER CHECK (reps >= 1 AND reps <= 1000),
  weight_kg NUMERIC(6,2) CHECK (weight_kg >= 0 AND weight_kg <= 1000),

  -- Time-based sets (for cardio/bodyweight)
  duration_seconds INTEGER CHECK (duration_seconds >= 1 AND duration_seconds <= 3600),
  distance_meters NUMERIC(8,2) CHECK (distance_meters > 0),

  -- Intensity tracking
  rpe INTEGER CHECK (rpe >= 1 AND rpe <= 10),  -- Rate of Perceived Exertion
  tempo TEXT,  -- e.g., "3-1-2-0" (eccentric-pause-concentric-pause)
  rest_seconds INTEGER CHECK (rest_seconds >= 0 AND rest_seconds <= 600),

  -- Performance notes
  completed BOOLEAN DEFAULT true,
  failure BOOLEAN DEFAULT false,  -- Did set go to failure?
  notes TEXT,

  -- Metadata
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  -- Constraints
  CONSTRAINT exercise_sets_data_check CHECK (
    -- Must have either reps+weight OR duration OR distance
    (reps IS NOT NULL AND weight_kg IS NOT NULL) OR
    duration_seconds IS NOT NULL OR
    distance_meters IS NOT NULL
  ),
  CONSTRAINT unique_activity_exercise_set UNIQUE (activity_id, exercise_id, set_number)
);

-- Indexes for exercise_sets
CREATE INDEX idx_exercise_sets_activity ON exercise_sets(activity_id);
CREATE INDEX idx_exercise_sets_exercise ON exercise_sets(exercise_id);
CREATE INDEX idx_exercise_sets_user ON exercise_sets(user_id, created_at DESC);
CREATE INDEX idx_exercise_sets_user_exercise ON exercise_sets(user_id, exercise_id, created_at DESC);

-- Comments
COMMENT ON TABLE exercise_sets IS 'Individual sets for strength training activities - enables progressive overload tracking';
COMMENT ON COLUMN exercise_sets.set_number IS 'Set number within the activity (1, 2, 3, etc.)';
COMMENT ON COLUMN exercise_sets.rpe IS 'Rate of Perceived Exertion (1-10 scale, 10 = maximum effort)';
COMMENT ON COLUMN exercise_sets.tempo IS 'Tempo notation: eccentric-pause-concentric-pause (e.g., "3-1-2-0" = 3sec down, 1sec pause, 2sec up, no pause)';
COMMENT ON COLUMN exercise_sets.failure IS 'Whether set was taken to muscular failure';
COMMENT ON COLUMN exercise_sets.completed IS 'Whether set was completed (false if abandoned mid-set)';

-- ============================================
-- PART 3: Add Exercise Search Function
-- ============================================

-- Create full-text search index on exercises table
CREATE INDEX IF NOT EXISTS idx_exercises_name_search
  ON exercises USING gin(to_tsvector('english', name));

CREATE INDEX IF NOT EXISTS idx_exercises_category ON exercises(category) WHERE is_public = true;
CREATE INDEX IF NOT EXISTS idx_exercises_usage ON exercises(usage_count DESC) WHERE is_public = true;

-- Function to search exercises with ranking
CREATE OR REPLACE FUNCTION search_exercises(
  search_query TEXT,
  category_filter TEXT DEFAULT NULL,
  limit_count INTEGER DEFAULT 20
)
RETURNS TABLE (
  id UUID,
  name TEXT,
  description TEXT,
  category TEXT,
  primary_muscle_groups TEXT[],
  equipment_needed TEXT[],
  difficulty_level TEXT,
  usage_count INTEGER,
  rank REAL
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    e.id,
    e.name,
    e.description,
    e.category,
    e.primary_muscle_groups,
    e.equipment_needed,
    e.difficulty_level,
    e.usage_count,
    ts_rank(to_tsvector('english', e.name), plainto_tsquery('english', search_query)) AS rank
  FROM exercises e
  WHERE
    e.is_public = true
    AND e.verified = true
    AND to_tsvector('english', e.name) @@ plainto_tsquery('english', search_query)
    AND (category_filter IS NULL OR e.category = category_filter)
  ORDER BY rank DESC, e.usage_count DESC
  LIMIT limit_count;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION search_exercises IS 'Full-text search for exercises with relevance ranking';

-- ============================================
-- PART 4: Create Exercise History View
-- ============================================

-- View to easily query user's exercise history with PRs
CREATE OR REPLACE VIEW user_exercise_history AS
SELECT
  es.user_id,
  es.exercise_id,
  e.name as exercise_name,
  e.category,
  es.activity_id,
  a.activity_name,
  a.start_time,
  es.set_number,
  es.reps,
  es.weight_kg,
  es.duration_seconds,
  es.distance_meters,
  es.rpe,
  es.completed,
  -- Calculate one-rep max estimate (Epley formula)
  CASE
    WHEN es.reps IS NOT NULL AND es.weight_kg IS NOT NULL AND es.reps <= 10
    THEN ROUND(es.weight_kg * (1 + es.reps / 30.0), 2)
    ELSE NULL
  END as estimated_1rm,
  -- Calculate total volume for this set
  CASE
    WHEN es.reps IS NOT NULL AND es.weight_kg IS NOT NULL
    THEN ROUND(es.reps * es.weight_kg, 2)
    ELSE NULL
  END as set_volume
FROM exercise_sets es
JOIN exercises e ON es.exercise_id = e.id
JOIN activities a ON es.activity_id = a.id
WHERE a.deleted_at IS NULL;

COMMENT ON VIEW user_exercise_history IS 'Complete exercise history with calculated 1RM estimates and volume';

-- ============================================
-- PART 5: Create Personal Records View
-- ============================================

CREATE OR REPLACE VIEW user_personal_records AS
WITH ranked_sets AS (
  SELECT
    user_id,
    exercise_id,
    weight_kg,
    reps,
    ROUND(weight_kg * (1 + reps / 30.0), 2) as estimated_1rm,
    ROUND(reps * weight_kg, 2) as volume,
    start_time,
    ROW_NUMBER() OVER (PARTITION BY user_id, exercise_id ORDER BY weight_kg DESC) as max_weight_rank,
    ROW_NUMBER() OVER (PARTITION BY user_id, exercise_id ORDER BY weight_kg * (1 + reps / 30.0) DESC) as max_1rm_rank,
    ROW_NUMBER() OVER (PARTITION BY user_id, exercise_id ORDER BY reps * weight_kg DESC) as max_volume_rank
  FROM user_exercise_history
  WHERE completed = true
    AND reps IS NOT NULL
    AND weight_kg IS NOT NULL
)
SELECT
  user_id,
  exercise_id,
  MAX(CASE WHEN max_weight_rank = 1 THEN weight_kg END) as max_weight_kg,
  MAX(CASE WHEN max_weight_rank = 1 THEN reps END) as max_weight_reps,
  MAX(CASE WHEN max_weight_rank = 1 THEN start_time END) as max_weight_date,
  MAX(CASE WHEN max_1rm_rank = 1 THEN estimated_1rm END) as max_estimated_1rm,
  MAX(CASE WHEN max_1rm_rank = 1 THEN start_time END) as max_1rm_date,
  MAX(CASE WHEN max_volume_rank = 1 THEN volume END) as max_set_volume,
  MAX(CASE WHEN max_volume_rank = 1 THEN start_time END) as max_volume_date
FROM ranked_sets
GROUP BY user_id, exercise_id;

COMMENT ON VIEW user_personal_records IS 'Personal records per exercise: max weight, estimated 1RM, max volume';

-- ============================================
-- PART 6: Add Update Trigger for Exercise Usage Count
-- ============================================

CREATE OR REPLACE FUNCTION update_exercise_usage_count()
RETURNS TRIGGER AS $$
BEGIN
  -- Increment usage count when exercise is used in a set
  UPDATE exercises
  SET usage_count = usage_count + 1,
      updated_at = NOW()
  WHERE id = NEW.exercise_id;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_exercise_usage
  AFTER INSERT ON exercise_sets
  FOR EACH ROW
  EXECUTE FUNCTION update_exercise_usage_count();

COMMENT ON FUNCTION update_exercise_usage_count IS 'Automatically increment exercise usage count when used in a workout';

-- ============================================
-- PART 7: Migration Data Handling
-- ============================================

-- Migrate existing JSONB exercises data to exercise_sets table (if needed)
DO $$
DECLARE
  activity_record RECORD;
  exercise_data JSONB;
  exercise_record RECORD;
  matched_exercise_id UUID;
  set_num INTEGER;
BEGIN
  -- Only process activities with exercises in JSONB that haven't been migrated
  FOR activity_record IN
    SELECT id, user_id, exercises, start_time
    FROM activities
    WHERE exercises IS NOT NULL
      AND exercises != '[]'::jsonb
      AND deleted_at IS NULL
      AND NOT EXISTS (
        SELECT 1 FROM exercise_sets es WHERE es.activity_id = activities.id
      )
  LOOP
    -- Process each exercise in the JSONB array
    FOR exercise_data IN SELECT * FROM jsonb_array_elements(activity_record.exercises)
    LOOP
      -- Try to match exercise by name (case-insensitive)
      SELECT id INTO matched_exercise_id
      FROM exercises
      WHERE LOWER(name) = LOWER(exercise_data->>'name')
        AND is_public = true
      LIMIT 1;

      -- Skip if we can't match the exercise (would need manual intervention)
      IF matched_exercise_id IS NULL THEN
        RAISE NOTICE 'Could not match exercise: % in activity %',
          exercise_data->>'name', activity_record.id;
        CONTINUE;
      END IF;

      -- Insert sets for this exercise
      FOR set_num IN 1..(exercise_data->>'sets')::INTEGER
      LOOP
        INSERT INTO exercise_sets (
          activity_id,
          exercise_id,
          user_id,
          set_number,
          reps,
          weight_kg,
          rpe,
          created_at
        ) VALUES (
          activity_record.id,
          matched_exercise_id,
          activity_record.user_id,
          set_num,
          (exercise_data->>'reps')::INTEGER,
          (exercise_data->>'weight_kg')::NUMERIC,
          (exercise_data->>'rpe')::INTEGER,
          activity_record.start_time
        );
      END LOOP;

      RAISE NOTICE 'Migrated exercise % (% sets) for activity %',
        exercise_data->>'name', exercise_data->>'sets', activity_record.id;
    END LOOP;
  END LOOP;

  RAISE NOTICE 'Exercise data migration complete';
END $$;

-- ============================================
-- VERIFICATION QUERIES
-- ============================================

DO $$
DECLARE
  activities_count INTEGER;
  exercise_sets_count INTEGER;
BEGIN
  -- Verify activities table columns
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'activities' AND column_name = 'activity_name'
  ) THEN
    RAISE EXCEPTION 'Migration failed: activities.activity_name column not found';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'activities' AND column_name = 'category'
  ) THEN
    RAISE EXCEPTION 'Migration failed: activities.category column not found';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'activities' AND column_name = 'calories_burned'
  ) THEN
    RAISE EXCEPTION 'Migration failed: activities.calories_burned column not found';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'activities' AND column_name = 'intensity_mets'
  ) THEN
    RAISE EXCEPTION 'Migration failed: activities.intensity_mets column not found';
  END IF;

  -- Verify exercise_sets table exists
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_name = 'exercise_sets'
  ) THEN
    RAISE EXCEPTION 'Migration failed: exercise_sets table not created';
  END IF;

  -- Count records
  SELECT COUNT(*) INTO activities_count FROM activities WHERE deleted_at IS NULL;
  SELECT COUNT(*) INTO exercise_sets_count FROM exercise_sets;

  RAISE NOTICE '===========================================';
  RAISE NOTICE 'Migration 012 completed successfully! ✓';
  RAISE NOTICE '===========================================';
  RAISE NOTICE 'Activities table: Column names fixed ✓';
  RAISE NOTICE 'Exercise sets table: Created ✓';
  RAISE NOTICE 'Search function: Created ✓';
  RAISE NOTICE 'Views: Created (user_exercise_history, user_personal_records) ✓';
  RAISE NOTICE 'Triggers: Created (exercise usage counter) ✓';
  RAISE NOTICE '';
  RAISE NOTICE 'Statistics:';
  RAISE NOTICE '  - Active activities: %', activities_count;
  RAISE NOTICE '  - Migrated exercise sets: %', exercise_sets_count;
  RAISE NOTICE '';
  RAISE NOTICE 'Next steps:';
  RAISE NOTICE '1. Update backend code to use exercise_sets table';
  RAISE NOTICE '2. Update frontend to use exercise autocomplete';
  RAISE NOTICE '3. Test activity creation with new schema';
  RAISE NOTICE '4. Test exercise set tracking';
  RAISE NOTICE '===========================================';
END $$;
