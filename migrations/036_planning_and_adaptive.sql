-- Migration 036: Planning (normalized) + Adaptive Overrides
-- Date: 2025-10-15
-- Description:
--   1) Program + plan instance tables (sessions/meals)
--   2) Adherence and plan change audit
--   3) Day overrides for daily adjustments
--   4) Calendar events (denormalized view table)
--   5) Link actuals to planned (activities/meals)

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================
-- 1) Programs (immutable snapshots)
-- ============================================

CREATE TABLE IF NOT EXISTS programs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  primary_goal TEXT,
  program_start_date DATE,
  program_duration_weeks INT,
  version TEXT DEFAULT '1.0.0',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  valid_until TIMESTAMPTZ,
  next_reassessment_date DATE,
  tdee JSONB DEFAULT '{}',
  macros JSONB DEFAULT '{}',
  safety JSONB DEFAULT '{}',
  feasibility JSONB DEFAULT '{}',
  provenance JSONB DEFAULT '{}',
  full_bundle JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_programs_user ON programs(user_id, created_at DESC);

ALTER TABLE programs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS programs_select_own ON programs;
CREATE POLICY programs_select_own ON programs FOR SELECT USING (auth.uid() = user_id);
DROP POLICY IF EXISTS programs_insert_own ON programs;
CREATE POLICY programs_insert_own ON programs FOR INSERT WITH CHECK (auth.uid() = user_id);

-- ============================================
-- 2) Plan instances (sessions + meals)
-- ============================================

