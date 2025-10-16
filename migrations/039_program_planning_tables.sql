-- Migration 039: Program Planning Tables
-- Description: Add program storage, planning, and adaptive system tables
-- Created: 2025-10-16
--
-- This migration adds all tables required for:
-- - Program generation from consultation
-- - Calendar-based plan instances (sessions + meals)
-- - Daily adjustments and overrides
-- - Adherence tracking
-- - Bi-weekly reassessments
-- - Notifications and user context

-- =============================================================================
-- PROGRAMS TABLE
-- =============================================================================
-- Immutable snapshot of generated programs (from consultation or onboarding)
CREATE TABLE IF NOT EXISTS programs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Program metadata
    primary_goal TEXT NOT NULL CHECK (primary_goal IN ('lose_weight', 'build_muscle', 'maintain', 'improve_performance')),
    program_start_date DATE NOT NULL,
    program_duration_weeks INTEGER NOT NULL CHECK (program_duration_weeks BETWEEN 1 AND 52),
    version TEXT NOT NULL DEFAULT '1.0.0',

    -- Dates
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_until TIMESTAMPTZ,
    next_reassessment_date DATE,

    -- TDEE and targets
    tdee JSONB NOT NULL DEFAULT '{}'::jsonb,  -- {tdee_kcal, bmr_kcal, activity_multiplier}
    macros JSONB NOT NULL DEFAULT '{}'::jsonb,  -- {protein_g, carbs_g, fat_g, calories}

    -- Safety and feasibility reports
    safety JSONB DEFAULT '{}'::jsonb,
    feasibility JSONB DEFAULT '{}'::jsonb,
    provenance JSONB DEFAULT '{}'::jsonb,  -- Generation metadata

    -- Full program bundle (backup reference)
    full_bundle JSONB NOT NULL,

    CONSTRAINT programs_user_id_created_at_key UNIQUE (user_id, created_at)
);

-- Indexes for programs
CREATE INDEX IF NOT EXISTS idx_programs_user_id ON programs(user_id);
CREATE INDEX IF NOT EXISTS idx_programs_user_id_created_at ON programs(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_programs_next_reassessment ON programs(user_id, next_reassessment_date)
    WHERE next_reassessment_date IS NOT NULL;

-- RLS for programs
ALTER TABLE programs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own programs"
    ON programs FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own programs"
    ON programs FOR INSERT
    WITH CHECK (auth.uid() = user_id);

COMMENT ON TABLE programs IS 'Immutable program snapshots generated from consultation';
COMMENT ON COLUMN programs.full_bundle IS 'Complete ProgramBundle from generator for reference';


-- =============================================================================
-- SESSION INSTANCES TABLE
-- =============================================================================
-- Planned training sessions (resistance, cardio, multimodal)
CREATE TABLE IF NOT EXISTS session_instances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    program_id UUID NOT NULL REFERENCES programs(id) ON DELETE CASCADE,

    -- Position in program
    week_index INTEGER NOT NULL CHECK (week_index >= 0),
    day_index INTEGER NOT NULL CHECK (day_index BETWEEN 0 AND 6),
    day_of_week TEXT NOT NULL CHECK (day_of_week IN ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')),
    time_of_day TEXT CHECK (time_of_day IN ('morning', 'afternoon', 'evening', 'night')),

    -- Session details
    session_kind TEXT NOT NULL CHECK (session_kind IN ('resistance', 'cardio_steady', 'cardio_interval', 'multimodal', 'flexibility')),
    modality TEXT,  -- For multimodal: 'cycling', 'rowing', etc.
    session_name TEXT NOT NULL,
    estimated_duration_minutes INTEGER CHECK (estimated_duration_minutes > 0),

    -- Parameters (for cardio/multimodal - JSONB for flexibility)
    parameters_json JSONB DEFAULT '{}'::jsonb,

    -- State management
    state TEXT NOT NULL DEFAULT 'planned' CHECK (state IN ('planned', 'superseded', 'archived')),
    notes TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT session_instances_program_week_day_key UNIQUE (program_id, week_index, day_index)
);

-- Indexes for session_instances
CREATE INDEX IF NOT EXISTS idx_session_instances_program ON session_instances(program_id);
CREATE INDEX IF NOT EXISTS idx_session_instances_program_week ON session_instances(program_id, week_index);
CREATE INDEX IF NOT EXISTS idx_session_instances_state ON session_instances(program_id, state);

-- RLS for session_instances
ALTER TABLE session_instances ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own session instances"
    ON session_instances FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM programs
            WHERE programs.id = session_instances.program_id
            AND programs.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert own session instances"
    ON session_instances FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM programs
            WHERE programs.id = session_instances.program_id
            AND programs.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update own session instances"
    ON session_instances FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM programs
            WHERE programs.id = session_instances.program_id
            AND programs.user_id = auth.uid()
        )
    );

