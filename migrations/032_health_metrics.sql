-- Migration 032: Health Metrics (HR, Stress, Sleep)
-- Date: 2025-10-15
-- Description: Add flexible health_metrics table for wearable vitals

CREATE TABLE IF NOT EXISTS health_metrics (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  recorded_at TIMESTAMPTZ NOT NULL,
  metric_type TEXT NOT NULL CHECK (metric_type IN ('heart_rate', 'stress', 'sleep')),
  value JSONB NOT NULL DEFAULT '{}',

  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS uniq_health_metrics_user_type_time
  ON health_metrics(user_id, metric_type, recorded_at);

CREATE INDEX IF NOT EXISTS idx_health_metrics_user_time
  ON health_metrics(user_id, recorded_at DESC);

COMMENT ON TABLE health_metrics IS 'Flexible storage for wearable vitals (HR, stress, sleep)';

