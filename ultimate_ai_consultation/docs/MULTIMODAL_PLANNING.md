Multimodal Planning (Phase A → Phase B)

Overview
- Phase A (implemented): Optional weekly multimodal sessions (endurance/HIIT/sport) appended to ProgramBundle.
- Phase B (proposed): Persist templates and sessions in DB, extend solver to allocate per-modality with load caps, add adaptive loops.

Suggested DB Schema (Postgres / Supabase)

-- Taxonomy
CREATE TABLE modalities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,                 -- running, cycling, tennis, hiit, strength, rowing, swimming
  category TEXT NOT NULL,             -- endurance | sport | resistance | mobility
  default_load_model TEXT NOT NULL    -- srpe | trimp | none
);

CREATE TABLE session_templates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  modality_id UUID REFERENCES modalities(id) ON DELETE CASCADE,
  session_kind TEXT NOT NULL,         -- endurance | hiit | sport
  difficulty TEXT NOT NULL,           -- beginner | intermediate | advanced
  duration_min INT NOT NULL,
  structure JSONB NOT NULL,           -- e.g., {"intervals":[{"work_min":4,"rest_min":2,"target":"Z4"}]}
  notes TEXT
);

CREATE TABLE drills (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  modality_id UUID REFERENCES modalities(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  tags TEXT[],
  typical_duration_min INT,
  equipment TEXT[],
  coaching_cues TEXT
);

-- User context
CREATE TABLE user_facilities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  facility_type TEXT NOT NULL,        -- court, track, pool, bike, rower, field
  days_available TEXT[] NOT NULL,     -- ["monday","tuesday",...]
  notes TEXT
);

CREATE TABLE user_zones (
  user_id UUID PRIMARY KEY,
  hr_z1 INT, hr_z2 INT, hr_z3 INT, hr_z4 INT, hr_z5 INT,
  ftp_watts INT,
  threshold_pace_sec_per_km INT
);

CREATE TABLE user_modality_preferences (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  modality_id UUID REFERENCES modalities(id),
  priority INT NOT NULL CHECK (priority BETWEEN 1 AND 10),
  target_sessions_per_week INT,
  min_duration_min INT,
  max_duration_min INT,
  facility_needed TEXT,
  intensity_preference TEXT           -- low | moderate | high
);

-- Plans and sessions
CREATE TABLE weekly_plan (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  program_id UUID NOT NULL,
  week_index INT NOT NULL,
  training_load_budget INT,           -- e.g., sum of srpe*min or TRIMP cap
  notes TEXT
);

CREATE TABLE session_plan (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  weekly_plan_id UUID REFERENCES weekly_plan(id) ON DELETE CASCADE,
  day_index INT NOT NULL,             -- 1..7
  session_kind TEXT NOT NULL,         -- resistance | endurance | hiit | sport
  modality_id UUID REFERENCES modalities(id),
  start_time TIME,
  template_ref UUID REFERENCES session_templates(id),
  parameters JSONB                    -- pace targets, intervals, drill selection
);

CREATE TABLE session_step (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_plan_id UUID REFERENCES session_plan(id) ON DELETE CASCADE,
  step_order INT NOT NULL,
  step JSONB NOT NULL                 -- e.g., {"work_min":5,"rest_min":2,"target":"Z4"} or {"drill":"serve"}
);

-- Logging for adaptive adjustments
CREATE TABLE logged_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_plan_id UUID REFERENCES session_plan(id) ON DELETE SET NULL,
  performed_at TIMESTAMP WITH TIME ZONE NOT NULL,
  duration_min INT,
  srpe INT,                           -- 1..10
  avg_hr INT,
  distance_km NUMERIC,
  pace_sec_per_km INT,
  load_score INT,                     -- derived (srpe*min or TRIMP)
  notes TEXT
);

Notes
- Keep resistance planning as-is; this schema augments it for multi-modality.
- Phase B planner can fetch templates and zones to parameterize sessions precisely.
- Adaptive logic can constrain load increases (≤10%/week), detect monotony, and periodize carbs more tightly on high-load days.

