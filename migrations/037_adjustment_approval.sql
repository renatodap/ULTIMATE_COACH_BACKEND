-- Migration 037: Adjustment Approval System
-- Date: 2025-10-15
-- Description:
--   Add approval workflow for daily adjustments
--   - User can approve/reject/undo adjustments
--   - Confidence-based auto-apply after grace period
--   - Notification system for pending adjustments
--   - Track user preferences to learn patterns

-- ============================================
-- 1) Modify day_overrides for approval workflow
-- ============================================

-- Add status column to track approval state
ALTER TABLE day_overrides
ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'pending'
  CHECK (status IN ('pending', 'approved', 'rejected', 'auto_applied', 'undone'));

-- Add user override tracking
ALTER TABLE day_overrides
ADD COLUMN IF NOT EXISTS user_overridden BOOLEAN DEFAULT FALSE;

ALTER TABLE day_overrides
ADD COLUMN IF NOT EXISTS override_reason TEXT;

-- Add grace period tracking for auto-apply
ALTER TABLE day_overrides
ADD COLUMN IF NOT EXISTS grace_period_expires_at TIMESTAMPTZ;

-- Add approval/rejection timestamps
ALTER TABLE day_overrides
ADD COLUMN IF NOT EXISTS approved_at TIMESTAMPTZ;

ALTER TABLE day_overrides
ADD COLUMN IF NOT EXISTS rejected_at TIMESTAMPTZ;

ALTER TABLE day_overrides
ADD COLUMN IF NOT EXISTS undone_at TIMESTAMPTZ;

-- ============================================
-- 2) Notifications table for approval requests
-- ============================================