COMMENT ON TABLE session_instances IS 'Planned training sessions within programs';


-- =============================================================================
-- EXERCISE PLAN ITEMS TABLE
-- =============================================================================
-- Exercises within resistance training sessions
CREATE TABLE IF NOT EXISTS exercise_plan_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_instance_id UUID NOT NULL REFERENCES session_instances(id) ON DELETE CASCADE,

    -- Exercise details
    order_index INTEGER NOT NULL CHECK (order_index >= 0),
    name TEXT NOT NULL,
    muscle_groups TEXT[] NOT NULL DEFAULT '{}',

    -- Volume prescription
    sets INTEGER NOT NULL CHECK (sets BETWEEN 1 AND 20),
    rep_range TEXT,  -- e.g., "8-10", "12-15", "AMRAP"
    rest_seconds INTEGER CHECK (rest_seconds BETWEEN 30 AND 600),
    rir INTEGER CHECK (rir BETWEEN 0 AND 5),  -- Reps in reserve

    -- Instructions
    notes TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT exercise_plan_items_session_order_key UNIQUE (session_instance_id, order_index)
);

-- Indexes for exercise_plan_items
CREATE INDEX IF NOT EXISTS idx_exercise_plan_items_session ON exercise_plan_items(session_instance_id);
CREATE INDEX IF NOT EXISTS idx_exercise_plan_items_session_order ON exercise_plan_items(session_instance_id, order_index);

-- RLS for exercise_plan_items
ALTER TABLE exercise_plan_items ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own exercise plan items"
    ON exercise_plan_items FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM session_instances si
            JOIN programs p ON p.id = si.program_id
            WHERE si.id = exercise_plan_items.session_instance_id
            AND p.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert own exercise plan items"
    ON exercise_plan_items FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM session_instances si
            JOIN programs p ON p.id = si.program_id
            WHERE si.id = exercise_plan_items.session_instance_id
            AND p.user_id = auth.uid()
        )
    );

COMMENT ON TABLE exercise_plan_items IS 'Exercises within planned resistance training sessions';


-- =============================================================================
-- MEAL INSTANCES TABLE
-- =============================================================================
-- Planned meals within programs
CREATE TABLE IF NOT EXISTS meal_instances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    program_id UUID NOT NULL REFERENCES programs(id) ON DELETE CASCADE,

    -- Position in program
    week_index INTEGER NOT NULL CHECK (week_index >= 0),
    day_index INTEGER NOT NULL CHECK (day_index BETWEEN 0 AND 6),
    order_index INTEGER NOT NULL CHECK (order_index >= 0),  -- Meal number (0=breakfast, 1=lunch, etc.)

    -- Meal details
    meal_type TEXT CHECK (meal_type IN ('breakfast', 'lunch', 'dinner', 'snack', 'pre_workout', 'post_workout')),
    meal_name TEXT NOT NULL,

    -- Nutritional totals
    totals_json JSONB NOT NULL DEFAULT '{}'::jsonb,  -- {calories, protein_g, carbs_g, fat_g}

    notes TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT meal_instances_program_week_day_order_key UNIQUE (program_id, week_index, day_index, order_index)
);

-- Indexes for meal_instances
CREATE INDEX IF NOT EXISTS idx_meal_instances_program ON meal_instances(program_id);
CREATE INDEX IF NOT EXISTS idx_meal_instances_program_week_day ON meal_instances(program_id, week_index, day_index);

