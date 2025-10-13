-- ============================================================================
-- Migration 023: I18N Support (Internationalization)
-- ============================================================================
-- Created: 2025-10-12
-- Description: Multilingual support for coach responses
--
-- FEATURES:
-- 1. Language preference in user profiles
-- 2. Translation cache for canned responses
-- 3. Auto-language detection tracking
-- 4. Fast translation lookup with fallback
-- ============================================================================

-- ============================================================================
-- ADD LANGUAGE TO PROFILES
-- ============================================================================
ALTER TABLE profiles
  ADD COLUMN IF NOT EXISTS language TEXT DEFAULT 'en'
    CHECK (language IN ('en', 'pt', 'es', 'fr', 'de', 'it', 'ja', 'ko', 'zh'));

CREATE INDEX IF NOT EXISTS idx_profiles_language ON profiles(language);

COMMENT ON COLUMN profiles.language IS
  'User''s preferred language (ISO 639-1 code). Auto-detected from first message, user can override in settings.';

-- ============================================================================
-- ADD LANGUAGE DETECTION TO CONVERSATIONS
-- ============================================================================
ALTER TABLE coach_conversations
  ADD COLUMN IF NOT EXISTS detected_language TEXT,
  ADD COLUMN IF NOT EXISTS language_confidence NUMERIC(3, 2);

COMMENT ON COLUMN coach_conversations.detected_language IS
  'Auto-detected language from first user message';

-- ============================================================================
-- TRANSLATION CACHE TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS translation_cache (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  translation_key TEXT NOT NULL,
  language TEXT NOT NULL,
  translated_text TEXT NOT NULL,
  context JSONB DEFAULT '{}',

  -- Metadata
  translator TEXT DEFAULT 'manual' CHECK (translator IN ('manual', 'deepl', 'google', 'claude')),
  translation_cost_usd NUMERIC(10, 6) DEFAULT 0,
  verified BOOLEAN DEFAULT FALSE,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  CONSTRAINT unique_translation UNIQUE (translation_key, language)
);

CREATE INDEX IF NOT EXISTS idx_translation_cache_key ON translation_cache(translation_key, language);

-- RLS (public read for efficiency, service write)
ALTER TABLE translation_cache ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Translations are public"
  ON translation_cache FOR SELECT
  USING (true);

-- ============================================================================
-- SEED ENGLISH CANNED RESPONSES
-- ============================================================================
INSERT INTO translation_cache (translation_key, language, translated_text, translator, verified) VALUES
  ('canned.greeting', 'en', 'What''s up! 💪 Ready to CRUSH IT?', 'manual', true),
  ('canned.thanks', 'en', 'Anytime! KEEP PUSHING! 🔥', 'manual', true),
  ('canned.goodbye', 'en', 'See you later! Stay STRONG! 💯', 'manual', true),
  ('canned.acknowledgment', 'en', 'Got it! LET''S GO! 💪', 'manual', true),
  ('log.meal_confirmed', 'en', '✅ Meal logged! {calories} cal, {protein}g protein. FUEL THE MACHINE! 🍽️', 'manual', true),
  ('log.activity_confirmed', 'en', '✅ Workout logged! {calories} cal burned. YOU''RE A BEAST! 🔥', 'manual', true),
  ('error.failed_to_process', 'en', 'Had trouble processing that. Try again! 🤔', 'manual', true)
ON CONFLICT (translation_key, language) DO NOTHING;

-- Seed Portuguese translations (for your Brazilian users!)
INSERT INTO translation_cache (translation_key, language, translated_text, translator, verified) VALUES
  ('canned.greeting', 'pt', 'E aí! 💪 Pronto para ARRASAR?', 'manual', true),
  ('canned.thanks', 'pt', 'Sempre! CONTINUE FORTE! 🔥', 'manual', true),
  ('canned.goodbye', 'pt', 'Até logo! Fique FORTE! 💯', 'manual', true),
  ('canned.acknowledgment', 'pt', 'Entendi! VAMOS LÁ! 💪', 'manual', true),
  ('log.meal_confirmed', 'pt', '✅ Refeição registrada! {calories} cal, {protein}g proteína. ABASTEÇA A MÁQUINA! 🍽️', 'manual', true),
  ('log.activity_confirmed', 'pt', '✅ Treino registrado! {calories} cal queimadas. VOCÊ É UMA FERA! 🔥', 'manual', true),
  ('error.failed_to_process', 'pt', 'Tive problema processando isso. Tenta de novo! 🤔', 'manual', true)
ON CONFLICT (translation_key, language) DO NOTHING;

-- Seed Spanish translations
INSERT INTO translation_cache (translation_key, language, translated_text, translator, verified) VALUES
  ('canned.greeting', 'es', '¡Qué pasa! 💪 ¿Listo para DESTROZARLO?', 'manual', true),
  ('canned.thanks', 'es', '¡Siempre! ¡SIGUE EMPUJANDO! 🔥', 'manual', true),
  ('canned.goodbye', 'es', '¡Hasta luego! ¡Mantente FUERTE! 💯', 'manual', true),
  ('canned.acknowledgment', 'es', '¡Entendido! ¡VAMOS! 💪', 'manual', true),
  ('log.meal_confirmed', 'es', '✅ ¡Comida registrada! {calories} cal, {protein}g proteína. ¡ALIMENTA LA MÁQUINA! 🍽️', 'manual', true),
  ('log.activity_confirmed', 'es', '✅ ¡Entrenamiento registrado! {calories} cal quemadas. ¡ERES UNA BESTIA! 🔥', 'manual', true),
  ('error.failed_to_process', 'es', 'Tuve problemas procesando eso. ¡Inténtalo de nuevo! 🤔', 'manual', true)
ON CONFLICT (translation_key, language) DO NOTHING;

-- ============================================================================
-- TRANSLATION LOOKUP FUNCTION
-- ============================================================================
CREATE OR REPLACE FUNCTION get_translation(
  p_key TEXT,
  p_language TEXT DEFAULT 'en',
  p_params JSONB DEFAULT '{}'
)
RETURNS TEXT AS $$
DECLARE
  v_translation TEXT;
  v_param_key TEXT;
  v_param_value TEXT;
BEGIN
  -- Try to get translation in requested language
  SELECT translated_text INTO v_translation
  FROM translation_cache
  WHERE translation_key = p_key AND language = p_language
  LIMIT 1;

  -- Fallback to English if not found
  IF v_translation IS NULL THEN
    SELECT translated_text INTO v_translation
    FROM translation_cache
    WHERE translation_key = p_key AND language = 'en'
    LIMIT 1;
  END IF;

  -- If still not found, return key itself
  IF v_translation IS NULL THEN
    RETURN p_key;
  END IF;

  -- Replace parameters (e.g., {calories} -> value)
  FOR v_param_key, v_param_value IN SELECT * FROM jsonb_each_text(p_params) LOOP
    v_translation := REPLACE(v_translation, '{' || v_param_key || '}', v_param_value);
  END LOOP;

  RETURN v_translation;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_translation IS
  'Get translation with parameter substitution. Falls back to English if translation not found.';

-- Example usage:
-- SELECT get_translation('log.meal_confirmed', 'pt', '{"calories": "450", "protein": "35"}'::jsonb);
-- Returns: "✅ Refeição registrada! 450 cal, 35g proteína. ABASTEÇA A MÁQUINA! 🍽️"

-- ============================================================================
-- TRIGGER FOR UPDATED_AT
-- ============================================================================
CREATE TRIGGER update_translation_cache_updated_at
  BEFORE UPDATE ON translation_cache
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();