CREATE TABLE IF NOT EXISTS notifications (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,

  -- Notification details
  notification_type TEXT NOT NULL CHECK (notification_type IN (
    'adjustment_pending',
    'adjustment_auto_applied',
    'reassessment_due',
    'reassessment_complete',
    'general'
  )),

  title TEXT NOT NULL,
  message TEXT NOT NULL,

  -- Reference to related entity
  ref_type TEXT CHECK (ref_type IN ('day_override', 'program', 'plan_change_event')),
  ref_id UUID,

  -- Notification state
  read_at TIMESTAMPTZ,
  dismissed_at TIMESTAMPTZ,

  -- Action tracking
  action_taken TEXT CHECK (action_taken IN ('approved', 'rejected', 'undone', 'viewed', 'dismissed')),
  action_taken_at TIMESTAMPTZ,

  -- Metadata
  priority TEXT DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
  expires_at TIMESTAMPTZ,
  metadata JSONB DEFAULT '{}',

  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_notifications_user_created ON notifications(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_user_unread ON notifications(user_id, read_at) WHERE read_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_notifications_user_type ON notifications(user_id, notification_type);

-- Row Level Security
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS notifications_select_own ON notifications;
CREATE POLICY notifications_select_own ON notifications
  FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS notifications_insert_own ON notifications;
CREATE POLICY notifications_insert_own ON notifications
  FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS notifications_update_own ON notifications;
CREATE POLICY notifications_update_own ON notifications
  FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS notifications_delete_own ON notifications;
CREATE POLICY notifications_delete_own ON notifications
  FOR DELETE USING (auth.uid() = user_id);

-- ============================================
-- 3) Adjustment preferences tracking
-- ============================================

CREATE TABLE IF NOT EXISTS adjustment_preferences (
  user_id UUID PRIMARY KEY REFERENCES profiles(id) ON DELETE CASCADE,

  -- Global toggle
  daily_adjustments_enabled BOOLEAN DEFAULT TRUE,

  -- Per-trigger preferences
  poor_sleep_training TEXT DEFAULT 'auto_apply' CHECK (poor_sleep_training IN ('auto_apply', 'ask_me', 'disable')),
  poor_sleep_nutrition TEXT DEFAULT 'auto_apply' CHECK (poor_sleep_nutrition IN ('auto_apply', 'ask_me', 'disable')),

  high_stress_training TEXT DEFAULT 'auto_apply' CHECK (high_stress_training IN ('auto_apply', 'ask_me', 'disable')),
  high_stress_nutrition TEXT DEFAULT 'ask_me' CHECK (high_stress_nutrition IN ('auto_apply', 'ask_me', 'disable')),

  high_soreness_training TEXT DEFAULT 'auto_apply' CHECK (high_soreness_training IN ('auto_apply', 'ask_me', 'disable')),
  high_soreness_nutrition TEXT DEFAULT 'disable' CHECK (high_soreness_nutrition IN ('auto_apply', 'ask_me', 'disable')),

  injury_training TEXT DEFAULT 'ask_me' CHECK (injury_training IN ('auto_apply', 'ask_me', 'disable')),
  injury_nutrition TEXT DEFAULT 'disable' CHECK (injury_nutrition IN ('auto_apply', 'ask_me', 'disable')),

  missed_workout_training TEXT DEFAULT 'disable' CHECK (missed_workout_training IN ('auto_apply', 'ask_me', 'disable')),
  missed_workout_nutrition TEXT DEFAULT 'auto_apply' CHECK (missed_workout_nutrition IN ('auto_apply', 'ask_me', 'disable')),

  low_adherence_training TEXT DEFAULT 'ask_me' CHECK (low_adherence_training IN ('auto_apply', 'ask_me', 'disable')),
  low_adherence_nutrition TEXT DEFAULT 'ask_me' CHECK (low_adherence_nutrition IN ('auto_apply', 'ask_me', 'disable')),

  high_adherence_training TEXT DEFAULT 'auto_apply' CHECK (high_adherence_training IN ('auto_apply', 'ask_me', 'disable')),
  high_adherence_nutrition TEXT DEFAULT 'auto_apply' CHECK (high_adherence_nutrition IN ('auto_apply', 'ask_me', 'disable')),

  -- Grace period for auto-apply (minutes)
  auto_apply_grace_period_minutes INT DEFAULT 120, -- 2 hours

  -- Undo window (hours)
  undo_window_hours INT DEFAULT 24,

  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Row Level Security
ALTER TABLE adjustment_preferences ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS adjustment_preferences_select_own ON adjustment_preferences;
CREATE POLICY adjustment_preferences_select_own ON adjustment_preferences
  FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS adjustment_preferences_insert_own ON adjustment_preferences;
CREATE POLICY adjustment_preferences_insert_own ON adjustment_preferences
  FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS adjustment_preferences_update_own ON adjustment_preferences;
CREATE POLICY adjustment_preferences_update_own ON adjustment_preferences
  FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- ============================================
-- 4) User feedback tracking for ML
-- ============================================

CREATE TABLE IF NOT EXISTS adjustment_feedback (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  day_override_id UUID NOT NULL REFERENCES day_overrides(id) ON DELETE CASCADE,

  -- User action
  action TEXT NOT NULL CHECK (action IN ('approved', 'rejected', 'undone')),

  -- Context at time of feedback
  user_context JSONB DEFAULT '{}', -- Sleep, stress, etc from that day
  adjustment_details JSONB DEFAULT '{}', -- What was suggested

  -- Timing
  time_to_decision_seconds INT, -- How long before user responded

  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_adjustment_feedback_user ON adjustment_feedback(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_adjustment_feedback_override ON adjustment_feedback(day_override_id);

-- Row Level Security
ALTER TABLE adjustment_feedback ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS adjustment_feedback_select_own ON adjustment_feedback;
CREATE POLICY adjustment_feedback_select_own ON adjustment_feedback
  FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS adjustment_feedback_insert_own ON adjustment_feedback;
CREATE POLICY adjustment_feedback_insert_own ON adjustment_feedback
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- ============================================
-- 5) Functions and triggers
-- ============================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_adjustment_preferences_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER adjustment_preferences_updated_at
  BEFORE UPDATE ON adjustment_preferences
  FOR EACH ROW
  EXECUTE FUNCTION update_adjustment_preferences_updated_at();

-- ============================================
-- 6) Comments for documentation
-- ============================================

COMMENT ON TABLE notifications IS 'User notifications for adjustments, reassessments, and general messages';
COMMENT ON TABLE adjustment_preferences IS 'User preferences for daily adjustment approval workflow';
COMMENT ON TABLE adjustment_feedback IS 'Track user approvals/rejections for ML preference learning';

COMMENT ON COLUMN day_overrides.status IS 'pending | approved | rejected | auto_applied | undone';
COMMENT ON COLUMN day_overrides.grace_period_expires_at IS 'When pending adjustment auto-applies (if high confidence)';
COMMENT ON COLUMN notifications.notification_type IS 'Type of notification (adjustment_pending, reassessment_due, etc)';
COMMENT ON COLUMN adjustment_preferences.daily_adjustments_enabled IS 'Global toggle to disable all daily adjustments';
COMMENT ON COLUMN adjustment_preferences.auto_apply_grace_period_minutes IS 'How long to wait before auto-applying high-confidence adjustments';

-- ============================================================================
-- End Migration 037
-- ============================================================================
