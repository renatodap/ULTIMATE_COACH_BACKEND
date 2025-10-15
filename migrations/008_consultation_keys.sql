-- ============================================================================
-- Consultation Keys System
-- ============================================================================
-- Version: 1.0.0
-- Created: 2025-10-12
-- Description: One-time use keys to gate access to LLM consultation
--
-- PURPOSE:
-- 1. Control access to expensive LLM consultation feature
-- 2. Generate unique keys manually for approved users
-- 3. Track key usage and prevent reuse
-- 4. Analytics on key redemption
--
-- BUSINESS MODEL:
-- - Admin generates keys manually or via admin panel
-- - Keys can be single-use or limited-use
-- - Keys can have expiration dates
-- - Keys can be tied to specific users or open (first-come-first-serve)
-- ============================================================================

CREATE TABLE IF NOT EXISTS consultation_keys (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  -- The Key
  key_code TEXT NOT NULL UNIQUE,  -- e.g., "SHARP-2025-ABC123XYZ"

  -- Key Metadata
  description TEXT,  -- Internal note: "Beta tester", "VIP user", etc.
  max_uses INTEGER NOT NULL DEFAULT 1 CHECK (max_uses >= 1),
  current_uses INTEGER NOT NULL DEFAULT 0 CHECK (current_uses >= 0),

  -- Restrictions
  expires_at TIMESTAMPTZ,  -- Optional expiration
  assigned_to_user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,  -- Optional: lock to specific user

  -- Status
  is_active BOOLEAN DEFAULT TRUE,  -- Can be deactivated by admin

  -- Tracking
  created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,  -- Admin who created key
  created_at TIMESTAMPTZ DEFAULT NOW(),
  first_used_at TIMESTAMPTZ,
  last_used_at TIMESTAMPTZ,

  -- Constraints
  CONSTRAINT uses_within_limit CHECK (current_uses <= max_uses)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_consultation_keys_code ON consultation_keys (key_code);
CREATE INDEX IF NOT EXISTS idx_consultation_keys_active ON consultation_keys (is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_consultation_keys_assigned ON consultation_keys (assigned_to_user_id) WHERE assigned_to_user_id IS NOT NULL;

-- ============================================================================
-- Key Usage Tracking
-- ============================================================================
-- Track every time a key is used (audit trail)

CREATE TABLE IF NOT EXISTS consultation_key_usage (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  -- Key & User
  key_id UUID NOT NULL REFERENCES consultation_keys(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  session_id UUID NOT NULL REFERENCES consultation_sessions(id) ON DELETE CASCADE,

  -- Usage Info
  used_at TIMESTAMPTZ DEFAULT NOW(),
  ip_address INET,  -- Optional: track IP for fraud detection
  user_agent TEXT,  -- Optional: track browser

  -- Unique constraint: One key per session
  UNIQUE (session_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_consultation_key_usage_key_id ON consultation_key_usage (key_id);
CREATE INDEX IF NOT EXISTS idx_consultation_key_usage_user_id ON consultation_key_usage (user_id);
CREATE INDEX IF NOT EXISTS idx_consultation_key_usage_used_at ON consultation_key_usage (used_at DESC);

-- ============================================================================
-- RLS Policies
-- ============================================================================

-- Users can only see their own assigned keys
ALTER TABLE consultation_keys ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own assigned keys"
  ON consultation_keys FOR SELECT
  USING (assigned_to_user_id = auth.uid());

-- No insert/update/delete for regular users (admin only)
-- Admin policies would be added separately

-- Key usage visible to the user who used it
ALTER TABLE consultation_key_usage ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own key usage"
  ON consultation_key_usage FOR SELECT
  USING (user_id = auth.uid());

-- ============================================================================
-- FUNCTIONS: Key Validation & Redemption
-- ============================================================================

CREATE OR REPLACE FUNCTION validate_and_redeem_consultation_key(
  p_key_code TEXT,
  p_user_id UUID,
  p_session_id UUID,
  p_ip_address INET DEFAULT NULL,
  p_user_agent TEXT DEFAULT NULL
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER  -- Runs with elevated privileges to bypass RLS
AS $$
DECLARE
  v_key_record consultation_keys;
  v_result JSONB;
BEGIN
  -- 1. Find the key
  SELECT * INTO v_key_record
  FROM consultation_keys
  WHERE key_code = p_key_code
  FOR UPDATE;  -- Lock row to prevent race conditions

  -- 2. Validate key exists
  IF v_key_record.id IS NULL THEN
    RETURN jsonb_build_object(
      'success', FALSE,
      'error', 'invalid_key',
      'message', 'This consultation key is not valid.'
    );
  END IF;

  -- 3. Check if key is active
  IF NOT v_key_record.is_active THEN
    RETURN jsonb_build_object(
      'success', FALSE,
      'error', 'key_inactive',
      'message', 'This consultation key has been deactivated.'
    );
  END IF;

  -- 4. Check expiration
  IF v_key_record.expires_at IS NOT NULL AND v_key_record.expires_at < NOW() THEN
    RETURN jsonb_build_object(
      'success', FALSE,
      'error', 'key_expired',
      'message', 'This consultation key has expired.'
    );
  END IF;

  -- 5. Check if key is assigned to specific user
  IF v_key_record.assigned_to_user_id IS NOT NULL AND v_key_record.assigned_to_user_id != p_user_id THEN
    RETURN jsonb_build_object(
      'success', FALSE,
      'error', 'key_not_assigned',
      'message', 'This consultation key is assigned to a different user.'
    );
  END IF;

  -- 6. Check if key has uses remaining
  IF v_key_record.current_uses >= v_key_record.max_uses THEN
    RETURN jsonb_build_object(
      'success', FALSE,
      'error', 'key_exhausted',
      'message', 'This consultation key has already been used.'
    );
  END IF;

  -- 7. Key is valid! Redeem it
  UPDATE consultation_keys
  SET
    current_uses = current_uses + 1,
    first_used_at = COALESCE(first_used_at, NOW()),
    last_used_at = NOW()
  WHERE id = v_key_record.id;

  -- 8. Record usage
  INSERT INTO consultation_key_usage (
    key_id,
    user_id,
    session_id,
    ip_address,
    user_agent
  ) VALUES (
    v_key_record.id,
    p_user_id,
    p_session_id,
    p_ip_address,
    p_user_agent
  );

  -- 9. Return success
  RETURN jsonb_build_object(
    'success', TRUE,
    'key_id', v_key_record.id,
    'uses_remaining', v_key_record.max_uses - v_key_record.current_uses - 1,
    'message', 'Consultation key validated successfully!'
  );

EXCEPTION
  WHEN OTHERS THEN
    -- Handle any unexpected errors
    RETURN jsonb_build_object(
      'success', FALSE,
      'error', 'internal_error',
      'message', 'An error occurred while validating the key.'
    );
END;
$$;

-- ============================================================================
-- HELPER FUNCTION: Check if User Has Valid Key
-- ============================================================================

CREATE OR REPLACE FUNCTION user_has_valid_consultation_key(p_user_id UUID)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  v_has_key BOOLEAN;
BEGIN
  -- Check if user has any unused assigned keys
  SELECT EXISTS(
    SELECT 1
    FROM consultation_keys
    WHERE assigned_to_user_id = p_user_id
      AND is_active = TRUE
      AND (expires_at IS NULL OR expires_at > NOW())
      AND current_uses < max_uses
  ) INTO v_has_key;

  RETURN v_has_key;
END;
$$;

-- ============================================================================
-- HELPER FUNCTION: Generate Key Code
-- ============================================================================

CREATE OR REPLACE FUNCTION generate_consultation_key_code()
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
  v_code TEXT;
  v_exists BOOLEAN;
BEGIN
  LOOP
    -- Generate format: SHARP-YYYY-XXXXXXXXX (e.g., SHARP-2025-A7K9M2X4P)
    v_code := 'SHARP-' ||
              EXTRACT(YEAR FROM NOW())::TEXT || '-' ||
              UPPER(SUBSTRING(MD5(RANDOM()::TEXT || CLOCK_TIMESTAMP()::TEXT) FROM 1 FOR 9));

    -- Check if code already exists
    SELECT EXISTS(
      SELECT 1 FROM consultation_keys WHERE key_code = v_code
    ) INTO v_exists;

    -- If unique, return it
    IF NOT v_exists THEN
      RETURN v_code;
    END IF;
  END LOOP;
END;
$$;

-- ============================================================================
-- EXAMPLE USAGE
-- ============================================================================

-- Generate a single-use key for a specific user:
-- INSERT INTO consultation_keys (
--   key_code,
--   description,
--   max_uses,
--   assigned_to_user_id,
--   created_by
-- ) VALUES (
--   generate_consultation_key_code(),
--   'Beta tester - John Doe',
--   1,
--   'user-uuid',
--   'admin-uuid'
-- );

-- Generate an open key (first-come-first-serve, 10 uses):
-- INSERT INTO consultation_keys (
--   key_code,
--   description,
--   max_uses,
--   expires_at,
--   created_by
-- ) VALUES (
--   generate_consultation_key_code(),
--   'Launch week promotion',
--   10,
--   NOW() + INTERVAL '7 days',
--   'admin-uuid'
-- );

-- Validate and redeem a key:
-- SELECT validate_and_redeem_consultation_key(
--   'COACH-2025-ABC123XYZ',
--   'user-uuid',
--   'session-uuid',
--   '192.168.1.1'::INET,
--   'Mozilla/5.0...'
-- );

-- Check if user has valid key:
-- SELECT user_has_valid_consultation_key('user-uuid');

-- ============================================================================
-- ADMIN QUERIES (for manual key management)
-- ============================================================================

-- View all active keys:
-- SELECT
--   key_code,
--   description,
--   current_uses || '/' || max_uses AS usage,
--   assigned_to_user_id,
--   expires_at,
--   created_at
-- FROM consultation_keys
-- WHERE is_active = TRUE
-- ORDER BY created_at DESC;

-- View key usage history:
-- SELECT
--   k.key_code,
--   k.description,
--   u.email,
--   ku.used_at,
--   ku.ip_address
-- FROM consultation_key_usage ku
-- JOIN consultation_keys k ON k.id = ku.key_id
-- JOIN auth.users u ON u.id = ku.user_id
-- ORDER BY ku.used_at DESC;

-- Deactivate a key:
-- UPDATE consultation_keys
-- SET is_active = FALSE
-- WHERE key_code = 'COACH-2025-ABC123XYZ';

-- ============================================================================
-- SUMMARY
-- ============================================================================
-- ✅ consultation_keys table for key management
-- ✅ consultation_key_usage table for audit trail
-- ✅ validate_and_redeem_consultation_key() function
-- ✅ user_has_valid_consultation_key() function
-- ✅ generate_consultation_key_code() function
-- ✅ Single-use or multi-use keys
-- ✅ Optional expiration dates
-- ✅ Optional user assignment
-- ✅ Race condition protection (FOR UPDATE lock)
-- ✅ IP tracking for fraud detection
-- ✅ Admin-only key creation
--
-- READY FOR:
-- 1. Backend API endpoint to validate keys
-- 2. Admin panel to generate keys
-- 3. Frontend consultation key input UI
-- ============================================================================
