-- ============================================================================
-- Database Helper Functions for Program Management
-- ============================================================================
-- Drop-in for: ULTIMATE_COACH_BACKEND/database/functions.sql
--
-- These PostgreSQL functions provide efficient queries for the adaptive system.
-- Run this file after the main migration (001_adaptive_system.sql).
-- ============================================================================

-- ============================================================================
-- Function: Get User's Active Plan
-- ============================================================================

CREATE OR REPLACE FUNCTION get_active_plan(p_user_id UUID)
RETURNS TABLE (
    plan_id UUID,
    version INTEGER,
    plan_data JSONB,
    valid_from DATE,
    created_at TIMESTAMPTZ,
    days_since_creation INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        pv.id AS plan_id,
        pv.version,
        pv.plan_data,
        pv.valid_from,
        pv.created_at,
        (CURRENT_DATE - pv.valid_from)::INTEGER AS days_since_creation
    FROM plan_versions pv
    WHERE pv.user_id = p_user_id
      AND pv.status = 'active'
    ORDER BY pv.version DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_active_plan IS 'Get user''s current active plan with metadata';


-- ============================================================================
-- Function: Calculate Today's Plan Details
-- ============================================================================

CREATE OR REPLACE FUNCTION calculate_today_plan_details(
    p_user_id UUID,
    p_today_date DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE (
    plan_id UUID,
    cycle_day INTEGER,
    cycle_week INTEGER,
    is_training_day BOOLEAN,
    training_day_number INTEGER,
    workout_data JSONB,
    meals_data JSONB,
    macro_targets JSONB
) AS $$
DECLARE
    v_plan_data JSONB;
    v_valid_from DATE;
    v_days_since_start INTEGER;
    v_workouts_per_week INTEGER;
    v_cycle_length INTEGER;
BEGIN
    -- Get active plan
    SELECT ap.plan_data, ap.valid_from
    INTO v_plan_data, v_valid_from
    FROM get_active_plan(p_user_id) ap;

    IF v_plan_data IS NULL THEN
        RAISE EXCEPTION 'No active plan found for user %', p_user_id;
    END IF;

    -- Calculate days since plan started
    v_days_since_start := p_today_date - v_valid_from;

    -- Extract plan parameters
    v_workouts_per_week := (v_plan_data->'training'->>'workouts_per_week')::INTEGER;
    v_cycle_length := (v_plan_data->'training'->>'microcycle_length_days')::INTEGER;

    -- Calculate cycle position
    cycle_day := (v_days_since_start % v_cycle_length) + 1;
    cycle_week := (v_days_since_start / 7)::INTEGER + 1;

    -- Determine if today is a training day
    -- This depends on the workout schedule in plan_data
    -- For now, simplified logic - check if workout exists for this cycle day

    -- Return plan details
    plan_id := (SELECT id FROM plan_versions WHERE user_id = p_user_id AND status = 'active' LIMIT 1);
    workout_data := v_plan_data->'training'->'microcycle'->(cycle_day - 1);
    is_training_day := (workout_data IS NOT NULL);

    -- Calculate training day number (1st, 2nd, 3rd workout this week)
    training_day_number := NULL;  -- Would need more complex logic

    -- Get today's meals (cycle through 14-day meal plan)
    meals_data := v_plan_data->'nutrition'->'meal_plan'->((v_days_since_start % 14)::INTEGER);

    -- Get macro targets
    macro_targets := v_plan_data->'nutrition'->'daily_targets';

    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION calculate_today_plan_details IS 'Calculate what the user should do today based on their active plan';


-- ============================================================================
-- Function: Get Progress Metrics (Last N Days)
-- ============================================================================

CREATE OR REPLACE FUNCTION get_progress_metrics(
    p_user_id UUID,
    p_days INTEGER DEFAULT 14
)
RETURNS TABLE (
    start_date DATE,
    end_date DATE,

    -- Weight metrics
    start_weight_kg NUMERIC,
    current_weight_kg NUMERIC,
    weight_change_kg NUMERIC,
    weight_change_rate_per_week NUMERIC,

    -- Adherence metrics
    days_with_meals_logged INTEGER,
    days_with_workouts INTEGER,
    days_with_weight_logged INTEGER,
    meal_logging_adherence NUMERIC,
    training_adherence NUMERIC,

    -- Nutrition metrics
    avg_calories_consumed NUMERIC,
    avg_protein_consumed_g NUMERIC,

    -- Training metrics
    total_sets_completed INTEGER,
    avg_sets_per_workout NUMERIC
) AS $$
DECLARE
    v_start_date DATE;
    v_end_date DATE;
    v_weeks NUMERIC;
BEGIN
    v_end_date := CURRENT_DATE;
    v_start_date := v_end_date - p_days;
    v_weeks := p_days::NUMERIC / 7.0;

    start_date := v_start_date;
    end_date := v_end_date;

    -- Weight metrics
    SELECT
        FIRST_VALUE(bm.weight_kg) OVER (ORDER BY bm.recorded_at ASC),
        FIRST_VALUE(bm.weight_kg) OVER (ORDER BY bm.recorded_at DESC)
    INTO start_weight_kg, current_weight_kg
    FROM body_metrics bm
    WHERE bm.user_id = p_user_id
      AND bm.recorded_at::DATE BETWEEN v_start_date AND v_end_date;

    weight_change_kg := current_weight_kg - start_weight_kg;
    weight_change_rate_per_week := CASE
        WHEN v_weeks > 0 THEN weight_change_kg / v_weeks
        ELSE 0
    END;

    -- Adherence metrics
    SELECT
        COUNT(DISTINCT m.created_at::DATE),
        COUNT(DISTINCT a.created_at::DATE),
        COUNT(DISTINCT bm.recorded_at::DATE)
    INTO
        days_with_meals_logged,
        days_with_workouts,
        days_with_weight_logged
    FROM generate_series(v_start_date, v_end_date, '1 day'::INTERVAL) gs(day)
    LEFT JOIN meals m ON m.user_id = p_user_id AND m.created_at::DATE = gs.day::DATE
    LEFT JOIN activities a ON a.user_id = p_user_id AND a.created_at::DATE = gs.day::DATE AND a.activity_type = 'workout'
    LEFT JOIN body_metrics bm ON bm.user_id = p_user_id AND bm.recorded_at::DATE = gs.day::DATE;

    meal_logging_adherence := days_with_meals_logged::NUMERIC / p_days::NUMERIC;

    -- Get expected workouts per week from active plan
    training_adherence := days_with_workouts::NUMERIC /
        (SELECT
            ((v_plan_data->'training'->>'workouts_per_week')::NUMERIC * v_weeks)
         FROM get_active_plan(p_user_id)
        );

    -- Nutrition metrics
    SELECT
        ROUND(AVG(m.total_calories)),
        ROUND(AVG(m.total_protein_g), 1)
    INTO
        avg_calories_consumed,
        avg_protein_consumed_g
    FROM meals m
    WHERE m.user_id = p_user_id
      AND m.created_at::DATE BETWEEN v_start_date AND v_end_date;

    -- Training metrics
    SELECT
        SUM(a.total_sets),
        ROUND(AVG(a.total_sets), 1)
    INTO
        total_sets_completed,
        avg_sets_per_workout
    FROM activities a
    WHERE a.user_id = p_user_id
      AND a.activity_type = 'workout'
      AND a.created_at::DATE BETWEEN v_start_date AND v_end_date;

    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_progress_metrics IS 'Calculate comprehensive progress metrics for a user over N days';


-- ============================================================================
-- Function: Check If Reassessment Due
-- ============================================================================

CREATE OR REPLACE FUNCTION is_reassessment_due(p_user_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    v_valid_from DATE;
    v_days_since_creation INTEGER;
BEGIN
    -- Get active plan start date
    SELECT valid_from
    INTO v_valid_from
    FROM plan_versions
    WHERE user_id = p_user_id
      AND status = 'active'
    ORDER BY version DESC
    LIMIT 1;

    IF v_valid_from IS NULL THEN
        RETURN FALSE;
    END IF;

    -- Calculate days since creation
    v_days_since_creation := CURRENT_DATE - v_valid_from;

    -- Due if it's been 14, 28, 42, etc. days (14-day intervals)
    RETURN (v_days_since_creation > 0 AND v_days_since_creation % 14 = 0);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION is_reassessment_due IS 'Check if user is due for bi-weekly reassessment';


-- ============================================================================
-- Function: Get All Users Due for Reassessment
-- ============================================================================

CREATE OR REPLACE FUNCTION get_users_due_for_reassessment()
RETURNS TABLE (
    user_id UUID,
    plan_id UUID,
    version INTEGER,
    valid_from DATE,
    days_since_creation INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        pv.user_id,
        pv.id AS plan_id,
        pv.version,
        pv.valid_from,
        (CURRENT_DATE - pv.valid_from)::INTEGER AS days_since_creation
    FROM plan_versions pv
    WHERE pv.status = 'active'
      AND (CURRENT_DATE - pv.valid_from) % 14 = 0
      AND (CURRENT_DATE - pv.valid_from) >= 14
    ORDER BY pv.valid_from ASC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_users_due_for_reassessment IS 'Get all users whose plans are due for reassessment today';


-- ============================================================================
-- Function: Mark Plan as Superseded
-- ============================================================================

CREATE OR REPLACE FUNCTION mark_plan_superseded(
    p_plan_id UUID,
    p_superseded_by_id UUID
)
RETURNS VOID AS $$
BEGIN
    UPDATE plan_versions
    SET
        status = 'superseded',
        superseded_by = p_superseded_by_id,
        valid_until = CURRENT_DATE
    WHERE id = p_plan_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION mark_plan_superseded IS 'Mark an old plan version as superseded by a new version';


-- ============================================================================
-- Function: Get Plan History
-- ============================================================================

CREATE OR REPLACE FUNCTION get_plan_history(p_user_id UUID)
RETURNS TABLE (
    plan_id UUID,
    version INTEGER,
    status TEXT,
    created_at TIMESTAMPTZ,
    valid_from DATE,
    valid_until DATE,
    daily_calories INTEGER,
    workouts_per_week INTEGER,
    adjustment_reason TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        pv.id AS plan_id,
        pv.version,
        pv.status,
        pv.created_at,
        pv.valid_from,
        pv.valid_until,
        (pv.plan_data->'nutrition'->'daily_targets'->>'calories')::INTEGER AS daily_calories,
        (pv.plan_data->'training'->>'workouts_per_week')::INTEGER AS workouts_per_week,
        pa.adjustment_reason
    FROM plan_versions pv
    LEFT JOIN plan_adjustments pa ON pa.to_version = pv.version AND pa.plan_id = pv.id
    WHERE pv.user_id = p_user_id
    ORDER BY pv.version DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_plan_history IS 'Get complete history of a user''s plan versions and adjustments';


-- ============================================================================
-- Function: Get Grocery List (14-Day Meal Plan)
-- ============================================================================

CREATE OR REPLACE FUNCTION get_grocery_list(p_user_id UUID)
RETURNS TABLE (
    food_name TEXT,
    total_quantity NUMERIC,
    unit TEXT,
    category TEXT,
    used_in_days INTEGER
) AS $$
BEGIN
    RETURN QUERY
    WITH meal_plan AS (
        SELECT plan_data->'nutrition'->'meal_plan' AS meals
        FROM plan_versions
        WHERE user_id = p_user_id
          AND status = 'active'
        LIMIT 1
    ),
    all_foods AS (
        SELECT
            food->>'food_name' AS food_name,
            (food->>'quantity')::NUMERIC AS quantity,
            food->>'unit' AS unit,
            food->>'category' AS category
        FROM meal_plan,
             jsonb_array_elements(meals) AS day_meals,
             jsonb_array_elements(day_meals->'meals') AS meal,
             jsonb_array_elements(meal->'foods') AS food
    )
    SELECT
        af.food_name,
        SUM(af.quantity) AS total_quantity,
        af.unit,
        af.category,
        COUNT(DISTINCT af.food_name) AS used_in_days
    FROM all_foods af
    GROUP BY af.food_name, af.unit, af.category
    ORDER BY af.category, af.food_name;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_grocery_list IS 'Generate grocery list from user''s active meal plan';


-- ============================================================================
-- Function: Calculate Adherence Score
-- ============================================================================

CREATE OR REPLACE FUNCTION calculate_adherence_score(
    p_user_id UUID,
    p_days INTEGER DEFAULT 7
)
RETURNS NUMERIC AS $$
DECLARE
    v_meal_adherence NUMERIC;
    v_training_adherence NUMERIC;
    v_overall_score NUMERIC;
BEGIN
    -- Get meal logging adherence
    SELECT
        COUNT(DISTINCT m.created_at::DATE)::NUMERIC / p_days::NUMERIC
    INTO v_meal_adherence
    FROM meals m
    WHERE m.user_id = p_user_id
      AND m.created_at >= CURRENT_DATE - p_days;

    -- Get training adherence
    SELECT
        COUNT(DISTINCT a.created_at::DATE)::NUMERIC /
        (SELECT (plan_data->'training'->>'workouts_per_week')::NUMERIC * (p_days::NUMERIC / 7.0)
         FROM plan_versions
         WHERE user_id = p_user_id AND status = 'active'
         LIMIT 1)
    INTO v_training_adherence
    FROM activities a
    WHERE a.user_id = p_user_id
      AND a.activity_type = 'workout'
      AND a.created_at >= CURRENT_DATE - p_days;

    -- Overall score (weighted: 60% meals, 40% training)
    v_overall_score := (v_meal_adherence * 0.6) + (COALESCE(v_training_adherence, 0) * 0.4);

    RETURN ROUND(v_overall_score, 2);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION calculate_adherence_score IS 'Calculate overall adherence score (0-1) based on meals and training';


-- ============================================================================
-- Grants (adjust based on your RLS setup)
-- ============================================================================

-- Grant execute permissions to authenticated users
GRANT EXECUTE ON FUNCTION get_active_plan TO authenticated;
GRANT EXECUTE ON FUNCTION calculate_today_plan_details TO authenticated;
GRANT EXECUTE ON FUNCTION get_progress_metrics TO authenticated;
GRANT EXECUTE ON FUNCTION is_reassessment_due TO authenticated;
GRANT EXECUTE ON FUNCTION get_plan_history TO authenticated;
GRANT EXECUTE ON FUNCTION get_grocery_list TO authenticated;
GRANT EXECUTE ON FUNCTION calculate_adherence_score TO authenticated;

-- Grant execute on admin functions to service_role only
GRANT EXECUTE ON FUNCTION get_users_due_for_reassessment TO service_role;
GRANT EXECUTE ON FUNCTION mark_plan_superseded TO service_role;


-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- These should already be created in migration, but listing here for reference

CREATE INDEX IF NOT EXISTS idx_plan_versions_user_status
    ON plan_versions(user_id, status);

CREATE INDEX IF NOT EXISTS idx_plan_versions_valid_from
    ON plan_versions(valid_from);

CREATE INDEX IF NOT EXISTS idx_meals_user_date
    ON meals(user_id, ((created_at)::DATE));

CREATE INDEX IF NOT EXISTS idx_activities_user_date
    ON activities(user_id, ((created_at)::DATE));

CREATE INDEX IF NOT EXISTS idx_body_metrics_user_date
    ON body_metrics(user_id, ((recorded_at)::DATE));

CREATE INDEX IF NOT EXISTS idx_plan_adjustments_plan
    ON plan_adjustments(plan_id, to_version);