-- RLS for meal_instances
ALTER TABLE meal_instances ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own meal instances"
    ON meal_instances FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM programs
            WHERE programs.id = meal_instances.program_id
            AND programs.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert own meal instances"
    ON meal_instances FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM programs
            WHERE programs.id = meal_instances.program_id
            AND programs.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update own meal instances"
    ON meal_instances FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM programs
            WHERE programs.id = meal_instances.program_id
            AND programs.user_id = auth.uid()
        )
    );

COMMENT ON TABLE meal_instances IS 'Planned meals within programs';


-- =============================================================================
-- MEAL ITEM PLAN TABLE
-- =============================================================================
-- Food items within planned meals
CREATE TABLE IF NOT EXISTS meal_item_plan (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meal_instance_id UUID NOT NULL REFERENCES meal_instances(id) ON DELETE CASCADE,

    -- Food details
    order_index INTEGER NOT NULL CHECK (order_index >= 0),
    food_name TEXT NOT NULL,
    serving_size NUMERIC(10, 2) NOT NULL CHECK (serving_size > 0),
    serving_unit TEXT NOT NULL,

    -- Nutritional targets
    targets_json JSONB NOT NULL DEFAULT '{}'::jsonb,  -- {calories, protein_g, carbs_g, fat_g}

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT meal_item_plan_meal_order_key UNIQUE (meal_instance_id, order_index)
);

-- Indexes for meal_item_plan
CREATE INDEX IF NOT EXISTS idx_meal_item_plan_meal ON meal_item_plan(meal_instance_id);

-- RLS for meal_item_plan
ALTER TABLE meal_item_plan ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own meal item plan"
    ON meal_item_plan FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM meal_instances mi
            JOIN programs p ON p.id = mi.program_id
            WHERE mi.id = meal_item_plan.meal_instance_id
            AND p.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert own meal item plan"
    ON meal_item_plan FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM meal_instances mi
            JOIN programs p ON p.id = mi.program_id
            WHERE mi.id = meal_item_plan.meal_instance_id
            AND p.user_id = auth.uid()
        )
    );

COMMENT ON TABLE meal_item_plan IS 'Food items within planned meals';


-- =============================================================================
-- CALENDAR EVENTS TABLE
-- =============================================================================
-- Denormalized unified calendar view (training + meals)
CREATE TABLE IF NOT EXISTS calendar_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    program_id UUID NOT NULL REFERENCES programs(id) ON DELETE CASCADE,

    -- Event details
    date DATE NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN ('training', 'multimodal', 'meal')),

    -- Reference to source
    ref_table TEXT NOT NULL CHECK (ref_table IN ('session_instances', 'meal_instances')),
    ref_id UUID NOT NULL,

    -- Display info
    title TEXT NOT NULL,
    details JSONB DEFAULT '{}'::jsonb,

    -- Status
    status TEXT NOT NULL DEFAULT 'planned' CHECK (status IN ('planned', 'completed', 'skipped', 'rescheduled', 'modified')),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for calendar_events
CREATE INDEX IF NOT EXISTS idx_calendar_events_user_date ON calendar_events(user_id, date);
CREATE INDEX IF NOT EXISTS idx_calendar_events_program ON calendar_events(program_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_ref ON calendar_events(ref_table, ref_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_status ON calendar_events(user_id, status);

-- RLS for calendar_events
ALTER TABLE calendar_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own calendar events"
    ON calendar_events FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own calendar events"
    ON calendar_events FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own calendar events"
    ON calendar_events FOR UPDATE
    USING (auth.uid() = user_id);

COMMENT ON TABLE calendar_events IS 'Denormalized calendar view for unified display';


-- =============================================================================
-- DAY OVERRIDES TABLE
-- =============================================================================
-- Daily adjustments to plan (fatigue, stress, injury, etc.)
CREATE TABLE IF NOT EXISTS day_overrides (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    program_id UUID NOT NULL REFERENCES programs(id) ON DELETE CASCADE,

    date DATE NOT NULL,

    -- Adjustment details
    reason_code TEXT NOT NULL,  -- 'poor_sleep', 'high_stress', 'injury', etc.
    reason_text TEXT,

    -- Modifications (JSONB for flexibility)
    modifications_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    -- Example: {
    --   "calorie_adjustment": -200,
    --   "volume_adjustment": -2,
    --   "session_modification": "reduce_intensity"
    -- }

    -- Status and approval
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'auto_applied', 'undone')),
    user_overridden BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    applied_at TIMESTAMPTZ,

    CONSTRAINT day_overrides_user_program_date_key UNIQUE (user_id, program_id, date)
);

