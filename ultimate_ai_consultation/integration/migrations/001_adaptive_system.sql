-- ============================================================================
-- ULTIMATE AI CONSULTATION - Adaptive System Migration
-- ============================================================================
-- Version: 1.0.0
-- Created: 2025-10-13
-- Description: Adds adaptive program generation, feasibility checking, and
--              confidence tracking to existing ULTIMATE COACH system
--
-- CHANGES:
-- 1. New tables: plan_versions, feasibility_checks, plan_adjustments
-- 2. Enhanced tables: Add confidence columns to meals, activities, body_metrics
-- 3. Indexes for performance
-- 4. RLS policies
-- ============================================================================

-- ============================================================================
-- 1. PLAN_VERSIONS - Generated Programs
-- ============================================================================
-- Stores complete generated programs with training + nutrition plans
-- Immutable history - new versions created on adjustments

CREATE TABLE IF NOT EXISTS plan_versions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Version tracking
  version_number INTEGER NOT NULL CHECK (version_number >= 1),
  parent_version_id UUID REFERENCES plan_versions(id) ON DELETE SET NULL,  -- For tracking adjustments

  -- Status
  status TEXT CHECK (status IN ('draft', 'active', 'completed', 'archived')) DEFAULT 'draft',
  activated_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  archived_at TIMESTAMPTZ,

  -- Source data
  consultation_session_id UUID REFERENCES consultation_sessions(id) ON DELETE SET NULL,
  feasibility_check_id UUID,  -- Foreign key added after feasibility_checks table

  -- Goals & Timeline (snapshot at generation time)
  primary_goal TEXT,
  target_metrics JSONB DEFAULT '{}',  -- e.g., {"weight_kg": 80, "bf_percent": 12}
  timeline_weeks INTEGER,
  deadline_date DATE,

  -- Plan Parameters (from solver)
  plan_params JSONB NOT NULL,  -- Complete parameter set from solver
  -- Example: {
  --   "training": {
  --     "split": "upper_lower_4x",
  --     "sessions_per_week": 4,
  --     "session_duration_minutes": 60,
  --     "volume_targets_sets": {"chest": 14, "back": 14, ...}
  --   },
  --   "nutrition": {
  --     "calories": 2500,
  --     "protein_g": 180,
  --     "carbs_g": 280,
  --     "fat_g": 75,
  --     "meal_frequency": 4
  --   }
  -- }

  -- Generated Program (complete 14-day plan)
  training_program JSONB NOT NULL,  -- Day-by-day workouts
  -- Example: [
  --   {
  --     "date": "2025-10-20",
  --     "day_name": "Upper Body",
  --     "exercises": [
  --       {"exercise_id": "uuid", "sets": 4, "reps": "6-8", "rir": 2, "rest_seconds": 180}
  --     ]
  --   }
  -- ]

  nutrition_program JSONB NOT NULL,  -- Day-by-day meals
  -- Example: [
  --   {
  --     "date": "2025-10-20",
  --     "meals": [
  --       {"time": "08:00", "name": "Breakfast", "foods": [...], "macros": {...}}
  --     ],
  --     "daily_totals": {"calories": 2500, "protein_g": 180, ...}
  --   }
  -- ]

  -- Rationale & Explainability
  rationale TEXT,  -- Why this plan was recommended
  assumptions JSONB DEFAULT '[]',  -- List of assumptions made
  -- Example: ["TDEE estimated at 2700±150 kcal", "User confident in weight tracking (95%)"]

  alternatives_considered JSONB DEFAULT '[]',  -- Other options that were rejected and why

  -- Confidence Scores
  confidence JSONB DEFAULT '{}',
  -- Example: {
  --   "tdee": 0.80,
  --   "adherence_prediction": 0.85,
  --   "goal_achievability": 0.90
  -- }

  -- Cost tracking
  generation_cost_usd NUMERIC(10, 6) DEFAULT 0.0,
  ai_provider TEXT,
  ai_model TEXT,

  -- Metadata
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  -- Constraint: version numbers must be unique per user
  UNIQUE (user_id, version_number)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_plan_versions_user_id ON plan_versions (user_id);
