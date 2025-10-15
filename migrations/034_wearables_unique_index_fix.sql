-- ============================================================================
-- Migration 034: Wearable Accounts Unique Index Fix
-- Date: 2025-10-15
-- Description:
--   Ensure an upsert-compatible unique index exists on (user_id, provider)
--   for wearable_accounts to support ON CONFLICT in Supabase upserts.
-- ============================================================================

-- Create unique index if it doesn't exist (works for ON CONFLICT on column list)
CREATE UNIQUE INDEX IF NOT EXISTS uniq_wearable_accounts_user_provider
  ON wearable_accounts(user_id, provider);

-- Note: If a different unique constraint already exists, this is a no-op.
-- Supabase upsert(on_conflict=["user_id","provider"]) requires a unique index
-- or constraint on those columns.

