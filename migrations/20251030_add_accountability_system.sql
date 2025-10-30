-- ============================================================================
-- ACCOUNTABILITY SYSTEM - Daily Check-ins, Streaks, Notification Preferences
-- ============================================================================
-- Created: 2025-10-30
-- Purpose: Enable daily check-in system with mood/energy/sleep tracking,
--          streak calculation, and notification preference management
-- ============================================================================

-- ============================================================================
-- TABLE: daily_check_ins
-- ============================================================================
-- Stores daily check-in data (mood, energy, sleep, stress, notes)
-- One check-in per user per day (UNIQUE constraint on user_id + date)
-- ============================================================================

CREATE TABLE IF NOT EXISTS daily_check_ins (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Check-in date (user's local date, stored as DATE)
    check_in_date DATE NOT NULL,

    -- Subjective assessments (1-10 scale)
    energy_level INTEGER CHECK (energy_level >= 1 AND energy_level <= 10),
    hunger_level INTEGER CHECK (hunger_level >= 1 AND hunger_level <= 10),
    stress_level INTEGER CHECK (stress_level >= 1 AND stress_level <= 10),
    sleep_quality INTEGER CHECK (sleep_quality >= 1 AND sleep_quality <= 10),
    motivation INTEGER CHECK (motivation >= 1 AND motivation <= 10),

    -- AI-calculated fields
    adherence_score INTEGER CHECK (adherence_score >= 0 AND adherence_score <= 100),
    adaptive_deficit INTEGER,  -- Calorie adjustment based on progress

    -- Optional notes
    notes TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Ensure one check-in per user per day
    UNIQUE (user_id, check_in_date)
);

-- Index for efficient user queries
CREATE INDEX idx_daily_check_ins_user_date ON daily_check_ins(user_id, check_in_date DESC);

-- Row Level Security
ALTER TABLE daily_check_ins ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own check-ins"
    ON daily_check_ins FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own check-ins"
    ON daily_check_ins FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own check-ins"
    ON daily_check_ins FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own check-ins"
    ON daily_check_ins FOR DELETE
    USING (auth.uid() = user_id);


-- ============================================================================
-- TABLE: user_streaks
-- ============================================================================
-- Tracks check-in streaks for gamification
-- Automatically updated via trigger when check-ins are created
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_streaks (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Current streak (consecutive days)
    current_streak INTEGER NOT NULL DEFAULT 0,

    -- Longest streak ever achieved
    longest_streak INTEGER NOT NULL DEFAULT 0,

    -- Last check-in date (to detect streak breaks)
    last_check_in_date DATE,

    -- Total lifetime check-ins
    total_check_ins INTEGER NOT NULL DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Row Level Security
ALTER TABLE user_streaks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own streaks"
    ON user_streaks FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own streaks"
    ON user_streaks FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own streaks"
    ON user_streaks FOR UPDATE
    USING (auth.uid() = user_id);


-- ============================================================================
-- TABLE: notification_preferences
-- ============================================================================
-- User preferences for different notification types
-- One record per user (created on signup or first access)
-- ============================================================================

CREATE TABLE IF NOT EXISTS notification_preferences (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Simple boolean preferences
    daily_check_in_reminders BOOLEAN NOT NULL DEFAULT TRUE,
    meal_logging_reminders BOOLEAN NOT NULL DEFAULT TRUE,
    workout_reminders BOOLEAN NOT NULL DEFAULT TRUE,
    coach_notifications BOOLEAN NOT NULL DEFAULT TRUE,
    streak_notifications BOOLEAN NOT NULL DEFAULT TRUE,
    weekly_summary BOOLEAN NOT NULL DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Row Level Security
ALTER TABLE notification_preferences ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own notification preferences"
    ON notification_preferences FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own notification preferences"
    ON notification_preferences FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own notification preferences"
    ON notification_preferences FOR UPDATE
    USING (auth.uid() = user_id);


-- ============================================================================
-- TRIGGER: Update streak on check-in
-- ============================================================================
-- Automatically updates user_streaks when a daily_check_in is created
-- Calculates:
-- - Current streak (consecutive days)
-- - Longest streak (max ever achieved)
-- - Total check-ins (lifetime count)
-- ============================================================================

CREATE OR REPLACE FUNCTION update_user_streak()
RETURNS TRIGGER AS $$
DECLARE
    v_last_check_in_date DATE;
    v_current_streak INTEGER;
    v_longest_streak INTEGER;
    v_total_check_ins INTEGER;
    v_date_diff INTEGER;
BEGIN
    -- Get existing streak data (if exists)
    SELECT last_check_in_date, current_streak, longest_streak, total_check_ins
    INTO v_last_check_in_date, v_current_streak, v_longest_streak, v_total_check_ins
    FROM user_streaks
    WHERE user_id = NEW.user_id;

    -- Initialize if no streak record exists
    IF NOT FOUND THEN
        INSERT INTO user_streaks (user_id, current_streak, longest_streak, last_check_in_date, total_check_ins)
        VALUES (NEW.user_id, 1, 1, NEW.check_in_date, 1);
        RETURN NEW;
    END IF;

    -- Calculate days since last check-in
    v_date_diff := NEW.check_in_date - v_last_check_in_date;

    -- Update streak logic
    IF v_date_diff = 1 THEN
        -- Consecutive day: increment streak
        v_current_streak := v_current_streak + 1;
    ELSIF v_date_diff = 0 THEN
        -- Same day (update existing check-in): no streak change
        v_current_streak := v_current_streak;
    ELSE
        -- Streak broken: reset to 1
        v_current_streak := 1;
    END IF;

    -- Update longest streak if current exceeds it
    IF v_current_streak > v_longest_streak THEN
        v_longest_streak := v_current_streak;
    END IF;

    -- Increment total check-ins (only if new date)
    IF v_date_diff > 0 THEN
        v_total_check_ins := v_total_check_ins + 1;
    END IF;

    -- Update streak record
    UPDATE user_streaks
    SET
        current_streak = v_current_streak,
        longest_streak = v_longest_streak,
        last_check_in_date = NEW.check_in_date,
        total_check_ins = v_total_check_ins,
        updated_at = NOW()
    WHERE user_id = NEW.user_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach trigger to daily_check_ins table
DROP TRIGGER IF EXISTS trg_update_user_streak ON daily_check_ins;
CREATE TRIGGER trg_update_user_streak
    AFTER INSERT ON daily_check_ins
    FOR EACH ROW
    EXECUTE FUNCTION update_user_streak();


-- ============================================================================
-- COMMENTS (Documentation)
-- ============================================================================

COMMENT ON TABLE daily_check_ins IS 'Daily check-in data: mood, energy, sleep, stress tracking';
COMMENT ON TABLE user_streaks IS 'Check-in streak tracking for gamification';
COMMENT ON TABLE notification_preferences IS 'User notification preferences (reminders, emails, push)';

COMMENT ON COLUMN daily_check_ins.check_in_date IS 'User local date (not UTC timestamp)';
COMMENT ON COLUMN daily_check_ins.energy_level IS 'Energy level (1-10 scale)';
COMMENT ON COLUMN daily_check_ins.hunger_level IS 'Hunger level (1-10 scale)';
COMMENT ON COLUMN daily_check_ins.stress_level IS 'Stress level (1-10 scale)';
COMMENT ON COLUMN daily_check_ins.sleep_quality IS 'Sleep quality (1-10 scale)';
COMMENT ON COLUMN daily_check_ins.motivation IS 'Motivation level (1-10 scale)';
COMMENT ON COLUMN daily_check_ins.adherence_score IS 'AI-calculated adherence (0-100%)';
COMMENT ON COLUMN daily_check_ins.adaptive_deficit IS 'AI-determined calorie adjustment';

COMMENT ON COLUMN user_streaks.current_streak IS 'Current consecutive check-in days';
COMMENT ON COLUMN user_streaks.longest_streak IS 'Longest streak ever achieved';
COMMENT ON COLUMN user_streaks.last_check_in_date IS 'Last check-in date (for streak calculation)';
COMMENT ON COLUMN user_streaks.total_check_ins IS 'Lifetime total check-ins';

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
-- Tables created: daily_check_ins, user_streaks, notification_preferences
-- Trigger created: update_user_streak (auto-updates streaks)
-- RLS enabled: All tables have row-level security policies
-- ============================================================================