CREATE INDEX IF NOT EXISTS idx_plan_versions_status ON plan_versions (user_id, status) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_plan_versions_created_at ON plan_versions (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_plan_versions_parent ON plan_versions (parent_version_id) WHERE parent_version_id IS NOT NULL;

-- RLS
ALTER TABLE plan_versions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own plan versions"
  ON plan_versions FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "System can insert plan versions"
  ON plan_versions FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own plan versions"
  ON plan_versions FOR UPDATE USING (auth.uid() = user_id);

-- ============================================================================
-- 2. FEASIBILITY_CHECKS - Solver Results
-- ============================================================================
-- Stores constraint solver validation results

CREATE TABLE IF NOT EXISTS feasibility_checks (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  consultation_session_id UUID REFERENCES consultation_sessions(id) ON DELETE SET NULL,

  -- Input data (snapshot)
  goals JSONB NOT NULL,
  constraints_hard JSONB NOT NULL,
  constraints_soft JSONB DEFAULT '{}',
  baseline JSONB NOT NULL,

  -- Solver result
  is_feasible BOOLEAN NOT NULL,
  solver_runtime_ms INTEGER,
  solver_iterations INTEGER,

  -- If feasible: optimal parameters
  optimal_params JSONB,  -- Same structure as plan_versions.plan_params

  -- If infeasible: diagnostics and trade-offs
  infeasibility_diagnostics JSONB DEFAULT '[]',
  -- Example: [
  --   {
  --     "code": "FREQ_TOO_LOW",
  --     "constraint": "sessions_per_week >= 4",
  --     "detail": "2x/week insufficient for target muscle gain rate"
  --   }
  -- ]

  trade_offs JSONB DEFAULT '[]',  -- A/B/C options
  -- Example: [
  --   {
  --     "id": "A",
  --     "summary": "Keep 2x/week; slower gain",
  --     "adjustments": {"sessions_per_week": 2},
  --     "expected_outcomes": {"muscle_gain_8w_kg": [0.5, 1.5]},
  --     "trade_off": "Slower progress"
  --   },
  --   {
  --     "id": "B",
  --     "summary": "Increase to 4x/week; keep pace",
  --     "adjustments": {"sessions_per_week": 4},
  --     "expected_outcomes": {"muscle_gain_8w_kg": [2, 3]},
  --     "trade_off": "More time commitment"
  --   }
  -- ]

  user_selected_trade_off TEXT,  -- "A", "B", "C", or NULL if feasible

  -- Metadata
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_feasibility_checks_user_id ON feasibility_checks (user_id);
CREATE INDEX IF NOT EXISTS idx_feasibility_checks_session ON feasibility_checks (consultation_session_id);
CREATE INDEX IF NOT EXISTS idx_feasibility_checks_feasible ON feasibility_checks (is_feasible);

-- RLS
ALTER TABLE feasibility_checks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own feasibility checks"
  ON feasibility_checks FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "System can insert feasibility checks"
  ON feasibility_checks FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Add foreign key from plan_versions to feasibility_checks
ALTER TABLE plan_versions
  ADD CONSTRAINT fk_plan_versions_feasibility_check
  FOREIGN KEY (feasibility_check_id)
  REFERENCES feasibility_checks(id)
  ON DELETE SET NULL;

-- ============================================================================
-- 3. PLAN_ADJUSTMENTS - Adaptive Loop Modifications
-- ============================================================================
-- Tracks changes made during bi-weekly reassessments

CREATE TABLE IF NOT EXISTS plan_adjustments (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Which plan version was adjusted
  from_plan_version_id UUID NOT NULL REFERENCES plan_versions(id) ON DELETE CASCADE,
  to_plan_version_id UUID REFERENCES plan_versions(id) ON DELETE CASCADE,  -- Set after new plan generated

  -- When this adjustment was made
  adjustment_date DATE NOT NULL DEFAULT CURRENT_DATE,
  days_since_last_adjustment INTEGER,

  -- Input data for adjustment (last 14 days)
  adherence_metrics JSONB NOT NULL,
  -- Example: {
  --   "meals_logged_percent": 79,
  --   "training_completed_percent": 87,
  --   "calorie_adherence_percent": 95,
  --   "macro_adherence_percent": 92
  -- }

  biometric_trends JSONB NOT NULL,
  -- Example: {
  --   "weight_change_kg": -0.6,
  --   "weight_trend_kg_per_week": -0.3,
  --   "weight_target_kg_per_week": -0.5,
  --   "sleep_avg_hours": 7.2,
  --   "hrv_trend_percent": -5.0,
  --   "rhr_trend_bpm": +2.0
  -- }

  performance_markers JSONB DEFAULT '{}',
  -- Example: {
  --   "strength_change_percent": +3.5,
  --   "rpe_avg": 7.8,
  --   "volume_completed_percent": 94
  -- }

  sentiment_analysis JSONB DEFAULT '{}',
  -- Example: {
  --   "overall_sentiment": "positive",
  --   "energy_mentions": ["tired twice", "felt strong 3x"],
  --   "constraint_changes_detected": false
  -- }

  -- Adjustments made
  adjustments JSONB NOT NULL,
  -- Example: {
  --   "calories": {
  --     "old": 2500,
  --     "new": 2420,
  --     "change": -80,
  --     "reason": "Weight loss slower than target"
  --   },
  --   "volume": {
  --     "old_sets": {"chest": 14},
  --     "new_sets": {"chest": 16},
  --     "reason": "Progressive overload, recovery markers good"
  --   },
  --   "deload_triggered": false
  -- }

  adjustment_type TEXT CHECK (adjustment_type IN (
    'scheduled_reassessment',  -- Normal 14-day check
    'early_intervention',      -- User request or problem detected
    'deload',                  -- Forced recovery
    'constraint_change',       -- Travel, injury, schedule change
    'milestone_reached'        -- Goal achieved, pivot to next phase
  )),

  -- Rationale
  rationale TEXT NOT NULL,  -- Why these adjustments were made
  warnings JSONB DEFAULT '[]',  -- Any concerns flagged
  -- Example: ["Adherence <70%, consider simplifying meals", "HRV declining, watch for overtraining"]

  -- Metadata
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_plan_adjustments_user_id ON plan_adjustments (user_id);
CREATE INDEX IF NOT EXISTS idx_plan_adjustments_from_plan ON plan_adjustments (from_plan_version_id);
CREATE INDEX IF NOT EXISTS idx_plan_adjustments_date ON plan_adjustments (user_id, adjustment_date DESC);
CREATE INDEX IF NOT EXISTS idx_plan_adjustments_type ON plan_adjustments (adjustment_type);

-- RLS
ALTER TABLE plan_adjustments ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own plan adjustments"
  ON plan_adjustments FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "System can insert plan adjustments"
  ON plan_adjustments FOR INSERT WITH CHECK (auth.uid() = user_id);

-- ============================================================================
-- 4. ENHANCE EXISTING TABLES - Add Confidence Tracking
-- ============================================================================

-- Meals: Add confidence tracking
ALTER TABLE meals
  ADD COLUMN IF NOT EXISTS confidence NUMERIC(3,2) CHECK (confidence >= 0 AND confidence <= 1),
  ADD COLUMN IF NOT EXISTS data_source TEXT CHECK (data_source IN ('manual', 'ai_text', 'ai_voice', 'ai_photo', 'coach_chat', 'quick_entry')),
  ADD COLUMN IF NOT EXISTS ci_lower_kcal NUMERIC(10,2),  -- Confidence interval lower bound
  ADD COLUMN IF NOT EXISTS ci_upper_kcal NUMERIC(10,2);  -- Confidence interval upper bound

COMMENT ON COLUMN meals.confidence IS 'Statistical confidence in logged data (0.0-1.0). <0.70 = flag for clarification';
COMMENT ON COLUMN meals.data_source IS 'How this meal was logged (for tracking data quality)';
COMMENT ON COLUMN meals.ci_lower_kcal IS 'Lower bound of calorie estimate confidence interval';
COMMENT ON COLUMN meals.ci_upper_kcal IS 'Upper bound of calorie estimate confidence interval';

-- Activities: Add confidence tracking
ALTER TABLE activities
  ADD COLUMN IF NOT EXISTS confidence NUMERIC(3,2) CHECK (confidence >= 0 AND confidence <= 1),
  ADD COLUMN IF NOT EXISTS data_source_type TEXT CHECK (data_source_type IN ('manual', 'ai_text', 'ai_voice', 'wearable', 'coach_chat', 'quick_entry')),
  ADD COLUMN IF NOT EXISTS ci_lower_calories INTEGER,
  ADD COLUMN IF NOT EXISTS ci_upper_calories INTEGER;

COMMENT ON COLUMN activities.confidence IS 'Statistical confidence in logged data (0.0-1.0). Wearable=0.98, AI=0.70-0.85';
COMMENT ON COLUMN activities.data_source_type IS 'How this activity was logged';

-- Body Metrics: Add confidence tracking (if table doesn't exist, create it)
CREATE TABLE IF NOT EXISTS body_metrics (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Measurements
  recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  weight_kg NUMERIC(5,2),
  body_fat_percentage NUMERIC(4,2),
  muscle_mass_kg NUMERIC(5,2),
  waist_cm NUMERIC(5,2),
  chest_cm NUMERIC(5,2),
  arms_cm NUMERIC(5,2),
  legs_cm NUMERIC(5,2),

  -- Physiological markers (from wearables)
  resting_heart_rate INTEGER,
  hrv_ms INTEGER,  -- Heart rate variability
  sleep_hours NUMERIC(3,1),
  sleep_quality_score INTEGER CHECK (sleep_quality_score >= 0 AND sleep_quality_score <= 100),

  -- Confidence tracking
  confidence NUMERIC(3,2) CHECK (confidence >= 0 AND confidence <= 1),
  data_source TEXT CHECK (data_source IN ('manual', 'scale_sync', 'wearable', 'dexa_scan', 'coach_chat')),

  -- Notes
  notes TEXT,

  -- Metadata
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for body_metrics
CREATE INDEX IF NOT EXISTS idx_body_metrics_user_id ON body_metrics (user_id);
CREATE INDEX IF NOT EXISTS idx_body_metrics_recorded_at ON body_metrics (user_id, recorded_at DESC);

-- RLS for body_metrics
ALTER TABLE body_metrics ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own body metrics" ON body_metrics FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own body metrics" ON body_metrics FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own body metrics" ON body_metrics FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own body metrics" ON body_metrics FOR DELETE USING (auth.uid() = user_id);

-- ============================================================================
-- 5. HELPER FUNCTIONS
-- ============================================================================

-- Function to get active plan for user
CREATE OR REPLACE FUNCTION get_active_plan(p_user_id UUID)
RETURNS SETOF plan_versions
LANGUAGE sql
STABLE
AS $$
  SELECT *
  FROM plan_versions
  WHERE user_id = p_user_id
    AND status = 'active'
  ORDER BY version_number DESC
  LIMIT 1;
$$;

-- Function to get plan history
CREATE OR REPLACE FUNCTION get_plan_history(p_user_id UUID)
RETURNS TABLE (
  version_number INTEGER,
  status TEXT,
  activated_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  primary_goal TEXT,
  adjustments_count BIGINT
)
LANGUAGE sql
STABLE
AS $$
  SELECT
    pv.version_number,
    pv.status,
    pv.activated_at,
    pv.completed_at,
    pv.primary_goal,
    COUNT(pa.id) as adjustments_count
  FROM plan_versions pv
  LEFT JOIN plan_adjustments pa ON pa.from_plan_version_id = pv.id
  WHERE pv.user_id = p_user_id
  GROUP BY pv.id, pv.version_number, pv.status, pv.activated_at, pv.completed_at, pv.primary_goal
  ORDER BY pv.version_number DESC;
$$;

-- Function to calculate adherence metrics for date range
CREATE OR REPLACE FUNCTION calculate_adherence_metrics(
  p_user_id UUID,
  p_start_date DATE,
  p_end_date DATE
)
RETURNS JSONB
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
  result JSONB;
  meals_count INTEGER;
  activities_count INTEGER;
  days_count INTEGER;
BEGIN
  days_count := p_end_date - p_start_date + 1;

  -- Count meals logged
  SELECT COUNT(*) INTO meals_count
  FROM meals
  WHERE user_id = p_user_id
    AND logged_at::DATE BETWEEN p_start_date AND p_end_date;

  -- Count activities logged
  SELECT COUNT(*) INTO activities_count
  FROM activities
  WHERE user_id = p_user_id
    AND start_time::DATE BETWEEN p_start_date AND p_end_date;

  -- Build JSON result
  result := jsonb_build_object(
    'period_days', days_count,
    'meals_logged', meals_count,
    'activities_logged', activities_count,
    'meals_per_day', ROUND(meals_count::NUMERIC / days_count, 2),
    'activities_per_week', ROUND(activities_count::NUMERIC / days_count * 7, 2)
  );

  RETURN result;
END;
$$;

-- ============================================================================
-- 6. TRIGGERS
-- ============================================================================

CREATE TRIGGER update_plan_versions_updated_at
  BEFORE UPDATE ON plan_versions
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_body_metrics_updated_at
  BEFORE UPDATE ON body_metrics
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================================
-- SUMMARY
-- ============================================================================
-- ✅ NEW TABLES:
-- 1. plan_versions: Complete generated programs with training + nutrition
-- 2. feasibility_checks: Constraint solver validation results
-- 3. plan_adjustments: Bi-weekly reassessment modifications
-- 4. body_metrics: Enhanced tracking with confidence intervals
--
-- ✅ ENHANCED TABLES:
-- 1. meals: Added confidence, data_source, CI bounds
-- 2. activities: Added confidence, data_source_type, CI bounds
--
-- ✅ HELPER FUNCTIONS:
-- 1. get_active_plan(user_id): Get current active plan
-- 2. get_plan_history(user_id): Plan version history
-- 3. calculate_adherence_metrics(user_id, start, end): Adherence stats
--
-- NEXT STEPS:
-- 1. Run this migration in ULTIMATE_COACH_BACKEND database
-- 2. Update backend services to populate confidence fields
-- 3. Build solver, programmer, and adaptive services
-- ============================================================================
