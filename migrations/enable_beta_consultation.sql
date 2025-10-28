-- ============================================================================
-- Migration: Enable Consultation for Beta Users
-- Purpose: Grant consultation access to initial beta testers
-- Date: 2025-10-27
-- ============================================================================
--
-- This script enables the `consultation_enabled` flag for beta users.
-- Run this AFTER identifying your beta users and adding their emails.
--
-- ============================================================================

-- ============================================================================
-- METHOD 1: Enable by Email (Recommended for Beta Launch)
-- ============================================================================

-- Enable consultation for specific beta users by email
-- Replace the emails below with your actual beta users' emails

UPDATE profiles
SET consultation_enabled = true
WHERE email IN (
  -- Add your beta users' emails here:
  -- 'beta1@example.com',
  -- 'beta2@example.com',
  -- 'beta3@example.com'
  -- etc.
);

-- ============================================================================
-- METHOD 2: Enable for All Existing Users (Use with EXTREME caution)
-- ============================================================================

-- Uncomment the query below ONLY if you want to enable consultation
-- for ALL users who signed up before today.
--
-- WARNING: This gives access to expensive AI consultation feature.
-- Only use this if you're ready to support costs for all users.

-- UPDATE profiles
-- SET consultation_enabled = true
-- WHERE created_at < NOW()
--   AND consultation_enabled = false;

-- ============================================================================
-- METHOD 3: Enable for Users Who Completed Onboarding (Safer option)
-- ============================================================================

-- Enable consultation only for users who completed onboarding.
-- This ensures they have proper profile data for consultation.

-- UPDATE profiles
-- SET consultation_enabled = true
-- WHERE onboarding_completed_at IS NOT NULL
--   AND consultation_enabled = false;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Check how many users currently have consultation access
SELECT COUNT(*) as users_with_access
FROM profiles
WHERE consultation_enabled = true;

-- List all users with consultation access
SELECT
  id,
  email,
  full_name,
  consultation_enabled,
  onboarding_completed_at,
  created_at
FROM profiles
WHERE consultation_enabled = true
ORDER BY created_at DESC;

-- Check specific user's consultation status
-- SELECT email, consultation_enabled, onboarding_completed_at
-- FROM profiles
-- WHERE email = 'user@example.com';

-- ============================================================================
-- DISABLE CONSULTATION (If needed)
-- ============================================================================

-- To disable consultation for a specific user:
-- UPDATE profiles
-- SET consultation_enabled = false
-- WHERE email = 'user@example.com';

-- To disable for all users (nuclear option):
-- UPDATE profiles
-- SET consultation_enabled = false
-- WHERE consultation_enabled = true;

-- ============================================================================
-- NOTES
-- ============================================================================
--
-- 1. Consultation is a premium feature with significant AI costs
-- 2. Only enable for users you're actively working with
-- 3. For 7-day ship plan: Enable for your 10 beta users
-- 4. Monitor usage and costs after enabling
-- 5. Users without this flag will see "Consultation not available" message
--
-- ============================================================================
