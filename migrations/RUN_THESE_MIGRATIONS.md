# SQL Migrations - MUST RUN IN ORDER

## Overview
These migrations enable the personalized coaching system. Run them in the **exact order** listed below.

---

## Migration 1: Personalized System Prompts Support
**File:** `add_personalized_prompts.sql`
**Purpose:** Add columns for personalized coaching personas

### What it adds:
- `coaching_system_prompt` - Stores 500-800 word personalized prompts
- `conversational_profile` - Stores 200-word psychological profile from consultation
- `behavioral_data` - JSONB storing usage metrics (adherence, streaks, etc.)
- `system_prompt_version` - Version tracking for A/B testing
- `last_prompt_update` - Timestamp for weekly update tracking
- `system_prompt_version_used` - Tracks which version was used in each conversation

### Run this migration:
```bash
# Using psql
psql -h YOUR_SUPABASE_DB_HOST -U postgres -d postgres -f migrations/add_personalized_prompts.sql

# OR in Supabase SQL Editor
# Copy/paste the contents of add_personalized_prompts.sql and execute
```

---

## Migration 2: Consultation Access Control
**File:** `add_consultation_gate.sql`
**Purpose:** Gate AI consultation behind manual approval flag

### What it adds:
- `consultation_enabled` - Boolean flag (default: false) to control consultation access

### Run this migration:
```bash
# Using psql
psql -h YOUR_SUPABASE_DB_HOST -U postgres -d postgres -f migrations/add_consultation_gate.sql

# OR in Supabase SQL Editor
# Copy/paste the contents of add_consultation_gate.sql and execute
```

### After running this migration:
**IMPORTANT:** By default, NO users will have consultation access. You must manually enable it.

```sql
-- Enable consultation for a specific user
UPDATE profiles
SET consultation_enabled = true
WHERE email = 'user@example.com';

-- Enable for all existing users (use with caution!)
UPDATE profiles
SET consultation_enabled = true;

-- Check who has access
SELECT id, email, consultation_enabled, created_at
FROM profiles
WHERE consultation_enabled = true;
```

---

## Verification

After running both migrations, verify they worked:

```sql
-- Check that new columns exist in profiles table
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'profiles'
AND column_name IN (
    'coaching_system_prompt',
    'conversational_profile',
    'behavioral_data',
    'system_prompt_version',
    'last_prompt_update',
    'consultation_enabled'
);

-- Check that new column exists in coach_conversations table
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'coach_conversations'
AND column_name = 'system_prompt_version_used';

-- Check that indexes were created
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'profiles'
AND indexname IN (
    'idx_profiles_prompt_update',
    'idx_profiles_behavioral_data',
    'idx_profiles_consultation_enabled'
);

SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'coach_conversations'
AND indexname = 'idx_coach_conversations_prompt_version';
```

Expected output: All columns and indexes should exist.

---

## Rollback (if needed)

If something goes wrong, you can rollback:

```sql
-- Rollback Migration 2 (Consultation Gate)
DROP INDEX IF EXISTS idx_profiles_consultation_enabled;
ALTER TABLE profiles DROP COLUMN IF EXISTS consultation_enabled;

-- Rollback Migration 1 (Personalized Prompts)
DROP INDEX IF EXISTS idx_coach_conversations_prompt_version;
DROP INDEX IF EXISTS idx_profiles_behavioral_data;
DROP INDEX IF EXISTS idx_profiles_prompt_update;

ALTER TABLE coach_conversations DROP COLUMN IF EXISTS system_prompt_version_used;

ALTER TABLE profiles DROP COLUMN IF EXISTS last_prompt_update;
ALTER TABLE profiles DROP COLUMN IF EXISTS system_prompt_version;
ALTER TABLE profiles DROP COLUMN IF EXISTS behavioral_data;
ALTER TABLE profiles DROP COLUMN IF EXISTS conversational_profile;
ALTER TABLE profiles DROP COLUMN IF EXISTS coaching_system_prompt;
```