CREATE TABLE IF NOT EXISTS session_instances (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  program_id UUID NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
  week_index INT NOT NULL,
  day_index INT NOT NULL,
  day_of_week TEXT,
  time_of_day TEXT, -- morning|afternoon|evening
  start_hour INT,   -- optional fixed window
  end_hour INT,     -- optional fixed window
  session_kind TEXT NOT NULL, -- resistance|endurance|hiit|sport
  modality TEXT,
  session_name TEXT,
  estimated_duration_minutes INT,
  template_ref UUID,
  parameters_json JSONB DEFAULT '{}', -- intervals/drills or split params
  notes TEXT,
  state TEXT NOT NULL DEFAULT 'planned', -- planned|completed|modified|skipped|superseded
  planned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  modified_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_session_instances_prog_day ON session_instances(program_id, week_index, day_index);

ALTER TABLE session_instances ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS session_instances_select_own ON session_instances;
CREATE POLICY session_instances_select_own ON session_instances FOR SELECT USING (
  auth.uid() = (SELECT user_id FROM programs p WHERE p.id = program_id)
);
DROP POLICY IF EXISTS session_instances_insert_own ON session_instances;
CREATE POLICY session_instances_insert_own ON session_instances FOR INSERT WITH CHECK (
  auth.uid() = (SELECT user_id FROM programs p WHERE p.id = program_id)
);

CREATE TABLE IF NOT EXISTS exercise_plan_items (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_instance_id UUID NOT NULL REFERENCES session_instances(id) ON DELETE CASCADE,
  order_index INT NOT NULL DEFAULT 0,
  name TEXT NOT NULL,
  muscle_groups TEXT[],
  sets INT,
  rep_range TEXT,
  rest_seconds INT,
  rir INT,
  is_compound BOOLEAN,
  notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_exercise_plan_items_session ON exercise_plan_items(session_instance_id);

ALTER TABLE exercise_plan_items ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS exercise_plan_items_select_own ON exercise_plan_items;
CREATE POLICY exercise_plan_items_select_own ON exercise_plan_items FOR SELECT USING (
  auth.uid() = (SELECT p.user_id FROM programs p JOIN session_instances s ON s.program_id = p.id WHERE s.id = session_instance_id)
);

CREATE TABLE IF NOT EXISTS meal_instances (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  program_id UUID NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
  week_index INT NOT NULL,
  day_index INT NOT NULL,
  day_name TEXT,
  order_index INT NOT NULL DEFAULT 0,
  meal_type TEXT,
  meal_name TEXT,
  targets_json JSONB DEFAULT '{}', -- planned macro targets for this meal
  totals_json JSONB DEFAULT '{}',  -- planned totals rollup
  prep_time_minutes INT,
  notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_meal_instances_prog_day ON meal_instances(program_id, week_index, day_index);

ALTER TABLE meal_instances ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS meal_instances_select_own ON meal_instances;
CREATE POLICY meal_instances_select_own ON meal_instances FOR SELECT USING (
  auth.uid() = (SELECT user_id FROM programs p WHERE p.id = program_id)
);

CREATE TABLE IF NOT EXISTS meal_item_plan (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  meal_instance_id UUID NOT NULL REFERENCES meal_instances(id) ON DELETE CASCADE,
  order_index INT NOT NULL DEFAULT 0,
  food_name TEXT NOT NULL,
  serving_size NUMERIC,
  serving_unit TEXT,
  targets_json JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_meal_item_plan_meal ON meal_item_plan(meal_instance_id);

ALTER TABLE meal_item_plan ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS meal_item_plan_select_own ON meal_item_plan;
CREATE POLICY meal_item_plan_select_own ON meal_item_plan FOR SELECT USING (
  auth.uid() = (
    SELECT p.user_id FROM programs p JOIN meal_instances m ON m.program_id = p.id WHERE m.id = meal_instance_id
  )
);

-- ============================================
-- 3) Adherence + Plan Changes + Day Overrides
-- ============================================

CREATE TABLE IF NOT EXISTS adherence_records (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  planned_entity_type TEXT NOT NULL CHECK (planned_entity_type IN ('session','meal')),
  planned_entity_id UUID NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('completed','partial','similar','skipped','unknown')),
  similarity_score NUMERIC,
  adherence_json JSONB DEFAULT '{}',
  actual_ref_type TEXT CHECK (actual_ref_type IN ('activity','meal')),
  actual_ref_id UUID,
  assessed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_adherence_user_time ON adherence_records(user_id, assessed_at DESC);

ALTER TABLE adherence_records ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS adherence_records_select_own ON adherence_records;
CREATE POLICY adherence_records_select_own ON adherence_records FOR SELECT USING (auth.uid() = user_id);
DROP POLICY IF EXISTS adherence_records_insert_own ON adherence_records;
CREATE POLICY adherence_records_insert_own ON adherence_records FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE TABLE IF NOT EXISTS plan_change_events (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  program_id UUID NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  change_type TEXT NOT NULL CHECK (change_type IN ('swap','edit','move','cancel','reschedule')),
  planned_entity_type TEXT NOT NULL CHECK (planned_entity_type IN ('session','meal')),
  planned_entity_id UUID NOT NULL,
  new_entity_id UUID,
  effective_date DATE,
  reason_code TEXT,
  reason_text TEXT,
  diff_json JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_plan_change_events_user_time ON plan_change_events(user_id, created_at DESC);

ALTER TABLE plan_change_events ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS plan_change_events_select_own ON plan_change_events;
CREATE POLICY plan_change_events_select_own ON plan_change_events FOR SELECT USING (auth.uid() = user_id);
DROP POLICY IF EXISTS plan_change_events_insert_own ON plan_change_events;
CREATE POLICY plan_change_events_insert_own ON plan_change_events FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE TABLE IF NOT EXISTS day_overrides (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  override_type TEXT NOT NULL CHECK (override_type IN ('nutrition','training','both')),
  reason_code TEXT,
  reason_details TEXT,
  confidence NUMERIC,
  nutrition_override JSONB,
  training_override JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_day_overrides_user_date ON day_overrides(user_id, date DESC);

ALTER TABLE day_overrides ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS day_overrides_select_own ON day_overrides;
CREATE POLICY day_overrides_select_own ON day_overrides FOR SELECT USING (auth.uid() = user_id);
DROP POLICY IF EXISTS day_overrides_insert_own ON day_overrides;
CREATE POLICY day_overrides_insert_own ON day_overrides FOR INSERT WITH CHECK (auth.uid() = user_id);

-- ============================================
-- 4) Calendar Events (denormalized)
-- ============================================

CREATE TABLE IF NOT EXISTS calendar_events (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  program_id UUID REFERENCES programs(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  start_time_utc TIMESTAMPTZ,
  end_time_utc TIMESTAMPTZ,
  local_tz TEXT,
  event_type TEXT NOT NULL CHECK (event_type IN ('training','multimodal','meal')),
  ref_table TEXT NOT NULL,
  ref_id UUID NOT NULL,
  title TEXT,
  details JSONB DEFAULT '{}',
  status TEXT DEFAULT 'planned', -- planned|completed|similar|skipped|modified
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_calendar_events_user_date ON calendar_events(user_id, date DESC);

ALTER TABLE calendar_events ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS calendar_events_select_own ON calendar_events;
CREATE POLICY calendar_events_select_own ON calendar_events FOR SELECT USING (auth.uid() = user_id);
DROP POLICY IF EXISTS calendar_events_insert_own ON calendar_events;
CREATE POLICY calendar_events_insert_own ON calendar_events FOR INSERT WITH CHECK (auth.uid() = user_id);
DROP POLICY IF EXISTS calendar_events_update_own ON calendar_events;
CREATE POLICY calendar_events_update_own ON calendar_events FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- ============================================
-- 5) Link actuals to planned (activities, meals)
-- ============================================

-- Extend activities with link to planned session and similarity score
ALTER TABLE IF EXISTS activities
  ADD COLUMN IF NOT EXISTS planned_session_instance_id UUID,
  ADD COLUMN IF NOT EXISTS similarity_score NUMERIC;

CREATE INDEX IF NOT EXISTS idx_activities_planned_session ON activities(planned_session_instance_id);

-- Extend meals with link to planned meal and adherence
ALTER TABLE IF EXISTS meals
  ADD COLUMN IF NOT EXISTS planned_meal_instance_id UUID,
  ADD COLUMN IF NOT EXISTS adherence_json JSONB;

CREATE INDEX IF NOT EXISTS idx_meals_planned_meal ON meals(planned_meal_instance_id);

-- ============================================================================
-- End Migration 036
-- ============================================================================

