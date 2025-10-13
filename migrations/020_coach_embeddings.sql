-- ============================================================================
-- Migration 020: Coach Message Embeddings + Cleanup Strategy
-- ============================================================================
-- Created: 2025-10-12
-- Description: Vector storage for coach messages with intelligent cleanup
--
-- FEATURES:
-- 1. pgvector embeddings (384D from OpenAI)
-- 2. Importance scoring for cleanup strategy
-- 3. Fast vector similarity search
-- 4. Automatic archival of old low-importance messages
-- ============================================================================

-- Enable pgvector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- COACH MESSAGE EMBEDDINGS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS coach_message_embeddings (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  message_id UUID NOT NULL REFERENCES coach_messages(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),

  -- Vector embedding (384 dimensions from OpenAI text-embedding-3-small)
  embedding vector(384) NOT NULL,

  -- Searchable text (truncated for storage)
  content_text TEXT NOT NULL,

  -- Metadata
  embedding_model TEXT DEFAULT 'text-embedding-3-small' NOT NULL,
  embedding_cost_usd NUMERIC(10, 6) DEFAULT 0.0001,

  -- Importance scoring (for cleanup strategy)
  importance_score NUMERIC(3, 2) DEFAULT 0.5 CHECK (importance_score >= 0 AND importance_score <= 1),
  is_archived BOOLEAN DEFAULT FALSE,

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  archived_at TIMESTAMPTZ
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_coach_embeddings_user ON coach_message_embeddings(user_id);
CREATE INDEX IF NOT EXISTS idx_coach_embeddings_message ON coach_message_embeddings(message_id);
CREATE INDEX IF NOT EXISTS idx_coach_embeddings_created ON coach_message_embeddings(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_coach_embeddings_importance ON coach_message_embeddings(user_id, importance_score DESC) WHERE is_archived = FALSE;

-- Vector similarity index (IVFFlat for fast approximate search)
CREATE INDEX IF NOT EXISTS idx_coach_embeddings_vector ON coach_message_embeddings
  USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- RLS
ALTER TABLE coach_message_embeddings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own embeddings"
  ON coach_message_embeddings FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Service can insert embeddings"
  ON coach_message_embeddings FOR INSERT
  WITH CHECK (true); -- Service role only

-- ============================================================================
-- SEARCH FUNCTION
-- ============================================================================
CREATE OR REPLACE FUNCTION match_coach_embeddings(
  query_embedding vector(384),
  filter_user_id UUID,
  match_threshold FLOAT DEFAULT 0.5,
  match_count INT DEFAULT 10,
  include_archived BOOLEAN DEFAULT FALSE
)
RETURNS TABLE (
  id UUID,
  message_id UUID,
  role TEXT,
  content_text TEXT,
  similarity FLOAT,
  importance_score NUMERIC,
  created_at TIMESTAMPTZ
)
LANGUAGE sql STABLE
AS $$
  SELECT
    e.id,
    e.message_id,
    e.role,
    e.content_text,
    1 - (e.embedding <=> query_embedding) AS similarity,
    e.importance_score,
    e.created_at
  FROM coach_message_embeddings e
  WHERE e.user_id = filter_user_id
    AND (include_archived OR e.is_archived = FALSE)
    AND 1 - (e.embedding <=> query_embedding) > match_threshold
  ORDER BY e.embedding <=> query_embedding
  LIMIT match_count;
$$;

COMMENT ON FUNCTION match_coach_embeddings IS
  'Find similar coach messages using vector similarity search';

-- ============================================================================
-- IMPORTANCE CALCULATION
-- ============================================================================
CREATE OR REPLACE FUNCTION calculate_embedding_importance(
  p_message_id UUID
)
RETURNS NUMERIC AS $$
DECLARE
  v_importance NUMERIC := 0.5;
  v_age_days INT;
  v_conversation_id UUID;
  v_is_favorited BOOLEAN;
  v_has_followup BOOLEAN;
BEGIN
  -- Get message details
  SELECT
    m.conversation_id,
    EXTRACT(DAY FROM NOW() - m.created_at) AS age_days
  INTO v_conversation_id, v_age_days
  FROM coach_messages m
  WHERE m.id = p_message_id;

  -- Check if conversation is favorited
  SELECT c.archived INTO v_is_favorited
  FROM coach_conversations c
  WHERE c.id = v_conversation_id;

  -- Check if message has follow-up (user asked follow-up question)
  SELECT EXISTS(
    SELECT 1 FROM coach_messages
    WHERE conversation_id = v_conversation_id
      AND created_at > (SELECT created_at FROM coach_messages WHERE id = p_message_id)
      AND role = 'user'
    LIMIT 1
  ) INTO v_has_followup;

  -- Calculate importance
  -- Base: 0.5
  -- +0.3 if favorited conversation
  -- +0.2 if has follow-up (engaged)
  -- -0.1 per 30 days age (decay)
  v_importance := 0.5;

  IF v_is_favorited THEN
    v_importance := v_importance + 0.3;
  END IF;

  IF v_has_followup THEN
    v_importance := v_importance + 0.2;
  END IF;

  -- Age decay (lose 0.1 per 30 days)
  v_importance := v_importance - (v_age_days / 30.0 * 0.1);

  -- Clamp to [0, 1]
  v_importance := GREATEST(0, LEAST(1, v_importance));

  RETURN v_importance;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION calculate_embedding_importance IS
  'Calculate importance score for embedding based on age, engagement, and favoriting';

-- ============================================================================
-- CLEANUP FUNCTION
-- ============================================================================
CREATE OR REPLACE FUNCTION archive_old_embeddings(
  p_archive_after_days INT DEFAULT 90,
  p_min_importance NUMERIC DEFAULT 0.3
)
RETURNS INT AS $$
DECLARE
  v_archived_count INT;
BEGIN
  UPDATE coach_message_embeddings
  SET
    is_archived = TRUE,
    archived_at = NOW()
  WHERE
    is_archived = FALSE
    AND created_at < NOW() - (p_archive_after_days || ' days')::INTERVAL
    AND importance_score < p_min_importance;

  GET DIAGNOSTICS v_archived_count = ROW_COUNT;

  RETURN v_archived_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION archive_old_embeddings IS
  'Archive embeddings older than N days with low importance. Run via background job.';
