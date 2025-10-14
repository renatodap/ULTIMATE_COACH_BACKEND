-- ============================================================================
-- ADAPTIVE PROGRAM SYSTEM - Additional SQL Functions
-- ============================================================================
-- Functions to support program generation, activity tracking, and reassessment
-- ============================================================================

-- ============================================================================
-- FUNCTION: get_active_templates
-- ============================================================================
-- Get user's active workout templates

CREATE OR REPLACE FUNCTION get_active_templates(p_user_id UUID)
RETURNS TABLE (
  id UUID,
  template_name TEXT,
  activity_type TEXT,
  default_exercises JSONB,
  expected_duration_minutes INTEGER,
  use_count INTEGER,
  last_used_at TIMESTAMPTZ
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    at.id,
    at.template_name,
    at.activity_type,
    at.default_exercises,
    at.expected_duration_minutes,
    at.use_count,
    at.last_used_at
  FROM activity_templates at
  WHERE
    at.user_id = p_user_id
    AND at.is_active = TRUE
  ORDER BY at.created_at;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_active_templates IS 'Returns user''s active workout templates for current program';

-- ============================================================================
-- FUNCTION: get_todays_template
-- ============================================================================
-- Get today's recommended workout template based on day of week

CREATE OR REPLACE FUNCTION get_todays_template(p_user_id UUID)
RETURNS TABLE (
  id UUID,
  template_name TEXT,
  activity_type TEXT,
  default_exercises JSONB,
  description TEXT,
  expected_duration_minutes INTEGER
) AS $$
DECLARE
  v_day_of_week INTEGER;
  v_template_count INTEGER;
  v_template_index INTEGER;
BEGIN
  -- Get day of week (1=Monday, 7=Sunday)
  v_day_of_week := EXTRACT(ISODOW FROM CURRENT_DATE);

  -- Count active templates
  SELECT COUNT(*) INTO v_template_count
  FROM activity_templates
  WHERE user_id = p_user_id AND is_active = TRUE;

  -- If no templates, return empty
  IF v_template_count = 0 THEN
    RETURN;
  END IF;

  -- Simple rotation: template_index = (day_of_week - 1) % template_count
  v_template_index := (v_day_of_week - 1) % v_template_count;

  -- Return the template at this index
  RETURN QUERY
  SELECT
    at.id,
    at.template_name,
    at.activity_type,
    at.default_exercises,
    at.description,
    at.expected_duration_minutes
  FROM activity_templates at
  WHERE
    at.user_id = p_user_id
    AND at.is_active = TRUE
  ORDER BY at.created_at
  OFFSET v_template_index
  LIMIT 1;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_todays_template IS 'Returns today''s recommended workout template based on simple rotation';

-- ============================================================================
-- FUNCTION: get_adherence_for_period
-- ============================================================================
-- Calculate adherence for a period

CREATE OR REPLACE FUNCTION get_adherence_for_period(
  p_user_id UUID,
  p_days_back INTEGER DEFAULT 14
)
RETURNS TABLE (
  planned_count INTEGER,
  completed_count INTEGER,
  adherence_pct NUMERIC,
  completed_with_template INTEGER,
  completed_without_template INTEGER,
  informal_activities INTEGER
) AS $$
DECLARE
  v_start_date TIMESTAMPTZ;
  v_template_count INTEGER;
BEGIN
  v_start_date := NOW() - (p_days_back || ' days')::INTERVAL;

  -- Count active templates
  SELECT COUNT(*) INTO v_template_count
  FROM activity_templates
  WHERE user_id = p_user_id AND is_active = TRUE;

  -- Calculate planned count (templates × weeks in period)
  planned_count := v_template_count * (p_days_back / 7.0)::INTEGER;

  -- Count completed activities with template_id
  SELECT COUNT(*) INTO completed_with_template
  FROM activities
  WHERE
    user_id = p_user_id
    AND start_time >= v_start_date
    AND template_id IS NOT NULL
    AND deleted_at IS NULL;

  -- Count completed activities without template (manual logs)
  SELECT COUNT(*) INTO completed_without_template
  FROM activities
  WHERE
    user_id = p_user_id
    AND start_time >= v_start_date
    AND template_id IS NULL
    AND source != 'coach_chat'
    AND deleted_at IS NULL;

  -- Count informal activities (from chat)
  SELECT COUNT(*) INTO informal_activities
  FROM activities
  WHERE
    user_id = p_user_id
    AND start_time >= v_start_date
    AND source = 'coach_chat'
    AND (metrics->>'informal_log')::BOOLEAN = TRUE
    AND deleted_at IS NULL;

  -- Total completed
  completed_count := completed_with_template + completed_without_template;

  -- Calculate adherence percentage
  IF planned_count > 0 THEN
    adherence_pct := (completed_count::NUMERIC / planned_count::NUMERIC) * 100;
  ELSE
    adherence_pct := 0;
  END IF;

  RETURN QUERY
  SELECT
    planned_count,
    completed_count,
    adherence_pct,
    completed_with_template,
    completed_without_template,
    informal_activities;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_adherence_for_period IS 'Calculates workout adherence for a period';

-- ============================================================================
-- FUNCTION: get_exercise_history_for_user
-- ============================================================================
-- Get exercise history with PRs

CREATE OR REPLACE FUNCTION get_exercise_history_for_user(
  p_user_id UUID,
  p_exercise_id UUID,
  p_limit INTEGER DEFAULT 20
)
RETURNS TABLE (
  activity_id UUID,
  activity_name TEXT,
  start_time TIMESTAMPTZ,
  set_number INTEGER,
  reps INTEGER,
  weight_kg NUMERIC,
  rpe INTEGER,
  estimated_1rm NUMERIC,
  set_volume NUMERIC
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    a.id AS activity_id,
    a.activity_name,
    a.start_time,
    es.set_number,
    es.reps,
    es.weight_kg,
    es.rpe,
    -- Estimated 1RM (Epley formula)
    CASE
      WHEN es.reps IS NOT NULL AND es.weight_kg IS NOT NULL AND es.reps <= 10
      THEN ROUND((es.weight_kg * (1 + es.reps / 30.0))::NUMERIC, 2)
      ELSE NULL
    END AS estimated_1rm,
    -- Set volume
    CASE
      WHEN es.reps IS NOT NULL AND es.weight_kg IS NOT NULL
      THEN ROUND((es.reps * es.weight_kg)::NUMERIC, 2)
      ELSE NULL
    END AS set_volume
  FROM exercise_sets es
  JOIN activities a ON es.activity_id = a.id
  WHERE
    es.user_id = p_user_id
    AND es.exercise_id = p_exercise_id
    AND es.completed = TRUE
    AND a.deleted_at IS NULL
  ORDER BY a.start_time DESC, es.set_number
  LIMIT p_limit;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_exercise_history_for_user IS 'Returns recent history for an exercise with calculated 1RM and volume';

-- ============================================================================
-- FUNCTION: get_personal_records
-- ============================================================================
-- Get PRs for an exercise

CREATE OR REPLACE FUNCTION get_personal_records(
  p_user_id UUID,
  p_exercise_id UUID
)
RETURNS TABLE (
  max_weight_kg NUMERIC,
  max_weight_reps INTEGER,
  max_weight_date TIMESTAMPTZ,
  max_estimated_1rm NUMERIC,
  max_1rm_date TIMESTAMPTZ,
  max_set_volume NUMERIC,
  max_volume_date TIMESTAMPTZ
) AS $$
BEGIN
  RETURN QUERY
  WITH exercise_history AS (
    SELECT
      es.weight_kg,
      es.reps,
      a.start_time,
      -- Estimated 1RM
      CASE
        WHEN es.reps IS NOT NULL AND es.weight_kg IS NOT NULL AND es.reps <= 10
        THEN ROUND((es.weight_kg * (1 + es.reps / 30.0))::NUMERIC, 2)
        ELSE NULL
      END AS estimated_1rm,
      -- Set volume
      CASE
        WHEN es.reps IS NOT NULL AND es.weight_kg IS NOT NULL
        THEN ROUND((es.reps * es.weight_kg)::NUMERIC, 2)
        ELSE NULL
      END AS set_volume
    FROM exercise_sets es
    JOIN activities a ON es.activity_id = a.id
    WHERE
      es.user_id = p_user_id
      AND es.exercise_id = p_exercise_id
      AND es.completed = TRUE
      AND es.weight_kg IS NOT NULL
      AND a.deleted_at IS NULL
  )
  SELECT
    (SELECT weight_kg FROM exercise_history ORDER BY weight_kg DESC LIMIT 1) AS max_weight_kg,
    (SELECT reps FROM exercise_history ORDER BY weight_kg DESC LIMIT 1) AS max_weight_reps,
    (SELECT start_time FROM exercise_history ORDER BY weight_kg DESC LIMIT 1) AS max_weight_date,
    (SELECT estimated_1rm FROM exercise_history ORDER BY estimated_1rm DESC LIMIT 1) AS max_estimated_1rm,
    (SELECT start_time FROM exercise_history ORDER BY estimated_1rm DESC LIMIT 1) AS max_1rm_date,
    (SELECT set_volume FROM exercise_history ORDER BY set_volume DESC LIMIT 1) AS max_set_volume,
    (SELECT start_time FROM exercise_history ORDER BY set_volume DESC LIMIT 1) AS max_volume_date;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_personal_records IS 'Returns personal records for an exercise';

-- ============================================================================
-- FUNCTION: get_weekly_volume
-- ============================================================================
-- Calculate weekly training volume

CREATE OR REPLACE FUNCTION get_weekly_volume(
  p_user_id UUID,
  p_weeks_back INTEGER DEFAULT 4
)
RETURNS TABLE (
  week_start DATE,
  total_activities INTEGER,
  total_sets INTEGER,
  total_volume NUMERIC,
  avg_rpe NUMERIC
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    DATE_TRUNC('week', a.start_time)::DATE AS week_start,
    COUNT(DISTINCT a.id)::INTEGER AS total_activities,
    COUNT(es.id)::INTEGER AS total_sets,
    SUM(COALESCE(es.reps * es.weight_kg, 0))::NUMERIC AS total_volume,
    ROUND(AVG(es.rpe)::NUMERIC, 1) AS avg_rpe
  FROM activities a
  LEFT JOIN exercise_sets es ON a.id = es.activity_id
  WHERE
    a.user_id = p_user_id
    AND a.start_time >= NOW() - (p_weeks_back || ' weeks')::INTERVAL
    AND a.deleted_at IS NULL
    AND a.category IN ('strength_training', 'cardio_steady_state', 'cardio_interval')
  GROUP BY DATE_TRUNC('week', a.start_time)
  ORDER BY week_start DESC;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_weekly_volume IS 'Returns weekly training volume metrics';

-- ============================================================================
-- FUNCTION: increment_template_use_count
-- ============================================================================
-- Increment use count when template is used

CREATE OR REPLACE FUNCTION increment_template_use_count()
RETURNS TRIGGER AS $$
BEGIN
  -- When an activity is created with a template_id, increment template use count
  IF NEW.template_id IS NOT NULL THEN
    UPDATE activity_templates
    SET
      use_count = use_count + 1,
      last_used_at = NEW.start_time
    WHERE id = NEW.template_id;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
DROP TRIGGER IF EXISTS trigger_increment_template_use ON activities;
CREATE TRIGGER trigger_increment_template_use
  AFTER INSERT ON activities
  FOR EACH ROW
  EXECUTE FUNCTION increment_template_use_count();

COMMENT ON FUNCTION increment_template_use_count IS 'Auto-increment template use_count when activity is created';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
BEGIN
  RAISE NOTICE '===========================================';
  RAISE NOTICE 'Program SQL Functions Created Successfully';
  RAISE NOTICE '===========================================';
  RAISE NOTICE 'Functions created:';
  RAISE NOTICE '  - get_active_templates()';
  RAISE NOTICE '  - get_todays_template()';
  RAISE NOTICE '  - get_adherence_for_period()';
  RAISE NOTICE '  - get_exercise_history_for_user()';
  RAISE NOTICE '  - get_personal_records()';
  RAISE NOTICE '  - get_weekly_volume()';
  RAISE NOTICE '  - increment_template_use_count() + trigger';
  RAISE NOTICE '===========================================';
END $$;
