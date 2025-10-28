-- Migration: Add Consultation Access Control
-- Purpose: Gate AI consultation behind manual approval flag
-- Date: 2025-10-26
--
-- This migration adds consultation access control to prevent unrestricted
-- access to expensive AI consultation feature. Admins must manually enable
-- consultation_enabled for specific users.
--
-- ============================================================================
-- PROFILES TABLE: Add consultation access flag
-- ============================================================================

-- Add consultation_enabled flag (default false)
-- Only users with this flag set to true can start consultations
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS consultation_enabled BOOLEAN DEFAULT false;

-- ============================================================================
-- INDEX for performance
-- ============================================================================

-- Index for quickly finding users with consultation access
CREATE INDEX IF NOT EXISTS idx_profiles_consultation_enabled
ON profiles(consultation_enabled)
WHERE consultation_enabled = true;

-- ============================================================================
-- COMMENT for documentation
-- ============================================================================

COMMENT ON COLUMN profiles.consultation_enabled IS
'Controls access to AI consultation feature. Must be manually enabled by admin. Default: false (no access).';

-- ============================================================================
-- ADMIN INSTRUCTIONS
-- ============================================================================
-- To enable consultation for a specific user:
--
-- UPDATE profiles
-- SET consultation_enabled = true
-- WHERE email = 'user@example.com';
--
-- To enable for all existing users (use with caution):
--
-- UPDATE profiles
-- SET consultation_enabled = true
-- WHERE created_at < NOW();
--
-- To check who has access:
--
-- SELECT id, email, consultation_enabled, created_at
-- FROM profiles
-- WHERE consultation_enabled = true;
-- ============================================================================
