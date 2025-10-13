-- ============================================================================
-- Migration 021: Quick Entry Logs
-- ============================================================================
-- Created: 2025-10-12
-- Description: Track auto-detected logs from coach conversations
--
-- FEATURES:
-- 1. Pending/confirmed/cancelled status tracking
-- 2. Links to actual meal/activity/measurement records
-- 3. AI cost tracking
-- 4. Analytics for log detection accuracy
-- ============================================================================

CREATE TABLE IF NOT EXISTS quick_entry_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Conversation context
  conversation_id UUID REFERENCES coach_conversations(id) ON DELETE SET NULL,
  message_id UUID REFERENCES coach_messages(id) ON DELETE SET NULL,

  -- Classification
  log_type TEXT NOT NULL CHECK (log_type IN ('meal', 'activity', 'measurement')),
  original_text TEXT NOT NULL,
  confidence NUMERIC(3,2) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),

  -- Parsed data (before confirmation)
  structured_data JSONB NOT NULL,

  -- Linked records (after confirmation)
  meal_id UUID REFERENCES meals(id) ON DELETE SET NULL,
  activity_id UUID REFERENCES activities(id) ON DELETE SET NULL,
  -- measurement_id UUID REFERENCES body_measurements(id) ON DELETE SET NULL, -- TODO: Add when table exists

  -- Status tracking
  status TEXT NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'confirmed', 'cancelled', 'failed')),
  confirmed_at TIMESTAMPTZ,
  cancelled_at TIMESTAMPTZ,
  failure_reason TEXT,

  -- AI metadata
  classifier_model TEXT DEFAULT 'llama-3.3-70b-versatile',
  classifier_cost_usd NUMERIC(10, 6) DEFAULT 0.0001,
  extraction_model TEXT,
  extraction_cost_usd NUMERIC(10, 6) DEFAULT 0,

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_quick_entry_user ON quick_entry_logs(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_quick_entry_status ON quick_entry_logs(user_id, status) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_quick_entry_conversation ON quick_entry_logs(conversation_id);
CREATE INDEX IF NOT EXISTS idx_quick_entry_type ON quick_entry_logs(log_type, status);

-- RLS
ALTER TABLE quick_entry_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own logs"
  ON quick_entry_logs FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can create own logs"
  ON quick_entry_logs FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own logs"
  ON quick_entry_logs FOR UPDATE
  USING (auth.uid() = user_id);

-- Trigger for updated_at
CREATE TRIGGER update_quick_entry_logs_updated_at
  BEFORE UPDATE ON quick_entry_logs
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();

-- ============================================================================
-- ANALYTICS FUNCTION
-- ============================================================================
CREATE OR REPLACE FUNCTION get_quick_entry_stats(
  p_user_id UUID,
  p_days INT DEFAULT 30
)
RETURNS TABLE (
  total_logs INT,
  confirmed_logs INT,
  cancelled_logs INT,
  pending_logs INT,
  avg_confidence NUMERIC,
  meal_logs INT,
  activity_logs INT,
  measurement_logs INT,
  confirmation_rate NUMERIC
)
LANGUAGE sql STABLE
AS $$
  SELECT
    COUNT(*)::INT AS total_logs,
    COUNT(*) FILTER (WHERE status = 'confirmed')::INT AS confirmed_logs,
    COUNT(*) FILTER (WHERE status = 'cancelled')::INT AS cancelled_logs,
    COUNT(*) FILTER (WHERE status = 'pending')::INT AS pending_logs,
    ROUND(AVG(confidence)::NUMERIC, 2) AS avg_confidence,
    COUNT(*) FILTER (WHERE log_type = 'meal')::INT AS meal_logs,
    COUNT(*) FILTER (WHERE log_type = 'activity')::INT AS activity_logs,
    COUNT(*) FILTER (WHERE log_type = 'measurement')::INT AS measurement_logs,
    ROUND(
      (COUNT(*) FILTER (WHERE status = 'confirmed')::NUMERIC /
       NULLIF(COUNT(*) FILTER (WHERE status IN ('confirmed', 'cancelled'))::NUMERIC, 0)) * 100,
      1
    ) AS confirmation_rate
  FROM quick_entry_logs
  WHERE user_id = p_user_id
    AND created_at > NOW() - (p_days || ' days')::INTERVAL;
$$;

COMMENT ON FUNCTION get_quick_entry_stats IS
  'Get analytics for quick entry logs (detection accuracy, confirmation rates, etc.)';
