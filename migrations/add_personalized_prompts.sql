-- Migration: Add Personalized System Prompts Support
-- Purpose: Enable per-user coaching personas that evolve with behavior
-- Date: 2025-10-26
--
-- This migration adds columns to support:
-- 1. Personalized system prompts generated via Claude meta-prompt
-- 2. Conversational profiles from consultation AI
-- 3. Behavioral data tracking for prompt updates
-- 4. Version tracking for system prompts
-- 5. Audit trail for which prompt version was used in each conversation

-- ============================================================================
-- PROFILES TABLE: Add personalized coaching columns
-- ============================================================================

-- Store the personalized system prompt for this user's coach
-- Generated via meta-prompt using conversational_profile + behavioral_data
-- Updated weekly based on observed behavior
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS coaching_system_prompt TEXT;

-- Store the 200-word natural language profile from consultation AI
-- Generated from 5-8 adaptive questions during onboarding
-- Contains psychology, past failures, blockers, goals context
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS conversational_profile TEXT;

-- Store behavioral metrics as JSONB for flexibility
-- Updated weekly by background jobs
-- Example: {"diet_switches_per_month": 3, "logging_streak": 12, "adherence_rate": 0.67}
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS behavioral_data JSONB DEFAULT '{}';

-- Track system prompt version for A/B testing and debugging
-- Incremented each time prompt is regenerated
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS system_prompt_version INT DEFAULT 1;

-- Track when system prompt was last updated
-- Used by background jobs to determine update frequency
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS last_prompt_update TIMESTAMPTZ DEFAULT NOW();

-- ============================================================================
-- COACH_CONVERSATIONS TABLE: Track prompt version used
-- ============================================================================

-- Track which system prompt version was used for each conversation
-- Enables debugging and A/B testing of prompt variants
-- Links conversation quality to specific prompt versions
ALTER TABLE coach_conversations ADD COLUMN IF NOT EXISTS system_prompt_version_used INT;

-- ============================================================================
-- INDEXES for performance
-- ============================================================================

-- Index for finding users whose prompts need updating
CREATE INDEX IF NOT EXISTS idx_profiles_prompt_update
ON profiles(last_prompt_update)
WHERE coaching_system_prompt IS NOT NULL;

-- Index for behavioral data queries (JSONB GIN index)
CREATE INDEX IF NOT EXISTS idx_profiles_behavioral_data
ON profiles USING GIN(behavioral_data);

-- Index for prompt version tracking in conversations
CREATE INDEX IF NOT EXISTS idx_coach_conversations_prompt_version
ON coach_conversations(system_prompt_version_used)
WHERE system_prompt_version_used IS NOT NULL;

-- ============================================================================
-- COMMENTS for documentation
-- ============================================================================

COMMENT ON COLUMN profiles.coaching_system_prompt IS
'Personalized 500-800 word system prompt generated via Claude meta-prompt. Used in every coach conversation. Updated weekly based on behavioral_data.';

COMMENT ON COLUMN profiles.conversational_profile IS
'200-word natural language profile extracted from consultation AI (5-8 adaptive questions). Contains psychology, past failures, blockers, goals.';

COMMENT ON COLUMN profiles.behavioral_data IS
'JSONB tracking actual user behavior: diet_switches, logging_streak, adherence_rate, failure_patterns. Updated weekly by background jobs.';

COMMENT ON COLUMN profiles.system_prompt_version IS
'Version number of current system prompt. Incremented on each regeneration. Used for A/B testing and debugging.';

COMMENT ON COLUMN profiles.last_prompt_update IS
'Timestamp of last system prompt regeneration. Used by weekly background job to determine update frequency.';

COMMENT ON COLUMN coach_conversations.system_prompt_version_used IS
'System prompt version that was active during this conversation. Links conversation quality to specific prompt variants.';

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
-- Next steps:
-- 1. Run this migration on database
-- 2. Update Pydantic models to include new fields
-- 3. Build system_prompt_generator.py service
-- 4. Build behavioral_tracker.py service
-- 5. Integrate with unified_coach_service.py
-- ============================================================================
