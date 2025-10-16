-- Migration: Add 'auth_required' status to wearable_accounts
-- Purpose: Allow marking accounts that need re-authentication without showing generic "error"
-- Date: 2025-10-16

-- Drop existing CHECK constraint
ALTER TABLE public.wearable_accounts
  DROP CONSTRAINT IF EXISTS wearable_accounts_status_check;

-- Add new CHECK constraint with 'auth_required' status
ALTER TABLE public.wearable_accounts
  ADD CONSTRAINT wearable_accounts_status_check
  CHECK (status = ANY (ARRAY[
    'connected'::text,
    'disconnected'::text,
    'auth_required'::text,
    'error'::text,
    'configured_missing_secret'::text
  ]));

COMMENT ON COLUMN public.wearable_accounts.status IS 'Account connection status:
  - connected: Active and syncing
  - disconnected: Not connected
  - auth_required: Credentials expired, user needs to reconnect
  - error: Generic error (not auth-related)
  - configured_missing_secret: Credentials provided but encryption key missing';
