-- ============================================================================
-- Migration 033: Wearables RLS & Policies + updated_at trigger
-- Date: 2025-10-15
-- Description:
--   1) Enable Row Level Security on wearable tables
--   2) Add per-user RLS policies (SELECT/INSERT/UPDATE/DELETE)
--   3) Add updated_at trigger on wearable_accounts
-- ============================================================================

-- Optional extensions (usually enabled in Supabase projects)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================
-- wearable_accounts
-- ============================================

ALTER TABLE IF EXISTS wearable_accounts ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS wearable_accounts_select_own ON wearable_accounts;
CREATE POLICY wearable_accounts_select_own
ON wearable_accounts FOR SELECT
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS wearable_accounts_insert_own ON wearable_accounts;
CREATE POLICY wearable_accounts_insert_own
ON wearable_accounts FOR INSERT
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS wearable_accounts_update_own ON wearable_accounts;
CREATE POLICY wearable_accounts_update_own
ON wearable_accounts FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS wearable_accounts_delete_own ON wearable_accounts;
CREATE POLICY wearable_accounts_delete_own
ON wearable_accounts FOR DELETE
USING (auth.uid() = user_id);

-- updated_at trigger
CREATE OR REPLACE FUNCTION update_wearable_accounts_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS wearable_accounts_updated_at ON wearable_accounts;
CREATE TRIGGER wearable_accounts_updated_at
BEFORE UPDATE ON wearable_accounts
FOR EACH ROW EXECUTE FUNCTION update_wearable_accounts_updated_at();

-- ============================================
-- wearable_sync_jobs
-- ============================================

ALTER TABLE IF EXISTS wearable_sync_jobs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS wearable_sync_jobs_select_own ON wearable_sync_jobs;
CREATE POLICY wearable_sync_jobs_select_own
ON wearable_sync_jobs FOR SELECT
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS wearable_sync_jobs_insert_own ON wearable_sync_jobs;
CREATE POLICY wearable_sync_jobs_insert_own
ON wearable_sync_jobs FOR INSERT
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS wearable_sync_jobs_update_own ON wearable_sync_jobs;
CREATE POLICY wearable_sync_jobs_update_own
ON wearable_sync_jobs FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS wearable_sync_jobs_delete_own ON wearable_sync_jobs;
CREATE POLICY wearable_sync_jobs_delete_own
ON wearable_sync_jobs FOR DELETE
USING (auth.uid() = user_id);

-- ============================================
-- health_metrics
-- ============================================

ALTER TABLE IF EXISTS health_metrics ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS health_metrics_select_own ON health_metrics;
CREATE POLICY health_metrics_select_own
ON health_metrics FOR SELECT
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS health_metrics_insert_own ON health_metrics;
CREATE POLICY health_metrics_insert_own
ON health_metrics FOR INSERT
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS health_metrics_update_own ON health_metrics;
CREATE POLICY health_metrics_update_own
ON health_metrics FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS health_metrics_delete_own ON health_metrics;
CREATE POLICY health_metrics_delete_own
ON health_metrics FOR DELETE
USING (auth.uid() = user_id);

-- ============================================================================
-- End of Migration 033
-- ============================================================================

