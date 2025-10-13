-- ============================================================================
-- Migration 022: Add System AI Providers
-- ============================================================================
-- Created: 2025-10-13
-- Description: Add 'canned' and 'system' as valid ai_provider values
--
-- REASON:
-- Canned responses (pattern matching) and system messages need to be saved
-- to coach_messages table but don't come from external AI providers.
-- ============================================================================

-- Drop existing constraint
ALTER TABLE coach_messages
  DROP CONSTRAINT IF EXISTS coach_messages_ai_provider_check;

-- Add new constraint with additional providers
ALTER TABLE coach_messages
  ADD CONSTRAINT coach_messages_ai_provider_check
  CHECK (ai_provider IN ('anthropic', 'groq', 'openai', 'deepseek', 'canned', 'system'));

-- Note: 'canned' = pattern-matched responses (no AI call)
--       'system' = system-generated messages (quick ACKs, errors, etc.)