---

## Testing After Migration

1. **Test consultation gate:**
```bash
# Should return 403 Forbidden (if user doesn't have consultation_enabled=true)
curl -X POST https://your-api.com/api/v1/consultation/start \
  -H "Authorization: Bearer YOUR_JWT" \
  -H "Content-Type: application/json" \
  -d '{}'
```

2. **Enable consultation for test user:**
```sql
UPDATE profiles
SET consultation_enabled = true
WHERE email = 'your-test-email@example.com';
```

3. **Test consultation again (should work now):**
```bash
curl -X POST https://your-api.com/api/v1/consultation/start \
  -H "Authorization: Bearer YOUR_JWT" \
  -H "Content-Type: application/json" \
  -d '{}'
```

4. **Complete consultation and verify profile generation:**
```sql
-- After completing a consultation, check that these were populated:
SELECT
    id,
    email,
    conversational_profile IS NOT NULL as has_profile,
    coaching_system_prompt IS NOT NULL as has_prompt,
    system_prompt_version,
    last_prompt_update
FROM profiles
WHERE email = 'your-test-email@example.com';

-- Should show:
-- has_profile: true
-- has_prompt: true
-- system_prompt_version: 1
-- last_prompt_update: <recent timestamp>
```

---

## Production Deployment Checklist

- [ ] Backup database before running migrations
- [ ] Run Migration 1 (add_personalized_prompts.sql)
- [ ] Run Migration 2 (add_consultation_gate.sql)
- [ ] Verify all columns and indexes created successfully
- [ ] Enable `consultation_enabled` for initial beta users
- [ ] Test consultation flow end-to-end with a beta user
- [ ] Verify conversational_profile generated
- [ ] Verify coaching_system_prompt generated
- [ ] Verify personalized prompt used in coach conversations
- [ ] Monitor logs for any errors in background jobs
- [ ] Set environment variables for config (optional - see below)

---

## Environment Variables (Optional Configuration)

All personalized coaching features are configurable via environment variables.
See `app/config/personalized_coaching.py` for all available options.

**Key variables you might want to set:**

```bash
# Change detection thresholds (default: 0.10 = 10%)
ADHERENCE_CHANGE_THRESHOLD=0.15  # Only update if adherence changes by 15%
LOGGING_CHANGE_THRESHOLD=0.15    # Only update if logging changes by 15%
STREAK_CHANGE_THRESHOLD=10       # Only update if streak changes by 10+ days

# Background job schedule (default: Sunday 3am)
PROMPT_UPDATE_DAY=mon            # Run on Mondays instead
PROMPT_UPDATE_HOUR=2             # Run at 2am instead of 3am
MIN_DAYS_BETWEEN_UPDATES=14      # Only update every 2 weeks instead of weekly

# Cost optimization
ENABLE_CHANGE_DETECTION=true     # Set to false to always update (expensive!)
LOG_PROMPT_GENERATION_COSTS=true # Log costs for monitoring

# Behavioral analysis window
BEHAVIORAL_ANALYSIS_DAYS=30      # Analyze last 30 days of data
```

**To apply changes:** Restart the backend server.

---

## Support

If you encounter issues:
1. Check logs for error messages
2. Verify migrations ran successfully using the verification queries above
3. Check that `consultation_enabled=true` for test users
4. Verify environment variables are set correctly

---

## Summary

✅ **Migration 1:** Adds personalized prompt storage
✅ **Migration 2:** Adds consultation access control

After running both migrations and enabling consultation for users, the system will:
1. Generate conversational profiles from consultation conversations
2. Generate personalized system prompts (500-800 words)
3. Use personalized prompts in coach conversations
4. Update prompts weekly based on behavioral changes (configurable thresholds)
5. Track prompt versions for debugging and A/B testing

**Total time to run:** ~5 seconds
**Database downtime:** None (migrations are safe while app is running)
