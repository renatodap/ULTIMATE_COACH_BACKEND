-- Migration 031: Wearables Integration (accounts + sync jobs + dedupe)
-- Date: 2025-10-15
-- Description:
--   1. Create wearable_accounts and wearable_sync_jobs tables
--   2. Add unique index for activities de-duplication by wearable_activity_id
--   3. Prepare schema for multi-provider wearable ingestion

-- ============================================
-- 1) Wearable Accounts
-- ============================================

CREATE TABLE IF NOT EXISTS wearable_accounts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  provider TEXT NOT NULL CHECK (provider IN ('garmin', 'strava', 'apple_health', 'fitbit', 'oura', 'polar')),
  status TEXT NOT NULL DEFAULT 'disconnected' CHECK (status IN (
    'connected', 'disconnected', 'error', 'configured_missing_secret'
  )),
  device_name TEXT,
  last_sync_at TIMESTAMPTZ,
  error_code TEXT,
  error_message TEXT,

  -- Encrypted credential blob (symmetric encryption)
  credentials_encrypted TEXT,
  token_expires_at TIMESTAMPTZ,

  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),

  CONSTRAINT wearable_accounts_user_provider_unique UNIQUE (user_id, provider)
);

CREATE INDEX IF NOT EXISTS idx_wearable_accounts_user ON wearable_accounts(user_id);

COMMENT ON TABLE wearable_accounts IS 'Per-user wearable provider connection state and credentials';

-- ============================================
-- 2) Sync Jobs
-- ============================================

CREATE TABLE IF NOT EXISTS wearable_sync_jobs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  provider TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'success', 'error')),
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  stats JSONB DEFAULT '{}',
  error_message TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_wearable_sync_jobs_user ON wearable_sync_jobs(user_id, created_at DESC);

COMMENT ON TABLE wearable_sync_jobs IS 'Wearable sync job audit log with stats and errors';

-- ============================================
-- 3) Activities de-duplication by wearable id
-- ============================================

-- Ensure we don't create duplicate activities for same wearable activity id
CREATE UNIQUE INDEX IF NOT EXISTS uniq_activities_user_wearable
ON activities(user_id, wearable_activity_id)
WHERE wearable_activity_id IS NOT NULL AND deleted_at IS NULL;

COMMENT ON INDEX uniq_activities_user_wearable IS 'Prevents duplicate wearable activities per user';

