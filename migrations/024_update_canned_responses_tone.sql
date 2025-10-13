-- ============================================================================
-- Migration 024: Update Canned Responses - REAL Tone (Not Fake Enthusiasm)
-- ============================================================================
-- Created: 2025-10-13
-- Description: Replace fake-enthusiastic canned responses with direct, real tone
--
-- CHANGE: From "CRUSH IT! 💪 AMAZING!" to "What's up. Let's work."
-- WHY: Authentic direct communication > fake motivation
-- ============================================================================

-- ============================================================================
-- ENGLISH - Direct, Real Tone
-- ============================================================================
UPDATE translation_cache SET translated_text = 'What''s up. Let''s work.'
  WHERE translation_key = 'canned.greeting' AND language = 'en';

UPDATE translation_cache SET translated_text = 'Anytime.'
  WHERE translation_key = 'canned.thanks' AND language = 'en';

UPDATE translation_cache SET translated_text = 'Later. Stay consistent.'
  WHERE translation_key = 'canned.goodbye' AND language = 'en';

UPDATE translation_cache SET translated_text = 'Got it.'
  WHERE translation_key = 'canned.acknowledgment' AND language = 'en';

UPDATE translation_cache SET translated_text = 'Logged. {calories} cal, {protein}g protein.'
  WHERE translation_key = 'log.meal_confirmed' AND language = 'en';

UPDATE translation_cache SET translated_text = 'Logged. {calories} cal burned. Do it again tomorrow.'
  WHERE translation_key = 'log.activity_confirmed' AND language = 'en';

UPDATE translation_cache SET translated_text = 'Something went wrong. Try again.'
  WHERE translation_key = 'error.failed_to_process' AND language = 'en';

-- ============================================================================
-- PORTUGUESE (PT) - Direto, Tom Real
-- ============================================================================
UPDATE translation_cache SET translated_text = 'E aí. Vamos trabalhar.'
  WHERE translation_key = 'canned.greeting' AND language = 'pt';

UPDATE translation_cache SET translated_text = 'Tranquilo.'
  WHERE translation_key = 'canned.thanks' AND language = 'pt';

UPDATE translation_cache SET translated_text = 'Até. Mantenha a consistência.'
  WHERE translation_key = 'canned.goodbye' AND language = 'pt';

UPDATE translation_cache SET translated_text = 'Entendi.'
  WHERE translation_key = 'canned.acknowledgment' AND language = 'pt';

UPDATE translation_cache SET translated_text = 'Registrado. {calories} cal, {protein}g proteína.'
  WHERE translation_key = 'log.meal_confirmed' AND language = 'pt';

UPDATE translation_cache SET translated_text = 'Registrado. {calories} cal queimadas. Faça de novo amanhã.'
  WHERE translation_key = 'log.activity_confirmed' AND language = 'pt';

UPDATE translation_cache SET translated_text = 'Algo deu errado. Tenta de novo.'
  WHERE translation_key = 'error.failed_to_process' AND language = 'pt';

-- ============================================================================
-- SPANISH (ES) - Directo, Tono Real
-- ============================================================================
UPDATE translation_cache SET translated_text = 'Qué pasa. Vamos a trabajar.'
  WHERE translation_key = 'canned.greeting' AND language = 'es';

UPDATE translation_cache SET translated_text = 'De nada.'
  WHERE translation_key = 'canned.thanks' AND language = 'es';

UPDATE translation_cache SET translated_text = 'Hasta luego. Mantén la consistencia.'
  WHERE translation_key = 'canned.goodbye' AND language = 'es';

UPDATE translation_cache SET translated_text = 'Entendido.'
  WHERE translation_key = 'canned.acknowledgment' AND language = 'es';

UPDATE translation_cache SET translated_text = 'Registrado. {calories} cal, {protein}g proteína.'
  WHERE translation_key = 'log.meal_confirmed' AND language = 'es';

UPDATE translation_cache SET translated_text = 'Registrado. {calories} cal quemadas. Hazlo de nuevo mañana.'
  WHERE translation_key = 'log.activity_confirmed' AND language = 'es';

UPDATE translation_cache SET translated_text = 'Algo salió mal. Inténtalo de nuevo.'
  WHERE translation_key = 'error.failed_to_process' AND language = 'es';

-- ============================================================================
-- NOTES
-- ============================================================================
-- BEFORE:
--   EN: "What's up! 💪 Ready to CRUSH IT?"
--   PT: "E aí! 💪 Pronto para ARRASAR?"
--   ES: "¡Qué pasa! 💪 ¿Listo para DESTROZARLO?"
--
-- AFTER:
--   EN: "What's up. Let's work."
--   PT: "E aí. Vamos trabalhar."
--   ES: "Qué pasa. Vamos a trabajar."
--
-- WHY: Removed fake enthusiasm ("CRUSH IT!", "ARRASAR!", "DESTROZARLO!")
-- Replaced with direct, no-BS communication that respects user's intelligence.
--
-- This matches the system prompt personality:
-- - Direct truth-teller, not cheerleader
-- - No participation trophies
-- - Real acknowledgment for real progress
-- ============================================================================
