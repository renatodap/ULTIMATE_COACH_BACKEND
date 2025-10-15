-- ============================================================================
-- Consultation Messages Table
-- ============================================================================
-- Version: 1.0.0
-- Created: 2025-10-12
-- Description: Store conversation history for consultation sessions
--
-- PURPOSE:
-- 1. Track every message in consultation conversation
-- 2. Build conversation history for LLM context
-- 3. Prevent duplicate questions
-- 4. Allow users to review/edit their answers
-- 5. Analytics on conversation patterns
-- ============================================================================

CREATE TABLE IF NOT EXISTS consultation_messages (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  -- Relationships
  session_id UUID NOT NULL REFERENCES consultation_sessions(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Message Content
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  content TEXT NOT NULL,

  -- AI Metadata
  ai_model TEXT,  -- e.g., "claude-3-5-sonnet-20241022"
  tokens_used INTEGER,
  cost_usd NUMERIC(10, 6),

  -- Extracted Data (what was saved to DB from this message)
  extracted_data JSONB DEFAULT '[]',
  -- Example: [
  --   {"tool": "insert_user_training_modality", "id": "uuid", "data": {...}},
  --   {"tool": "insert_user_familiar_exercise", "id": "uuid", "data": {...}}
  -- ]

  -- Tool Calls (for debugging)
  tool_calls JSONB DEFAULT '[]',
  -- Example: [
  --   {"name": "search_exercises", "input": {"query": "bench press"}, "result": [...]},
  --   {"name": "insert_user_familiar_exercise", "input": {...}, "result": {...}}
  -- ]

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_consultation_messages_session_id
  ON consultation_messages (session_id, created_at);

CREATE INDEX IF NOT EXISTS idx_consultation_messages_user_id
  ON consultation_messages (user_id);

CREATE INDEX IF NOT EXISTS idx_consultation_messages_role
  ON consultation_messages (session_id, role);

-- RLS
ALTER TABLE consultation_messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own consultation messages"
  ON consultation_messages FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own consultation messages"
  ON consultation_messages FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- ============================================================================
-- HELPER FUNCTION: Get Data Already Collected
-- ============================================================================
-- This function returns a summary of what data has been extracted so far
-- in the consultation, so the LLM knows what NOT to ask again.

CREATE OR REPLACE FUNCTION get_consultation_progress(p_session_id UUID)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
  v_user_id UUID;
  v_progress JSONB;
BEGIN
  -- Get user_id for this session
  SELECT user_id INTO v_user_id
  FROM consultation_sessions
  WHERE id = p_session_id;

  IF v_user_id IS NULL THEN
    RETURN '{}'::JSONB;
  END IF;

  -- Build progress summary
  SELECT jsonb_build_object(
    'training_modalities_count', (
      SELECT COUNT(*) FROM user_training_modalities WHERE user_id = v_user_id
    ),
    'familiar_exercises_count', (
      SELECT COUNT(*) FROM user_familiar_exercises WHERE user_id = v_user_id
    ),
    'training_availability_count', (
      SELECT COUNT(*) FROM user_training_availability WHERE user_id = v_user_id
    ),
    'preferred_meal_times_count', (
      SELECT COUNT(*) FROM user_preferred_meal_times WHERE user_id = v_user_id
    ),
    'typical_meal_foods_count', (
      SELECT COUNT(*) FROM user_typical_meal_foods WHERE user_id = v_user_id
    ),
    'upcoming_events_count', (
      SELECT COUNT(*) FROM user_upcoming_events WHERE user_id = v_user_id
    ),
    'improvement_goals_count', (
      SELECT COUNT(*) FROM user_improvement_goals WHERE user_id = v_user_id
    ),
    'difficulties_count', (
      SELECT COUNT(*) FROM user_difficulties WHERE user_id = v_user_id
    ),
    'non_negotiables_count', (
      SELECT COUNT(*) FROM user_non_negotiables WHERE user_id = v_user_id
    ),

    -- Also include the actual data for context
    'training_modalities', (
      SELECT jsonb_agg(
        jsonb_build_object(
          'modality_name', tm.name,
          'is_primary', utm.is_primary,
          'proficiency_level', utm.proficiency_level,
          'years_experience', utm.years_experience
        )
      )
      FROM user_training_modalities utm
      JOIN training_modalities tm ON tm.id = utm.modality_id
      WHERE utm.user_id = v_user_id
    ),

    'familiar_exercises', (
      SELECT jsonb_agg(
        jsonb_build_object(
          'exercise_name', e.name,
          'comfort_level', ufe.comfort_level,
          'typical_weight_kg', ufe.typical_weight_kg,
          'typical_reps', ufe.typical_reps,
          'frequency', ufe.frequency
        )
      )
      FROM user_familiar_exercises ufe
      JOIN exercises e ON e.id = ufe.exercise_id
      WHERE ufe.user_id = v_user_id
    ),

    'training_schedule', (
      SELECT jsonb_agg(
        jsonb_build_object(
          'day_of_week', uta.day_of_week,
          'time_of_day', uta.time_of_day,
          'duration_minutes', uta.typical_duration_minutes,
          'location_type', uta.location_type
        )
      )
      FROM user_training_availability uta
      WHERE uta.user_id = v_user_id
      ORDER BY uta.day_of_week
    ),

    'meal_times', (
      SELECT jsonb_agg(
        jsonb_build_object(
          'meal_time', mt.label,
          'portion_size', upmt.typical_portion_size,
          'flexibility_minutes', upmt.flexibility_minutes
        )
      )
      FROM user_preferred_meal_times upmt
      JOIN meal_times mt ON mt.id = upmt.meal_time_id
      WHERE upmt.user_id = v_user_id
    ),

    'typical_foods', (
      SELECT jsonb_agg(
        jsonb_build_object(
          'food_name', f.name,
          'frequency', utmf.frequency,
          'typical_quantity_grams', utmf.typical_quantity_grams
        )
      )
      FROM user_typical_meal_foods utmf
      JOIN foods f ON f.id = utmf.food_id
      WHERE utmf.user_id = v_user_id
    ),

    'goals_and_events', (
      SELECT jsonb_agg(
        jsonb_build_object(
          'event_name', uue.event_name,
          'event_date', uue.event_date,
          'priority', uue.priority
        )
      )
      FROM user_upcoming_events uue
      WHERE uue.user_id = v_user_id
    )
  ) INTO v_progress;

  RETURN v_progress;
END;
$$;

-- Example usage:
-- SELECT get_consultation_progress('session-uuid');
-- Returns JSON with all extracted data so far

-- ============================================================================
-- SUMMARY
-- ============================================================================
-- ✅ consultation_messages table for conversation history
-- ✅ Tracks every message with role (user/assistant/system)
-- ✅ Stores extracted_data JSON for each message
-- ✅ Stores tool_calls JSON for debugging
-- ✅ Helper function to get progress summary
-- ✅ Progress summary includes counts AND actual data
--
-- USAGE:
-- 1. Save every message to this table
-- 2. Load history when building LLM context
-- 3. Call get_consultation_progress() to see what's already collected
-- 4. Include progress in system prompt so LLM doesn't ask duplicates
-- ============================================================================
