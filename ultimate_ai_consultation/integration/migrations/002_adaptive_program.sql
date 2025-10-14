-- ============================================================================
-- ADAPTIVE PROGRAM SYSTEM - Database Migration
-- ============================================================================
-- Version: 2.0
-- Date: 2025-10-14
-- Description: Adds tables for adaptive program generation, meal planning,
--              context tracking, and reassessment system
--
-- IMPORTANT: This migration DOES NOT duplicate existing workout tables
--            (activity_templates, activities, exercise_sets already exist)
-- ============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- TABLE 1: user_profiles_extended
-- ============================================================================
-- Extends the existing profiles table with program-specific data
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_profiles_extended (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID UNIQUE NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Persona Detection
  persona_type TEXT,  -- '9-to-5 Hustler', 'Busy Parent', etc.
  persona_confidence NUMERIC(3,2) CHECK (persona_confidence >= 0 AND persona_confidence <= 1),
  adaptations TEXT[] DEFAULT ARRAY[]::TEXT[],  -- ['flexible_schedule', 'home_gym', 'short_workouts']

  -- Calculated Metabolic Metrics
  estimated_tdee INTEGER CHECK (estimated_tdee >= 1000 AND estimated_tdee <= 10000),
  bmr INTEGER CHECK (bmr >= 800 AND bmr <= 5000),
  activity_multiplier NUMERIC(3,2) CHECK (activity_multiplier >= 1.0 AND activity_multiplier <= 2.5),

  -- Daily Macro Targets
  daily_calorie_goal INTEGER CHECK (daily_calorie_goal >= 1000 AND daily_calorie_goal <= 10000),
  daily_protein_g INTEGER CHECK (daily_protein_g >= 50 AND daily_protein_g <= 500),
  daily_carbs_g INTEGER CHECK (daily_carbs_g >= 50 AND daily_carbs_g <= 800),
  daily_fat_g INTEGER CHECK (daily_fat_g >= 20 AND daily_fat_g <= 300),

  -- Weekly Targets
  weekly_calorie_deficit INTEGER,  -- Negative for deficit, positive for surplus
  target_weight_change_kg_per_week NUMERIC(4,2),

  -- Program Metadata
  current_program_version INTEGER DEFAULT 1,
  program_start_date TIMESTAMPTZ,
  last_reassessment_date TIMESTAMPTZ,
  next_reassessment_date TIMESTAMPTZ,

  -- Preferences from Consultation
  dietary_restrictions TEXT[] DEFAULT ARRAY[]::TEXT[],
  training_preferences JSONB DEFAULT '{}',
  equipment_available TEXT[] DEFAULT ARRAY[]::TEXT[],

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for user_profiles_extended
CREATE INDEX IF NOT EXISTS idx_profiles_ext_user ON user_profiles_extended(user_id);
CREATE INDEX IF NOT EXISTS idx_profiles_ext_persona ON user_profiles_extended(persona_type);
CREATE INDEX IF NOT EXISTS idx_profiles_ext_next_reassess ON user_profiles_extended(next_reassessment_date)
  WHERE next_reassessment_date IS NOT NULL;

-- RLS for user_profiles_extended
ALTER TABLE user_profiles_extended ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own extended profile"
  ON user_profiles_extended FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update own extended profile"
  ON user_profiles_extended FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own extended profile"
  ON user_profiles_extended FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Comments
COMMENT ON TABLE user_profiles_extended IS 'Extended user profiles with program-specific data (TDEE, macros, persona)';
COMMENT ON COLUMN user_profiles_extended.persona_type IS 'Detected user persona (9-to-5 Hustler, Busy Parent, etc.)';
COMMENT ON COLUMN user_profiles_extended.adaptations IS 'Program adaptations based on persona (flexible_schedule, home_gym, etc.)';
COMMENT ON COLUMN user_profiles_extended.estimated_tdee IS 'Total Daily Energy Expenditure in calories';
COMMENT ON COLUMN user_profiles_extended.bmr IS 'Basal Metabolic Rate (calories at rest)';

-- ============================================================================
-- TABLE 2: meal_plans
-- ============================================================================
-- Stores 14-day meal plans with grocery lists
-- ============================================================================

CREATE TABLE IF NOT EXISTS meal_plans (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Versioning
  plan_version INTEGER NOT NULL DEFAULT 1,

  -- Plan Data (JSONB for flexibility)
  days JSONB NOT NULL,  -- 14 days of meals: [{day: 1, meals: [{type, name, items, macros}]}]
  grocery_list JSONB,  -- Organized by category: {produce: [], proteins: [], grains: []}

  -- Macro Targets (denormalized for quick access)
  target_calories_per_day INTEGER,
  target_protein_g_per_day INTEGER,
  target_carbs_g_per_day INTEGER,
  target_fat_g_per_day INTEGER,

  -- Validity Period
  valid_from TIMESTAMPTZ NOT NULL,
  valid_until TIMESTAMPTZ NOT NULL,
  is_active BOOLEAN DEFAULT TRUE,

  -- Generation Metadata
  generation_prompt TEXT,  -- Stores the prompt used for reproducibility
  ai_model TEXT,  -- e.g., 'claude-3-5-sonnet-20241022'
  generation_cost_usd NUMERIC(10,6) DEFAULT 0,

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for meal_plans
CREATE INDEX IF NOT EXISTS idx_meal_plans_user ON meal_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_meal_plans_user_version ON meal_plans(user_id, plan_version DESC);
CREATE INDEX IF NOT EXISTS idx_meal_plans_active ON meal_plans(user_id, is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_meal_plans_validity ON meal_plans(user_id, valid_from, valid_until);

-- RLS for meal_plans
ALTER TABLE meal_plans ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own meal plans"
  ON meal_plans FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own meal plans"
  ON meal_plans FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own meal plans"
  ON meal_plans FOR UPDATE USING (auth.uid() = user_id);

-- Comments
COMMENT ON TABLE meal_plans IS 'Bi-weekly meal plans with grocery lists';
COMMENT ON COLUMN meal_plans.days IS 'JSONB array of 14 days with breakfast, lunch, dinner, snacks';
COMMENT ON COLUMN meal_plans.grocery_list IS 'Auto-generated shopping list organized by category';

-- ============================================================================
-- TABLE 3: plan_adjustments
-- ============================================================================
-- Tracks all adjustments made during bi-weekly reassessments
-- ============================================================================

CREATE TABLE IF NOT EXISTS plan_adjustments (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Adjustment Metadata
  adjustment_type TEXT NOT NULL CHECK (adjustment_type IN (
    'bi_weekly_reassessment',
    'manual_user_adjustment',
    'injury_adaptation',
    'travel_adaptation',
    'stress_adaptation',
    'goal_change'
  )),

  -- Analysis Results
  adherence_score NUMERIC(4,2) CHECK (adherence_score >= 0 AND adherence_score <= 1),
  context_adjusted_adherence NUMERIC(4,2),

  -- Context Summary
  context_events_detected INTEGER DEFAULT 0,
  informal_activities_count INTEGER DEFAULT 0,

  -- Reasoning (for transparency)
  reason TEXT NOT NULL,  -- Human-readable explanation
  recommendation TEXT NOT NULL,  -- What was recommended

  -- Changes Applied (JSONB for flexibility)
  changes JSONB NOT NULL,  -- {volume_change: -10%, intensity_change: 0, macro_changes: {...}}

  -- Metrics Tracked
  metrics JSONB DEFAULT '{}',  -- {avg_rpe: 7.5, volume_landmarks: [...], weight_change: -1.2}

  -- User Response (did they accept/reject?)
  user_action TEXT CHECK (user_action IN ('accepted', 'rejected', 'modified', 'pending')),
  user_feedback TEXT,

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for plan_adjustments
CREATE INDEX IF NOT EXISTS idx_adjustments_user ON plan_adjustments(user_id);
CREATE INDEX IF NOT EXISTS idx_adjustments_user_date ON plan_adjustments(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_adjustments_type ON plan_adjustments(adjustment_type);

-- RLS for plan_adjustments
ALTER TABLE plan_adjustments ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own adjustments"
  ON plan_adjustments FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own adjustments"
  ON plan_adjustments FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own adjustments"
  ON plan_adjustments FOR UPDATE USING (auth.uid() = user_id);

-- Comments
COMMENT ON TABLE plan_adjustments IS 'History of all program adjustments with reasoning';
COMMENT ON COLUMN plan_adjustments.context_adjusted_adherence IS 'Adherence score adjusted for life context (stress, travel, etc.)';
COMMENT ON COLUMN plan_adjustments.changes IS 'Specific changes applied to program (volume, intensity, macros)';

-- ============================================================================
-- TABLE 4: user_context_log
-- ============================================================================
-- Stores life context extracted from coach chat (stress, travel, energy, etc.)
-- THIS IS THE KEY TO CONTEXT-AWARE COACHING
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_context_log (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Context Type
  context_type TEXT NOT NULL CHECK (context_type IN (
    'stress',
    'energy',
    'sleep',
    'travel',
    'injury',
    'illness',
    'motivation',
    'life_event',
    'informal_activity'
  )),

  -- Severity/Intensity
  severity TEXT CHECK (severity IN ('low', 'moderate', 'high')),

  -- Sentiment Scoring
  sentiment_score NUMERIC(3,2) CHECK (sentiment_score >= -1 AND sentiment_score <= 1),

  -- Description
  description TEXT NOT NULL,
  original_message TEXT,  -- Full original message from chat

  -- Impact Assessment
  affects_training BOOLEAN DEFAULT FALSE,
  affects_nutrition BOOLEAN DEFAULT FALSE,

  -- AI-Generated Suggestion
  suggested_adaptation TEXT,

  -- Extraction Metadata
  extracted_from_message_id UUID,  -- References coach_messages if applicable
  extraction_confidence NUMERIC(3,2) CHECK (extraction_confidence >= 0 AND extraction_confidence <= 1),
  extraction_model TEXT,  -- e.g., 'claude-3-haiku-20240307'

  -- For Informal Activities
  activity_created_id UUID,  -- If this context led to an activity record

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for user_context_log
CREATE INDEX IF NOT EXISTS idx_context_user ON user_context_log(user_id);
CREATE INDEX IF NOT EXISTS idx_context_user_date ON user_context_log(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_context_type ON user_context_log(user_id, context_type);
CREATE INDEX IF NOT EXISTS idx_context_affects ON user_context_log(user_id, affects_training) WHERE affects_training = TRUE;
CREATE INDEX IF NOT EXISTS idx_context_sentiment ON user_context_log(user_id, sentiment_score);

-- RLS for user_context_log
ALTER TABLE user_context_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own context"
  ON user_context_log FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own context"
  ON user_context_log FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Comments
COMMENT ON TABLE user_context_log IS 'Life context extracted from coach chat - enables context-aware coaching';
COMMENT ON COLUMN user_context_log.context_type IS 'Type of context: stress, energy, travel, injury, informal_activity, etc.';
COMMENT ON COLUMN user_context_log.sentiment_score IS 'Sentiment from -1.0 (very negative) to 1.0 (very positive)';
COMMENT ON COLUMN user_context_log.affects_training IS 'Whether this context should affect training adjustments';
COMMENT ON COLUMN user_context_log.suggested_adaptation IS 'AI-generated suggestion for how to adapt program';

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to get users due for reassessment
CREATE OR REPLACE FUNCTION get_users_due_for_reassessment()
RETURNS TABLE (
  user_id UUID,
  days_since_last_reassessment INTEGER,
  next_reassessment_date TIMESTAMPTZ
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    upe.user_id,
    EXTRACT(DAY FROM (NOW() - upe.last_reassessment_date))::INTEGER AS days_since,
    upe.next_reassessment_date
  FROM user_profiles_extended upe
  WHERE
    upe.next_reassessment_date IS NOT NULL
    AND upe.next_reassessment_date <= NOW()
    AND upe.program_start_date IS NOT NULL;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_users_due_for_reassessment IS 'Returns users who need bi-weekly reassessment';

-- Function to get context for a period
CREATE OR REPLACE FUNCTION get_user_context_for_period(
  p_user_id UUID,
  p_days_back INTEGER DEFAULT 14
)
RETURNS TABLE (
  context_type TEXT,
  count INTEGER,
  avg_severity NUMERIC,
  avg_sentiment NUMERIC
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    ucl.context_type,
    COUNT(*)::INTEGER AS count,
    AVG(
      CASE ucl.severity
        WHEN 'low' THEN 1
        WHEN 'moderate' THEN 2
        WHEN 'high' THEN 3
        ELSE NULL
      END
    )::NUMERIC(3,2) AS avg_severity,
    AVG(ucl.sentiment_score)::NUMERIC(3,2) AS avg_sentiment
  FROM user_context_log ucl
  WHERE
    ucl.user_id = p_user_id
    AND ucl.created_at >= NOW() - (p_days_back || ' days')::INTERVAL
  GROUP BY ucl.context_type
  ORDER BY count DESC;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_user_context_for_period IS 'Aggregates user context for a period (default 14 days)';

-- Function to calculate context-adjusted adherence
CREATE OR REPLACE FUNCTION calculate_context_adjusted_adherence(
  p_user_id UUID,
  p_base_adherence NUMERIC,
  p_days_back INTEGER DEFAULT 14
)
RETURNS NUMERIC AS $$
DECLARE
  v_adjusted_adherence NUMERIC;
  v_high_stress_count INTEGER;
  v_travel_count INTEGER;
  v_injury_count INTEGER;
  v_informal_activity_count INTEGER;
BEGIN
  -- Count context events
  SELECT
    COUNT(*) FILTER (WHERE context_type = 'stress' AND severity = 'high'),
    COUNT(*) FILTER (WHERE context_type = 'travel'),
    COUNT(*) FILTER (WHERE context_type IN ('injury', 'illness')),
    COUNT(*) FILTER (WHERE context_type = 'informal_activity')
  INTO
    v_high_stress_count,
    v_travel_count,
    v_injury_count,
    v_informal_activity_count
  FROM user_context_log
  WHERE
    user_id = p_user_id
    AND created_at >= NOW() - (p_days_back || ' days')::INTERVAL;

  -- Start with base adherence
  v_adjusted_adherence := p_base_adherence;

  -- Adjust for high stress (boost by 15%)
  IF v_high_stress_count > 3 THEN
    v_adjusted_adherence := v_adjusted_adherence * 1.15;
  END IF;

  -- Adjust for travel (boost by 20%)
  IF v_travel_count > 0 THEN
    v_adjusted_adherence := v_adjusted_adherence * 1.20;
  END IF;

  -- Adjust for injury/illness (boost by 25%)
  IF v_injury_count > 0 THEN
    v_adjusted_adherence := v_adjusted_adherence * 1.25;
  END IF;

  -- Adjust for informal activities (user is active outside plan, boost by 10%)
  IF v_informal_activity_count > 2 THEN
    v_adjusted_adherence := v_adjusted_adherence * 1.10;
  END IF;

  -- Cap at 1.0 (100%)
  v_adjusted_adherence := LEAST(v_adjusted_adherence, 1.0);

  RETURN v_adjusted_adherence;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION calculate_context_adjusted_adherence IS 'Adjusts adherence score based on life context (stress, travel, injury)';

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_profiles_extended_updated_at
  BEFORE UPDATE ON user_profiles_extended
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_timestamp();

CREATE TRIGGER update_meal_plans_updated_at
  BEFORE UPDATE ON meal_plans
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_timestamp();

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
DECLARE
  missing_tables TEXT[] := ARRAY[]::TEXT[];
  tbl TEXT;
BEGIN
  -- Check all tables exist
  FOR tbl IN SELECT unnest(ARRAY[
    'user_profiles_extended',
    'meal_plans',
    'plan_adjustments',
    'user_context_log'
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

  RAISE NOTICE '===========================================';
  RAISE NOTICE 'Migration 002 completed successfully! ✓';
  RAISE NOTICE '===========================================';
  RAISE NOTICE 'Tables created:';
  RAISE NOTICE '  - user_profiles_extended (persona, TDEE, macros)';
  RAISE NOTICE '  - meal_plans (14-day plans with grocery lists)';
  RAISE NOTICE '  - plan_adjustments (bi-weekly adjustment history)';
  RAISE NOTICE '  - user_context_log (life context tracking)';
  RAISE NOTICE '';
  RAISE NOTICE 'Helper functions created:';
  RAISE NOTICE '  - get_users_due_for_reassessment()';
  RAISE NOTICE '  - get_user_context_for_period()';
  RAISE NOTICE '  - calculate_context_adjusted_adherence()';
  RAISE NOTICE '';
  RAISE NOTICE 'Next steps:';
  RAISE NOTICE '1. Deploy backend context extraction service';
  RAISE NOTICE '2. Deploy persona detection service';
  RAISE NOTICE '3. Update program generation to use activity_templates';
  RAISE NOTICE '4. Test bi-weekly reassessment with context';
  RAISE NOTICE '===========================================';
END $$;

-- ============================================================================
-- SUMMARY
-- ============================================================================
-- ✅ TABLES ADDED (4):
-- 1. user_profiles_extended - Persona, TDEE, macros, adaptations
-- 2. meal_plans - 14-day meal plans with grocery lists
-- 3. plan_adjustments - Bi-weekly adjustment history with reasoning
-- 4. user_context_log - Life context (stress, travel, informal activities)
--
-- ✅ FUNCTIONS ADDED (3):
-- 1. get_users_due_for_reassessment() - Returns users needing reassessment
-- 2. get_user_context_for_period() - Aggregates context for a period
-- 3. calculate_context_adjusted_adherence() - Smart adherence calculation
--
-- ✅ EXISTING TABLES USED (NOT DUPLICATED):
-- - activity_templates (for planned workouts)
-- - activities (for completed workouts)
-- - exercise_sets (for set tracking)
-- - exercises (for exercise library)
-- - activity_template_matches (for adherence tracking)
-- - meals (for meal logging)
-- - body_metrics (for weight/body composition)
-- ============================================================================