-- Indexes for day_overrides
CREATE INDEX IF NOT EXISTS idx_day_overrides_user_date ON day_overrides(user_id, date);
CREATE INDEX IF NOT EXISTS idx_day_overrides_program ON day_overrides(program_id);
CREATE INDEX IF NOT EXISTS idx_day_overrides_status ON day_overrides(user_id, status);

-- RLS for day_overrides
ALTER TABLE day_overrides ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own day overrides"
    ON day_overrides FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own day overrides"
    ON day_overrides FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own day overrides"
    ON day_overrides FOR UPDATE
    USING (auth.uid() = user_id);

COMMENT ON TABLE day_overrides IS 'Daily plan adjustments based on user context';


-- =============================================================================
-- ADHERENCE RECORDS TABLE
-- =============================================================================
-- Track completion/adherence to planned sessions and meals
CREATE TABLE IF NOT EXISTS adherence_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- What was planned?
    planned_entity_type TEXT NOT NULL CHECK (planned_entity_type IN ('session', 'meal')),
    planned_entity_id UUID NOT NULL,

    -- What actually happened?
    status TEXT NOT NULL CHECK (status IN ('completed', 'similar', 'skipped')),
    actual_ref_type TEXT CHECK (actual_ref_type IN ('activity', 'meal')),  -- References activities or meals table
    actual_ref_id UUID,

    -- Adherence data
    adherence_json JSONB DEFAULT '{}'::jsonb,
    similarity_score NUMERIC(3, 2) CHECK (similarity_score BETWEEN 0 AND 1),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for adherence_records
CREATE INDEX IF NOT EXISTS idx_adherence_records_user ON adherence_records(user_id);
CREATE INDEX IF NOT EXISTS idx_adherence_records_planned ON adherence_records(planned_entity_type, planned_entity_id);
CREATE INDEX IF NOT EXISTS idx_adherence_records_created ON adherence_records(user_id, created_at DESC);

-- RLS for adherence_records
ALTER TABLE adherence_records ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own adherence records"
    ON adherence_records FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own adherence records"
    ON adherence_records FOR INSERT
    WITH CHECK (auth.uid() = user_id);

COMMENT ON TABLE adherence_records IS 'Track plan adherence (completed, similar, skipped)';


-- =============================================================================
-- PLAN CHANGE EVENTS TABLE
-- =============================================================================
-- Audit trail of plan modifications (swaps, edits, cancellations)
CREATE TABLE IF NOT EXISTS plan_change_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    program_id UUID NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- What changed?
    change_type TEXT NOT NULL CHECK (change_type IN ('swap', 'move', 'edit', 'cancel', 'reschedule')),
    planned_entity_type TEXT NOT NULL CHECK (planned_entity_type IN ('session', 'meal')),
    planned_entity_id UUID NOT NULL,
    new_entity_id UUID,

    -- Why?
    reason_code TEXT,  -- 'biweekly_reassessment_nutrition', 'injury', 'schedule_conflict', etc.
    reason_text TEXT,

    -- Details
    diff_json JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for plan_change_events
CREATE INDEX IF NOT EXISTS idx_plan_change_events_program ON plan_change_events(program_id);
CREATE INDEX IF NOT EXISTS idx_plan_change_events_user ON plan_change_events(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_plan_change_events_planned ON plan_change_events(planned_entity_type, planned_entity_id);

-- RLS for plan_change_events
ALTER TABLE plan_change_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own plan change events"
    ON plan_change_events FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own plan change events"
    ON plan_change_events FOR INSERT
    WITH CHECK (auth.uid() = user_id);

COMMENT ON TABLE plan_change_events IS 'Audit trail of plan modifications';


-- =============================================================================
-- USER CONTEXT LOG TABLE
-- =============================================================================
-- Daily user context (sleep, stress, soreness, energy)
CREATE TABLE IF NOT EXISTS user_context_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    date DATE NOT NULL,

    -- Sleep
    sleep_hours NUMERIC(3, 1) CHECK (sleep_hours BETWEEN 0 AND 24),
    sleep_quality INTEGER CHECK (sleep_quality BETWEEN 1 AND 10),

    -- Stress and mood
    stress_level INTEGER CHECK (stress_level BETWEEN 1 AND 10),
    energy_level INTEGER CHECK (energy_level BETWEEN 1 AND 10),

    -- Physical state
    soreness_level INTEGER CHECK (soreness_level BETWEEN 1 AND 10),
    injury_notes TEXT,

    -- General notes
    notes TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT user_context_log_user_date_key UNIQUE (user_id, date)
);

-- Indexes for user_context_log
CREATE INDEX IF NOT EXISTS idx_user_context_log_user_date ON user_context_log(user_id, date DESC);

-- RLS for user_context_log
ALTER TABLE user_context_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own context log"
    ON user_context_log FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own context log"
    ON user_context_log FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own context log"
    ON user_context_log FOR UPDATE
    USING (auth.uid() = user_id);

COMMENT ON TABLE user_context_log IS 'Daily user context for adaptive adjustments';


-- =============================================================================
-- NOTIFICATIONS TABLE
-- =============================================================================
-- System notifications (reassessments, suggestions, warnings)
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Notification details
    notification_type TEXT NOT NULL CHECK (notification_type IN (
        'reassessment_due',
        'adjustment_suggested',
        'program_completed',
        'milestone_reached',
        'warning',
        'info'
    )),

    title TEXT NOT NULL,
    message TEXT NOT NULL,

    -- Action
    action_url TEXT,  -- Where to navigate when clicked
    action_label TEXT,  -- e.g., "View Progress", "Approve", "Dismiss"

    -- Metadata
    metadata_json JSONB DEFAULT '{}'::jsonb,

    -- Status
    read_at TIMESTAMPTZ,
    dismissed_at TIMESTAMPTZ,
    action_taken_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

-- Indexes for notifications
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_unread ON notifications(user_id, read_at) WHERE read_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(user_id, notification_type);

-- RLS for notifications
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own notifications"
    ON notifications FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can update own notifications"
    ON notifications FOR UPDATE
    USING (auth.uid() = user_id);

COMMENT ON TABLE notifications IS 'System notifications for users';


-- =============================================================================
-- GRANTS
-- =============================================================================
-- Grant permissions to authenticated users
GRANT SELECT, INSERT, UPDATE ON programs TO authenticated;
GRANT SELECT, INSERT, UPDATE ON session_instances TO authenticated;
GRANT SELECT, INSERT ON exercise_plan_items TO authenticated;
GRANT SELECT, INSERT, UPDATE ON meal_instances TO authenticated;
GRANT SELECT, INSERT ON meal_item_plan TO authenticated;
GRANT SELECT, INSERT, UPDATE ON calendar_events TO authenticated;
GRANT SELECT, INSERT, UPDATE ON day_overrides TO authenticated;
GRANT SELECT, INSERT ON adherence_records TO authenticated;
GRANT SELECT, INSERT ON plan_change_events TO authenticated;
GRANT SELECT, INSERT, UPDATE ON user_context_log TO authenticated;
GRANT SELECT, UPDATE ON notifications TO authenticated;


-- =============================================================================
-- VALIDATION
-- =============================================================================
-- Verify all tables were created successfully
DO $$
DECLARE
    required_tables TEXT[];
    tbl TEXT;
BEGIN
    required_tables := ARRAY[
        'programs',
        'session_instances',
        'exercise_plan_items',
        'meal_instances',
        'meal_item_plan',
        'calendar_events',
        'day_overrides',
        'adherence_records',
        'plan_change_events',
        'user_context_log',
        'notifications'
    ];

    FOREACH tbl IN ARRAY required_tables
    LOOP
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = tbl
        ) THEN
            RAISE EXCEPTION 'Table % was not created', tbl;
        END IF;
    END LOOP;

    RAISE NOTICE 'Migration 039 completed successfully - all 11 tables created';
END $$;
