# How to Apply Activity Tracking System Migration

This guide walks you through applying the `20251012_230748_add_activity_tracking_system.sql` migration to your database.

## ⚠️ Before You Start

**IMPORTANT**: This migration modifies your database schema. Please:
1. ✅ Backup your database (Supabase does this automatically, but verify)
2. ✅ Test on a development/staging environment first if possible
3. ✅ Verify you have existing `activities` and `profiles` tables
4. ✅ Close any active connections to the database during migration

## 🎯 What This Migration Does

- **Adds 10 columns** to `activities` table (end_time, deleted_at, template fields, wearable fields)
- **Creates 5 new tables**: templates, GPS tracks, match history, duplicates, wearable connections
- **Updates** `profiles` table with activity-related fields
- **Creates 15+ indexes** for performance
- **Adds** helper function for HR zone calculation
- **Includes** self-verification checks

**Estimated Time**: 2-5 minutes

---

## 📋 Step-by-Step Application

### Option 1: Supabase Dashboard (Recommended)

**Step 1: Open SQL Editor**
1. Go to https://supabase.com/dashboard
2. Select your project
3. Click **SQL Editor** in left sidebar
4. Click **New Query**

**Step 2: Load Migration SQL**
1. Open the file: `migrations/20251012_230748_add_activity_tracking_system.sql`
2. Copy **ALL** contents (Ctrl+A, Ctrl+C)
3. Paste into Supabase SQL Editor (Ctrl+V)

**Step 3: Execute Migration**
1. Click **Run** button (or press Ctrl+Enter)
2. Wait for execution (should take 10-30 seconds)
3. **Look for success messages** at bottom:
   ```
   NOTICE:  Activities table: All required columns present ✓
   NOTICE:  New tables: All tables created ✓
   NOTICE:  Profiles table: Activity columns added ✓
   NOTICE:  ===========================================
   NOTICE:  Migration completed successfully! ✓
   ```

**Step 4: Verify Success**
1. Go to **Database** → **Tables** in left sidebar
2. Verify new tables exist:
   - ✅ `activity_templates`
   - ✅ `gps_tracks`
   - ✅ `activity_template_matches`
   - ✅ `activity_duplicates`
   - ✅ `wearable_connections`
3. Click `activities` table → View columns → Verify new columns:
   - ✅ `end_time`
   - ✅ `deleted_at`
   - ✅ `template_id`
   - ✅ (and 7 more columns)

---

### Option 2: Python Script (Alternative)

```bash
# From project root directory
python scripts/apply_migration.py migrations/20251012_230748_add_activity_tracking_system.sql
```

**Note**: This method may not work for all Supabase setups. If it fails, use Option 1.

---

### Option 3: Supabase CLI (Advanced)

**Prerequisites**:
```bash
# Install Supabase CLI
npm install -g supabase

# Link your project (one-time setup)
supabase link --project-ref YOUR_PROJECT_REF

# Find your project ref: Dashboard → Settings → General → Reference ID
```

**Apply Migration**:
```bash
# Copy migration to Supabase migrations folder
cp migrations/20251012_230748_add_activity_tracking_system.sql \
   supabase/migrations/$(date +%Y%m%d%H%M%S)_add_activity_tracking_system.sql

# Push to database
supabase db push
```

---

## ✅ Post-Migration Verification

Run these queries in SQL Editor to verify everything worked:

### 1. Check activities table columns
```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'activities'
  AND column_name IN (
    'end_time', 'deleted_at', 'template_id',
    'wearable_activity_id', 'device_name'
  )
ORDER BY column_name;
```
**Expected**: 5 rows returned

### 2. Check new tables exist
```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN (
    'activity_templates',
    'gps_tracks',
    'activity_template_matches',
    'activity_duplicates',
    'wearable_connections'
  )
ORDER BY table_name;
```
**Expected**: 5 rows returned

### 3. Check profiles columns
```sql
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'profiles'
  AND column_name IN (
    'daily_calorie_burn_goal',
    'max_heart_rate',
    'hr_zone_1_max'
  )
ORDER BY column_name;
```
**Expected**: 3 rows returned

### 4. Test HR zone calculation function
```sql
SELECT * FROM calculate_hr_zones(180);
```
**Expected**: 1 row with 5 columns (zone thresholds)

---

## 🐛 Troubleshooting

### Error: "relation 'activities' does not exist"
**Cause**: Base `activities` table doesn't exist yet
**Solution**: Apply core schema migration first (see `migrations/10-12-112pm.sql`)

### Error: "column 'template_id' already exists"
**Cause**: Migration was already partially applied
**Solution**: Run this cleanup, then re-run full migration:
```sql
-- Remove partial changes
ALTER TABLE activities DROP COLUMN IF EXISTS template_id CASCADE;
ALTER TABLE activities DROP COLUMN IF EXISTS deleted_at;
DROP TABLE IF EXISTS activity_templates CASCADE;
DROP TABLE IF EXISTS gps_tracks CASCADE;
DROP TABLE IF EXISTS activity_template_matches CASCADE;
DROP TABLE IF EXISTS activity_duplicates CASCADE;
DROP TABLE IF EXISTS wearable_connections CASCADE;
```

### Error: "constraint 'activities_source_check' does not exist"
**Solution**: This is OK - constraint will be created. Continue migration.

### Error: "permission denied for table activities"
**Cause**: Not using service role key
**Solution**: Ensure you're connected with admin/service role credentials

---

## 🔄 Rollback (If Needed)

If you need to undo this migration:

```sql
-- WARNING: This will delete all template and wearable data!

-- Remove columns from activities
ALTER TABLE activities
  DROP COLUMN IF EXISTS end_time,
  DROP COLUMN IF EXISTS deleted_at,
  DROP COLUMN IF EXISTS template_id,
  DROP COLUMN IF EXISTS template_match_score,
  DROP COLUMN IF EXISTS template_applied_at,
  DROP COLUMN IF EXISTS wearable_activity_id,
  DROP COLUMN IF EXISTS wearable_url,
  DROP COLUMN IF EXISTS device_name,
  DROP COLUMN IF EXISTS sync_timestamp,
  DROP COLUMN IF EXISTS raw_wearable_data;

-- Remove new tables
DROP TABLE IF EXISTS activity_template_matches CASCADE;
DROP TABLE IF EXISTS activity_duplicates CASCADE;
DROP TABLE IF EXISTS wearable_connections CASCADE;
DROP TABLE IF EXISTS gps_tracks CASCADE;
DROP TABLE IF EXISTS activity_templates CASCADE;

-- Remove profiles columns
ALTER TABLE profiles
  DROP COLUMN IF EXISTS daily_calorie_burn_goal,
  DROP COLUMN IF EXISTS max_heart_rate,
  DROP COLUMN IF EXISTS resting_heart_rate,
  DROP COLUMN IF EXISTS hr_zone_1_max,
  DROP COLUMN IF EXISTS hr_zone_2_max,
  DROP COLUMN IF EXISTS hr_zone_3_max,
  DROP COLUMN IF EXISTS hr_zone_4_max,
  DROP COLUMN IF EXISTS hr_zone_5_max;

-- Remove function
DROP FUNCTION IF EXISTS calculate_hr_zones;

-- Restore original source constraint
ALTER TABLE activities DROP CONSTRAINT IF EXISTS activities_source_check;
ALTER TABLE activities ADD CONSTRAINT activities_source_check
  CHECK (source IN ('manual', 'ai_text', 'ai_voice', 'garmin', 'strava'));
```

---

## 📝 Update Migration Status

After successful application, update `migrations/README.md`:

Find this section:
```markdown
### 20251012_230748_add_activity_tracking_system.sql
**Status**: ⏳ Pending
```

Change to:
```markdown
### 20251012_230748_add_activity_tracking_system.sql
**Status**: ✅ Applied
**Applied On**: [TODAY'S DATE]
**Applied By**: [YOUR NAME]
```

---

## 🎉 Next Steps

Once migration is applied successfully:

1. ✅ Update backend CLAUDE.md to mark migration as complete
2. ✅ Test creating an activity with `deleted_at=NULL`
3. ✅ Test soft delete by setting `deleted_at=NOW()`
4. ✅ Ready to implement Phase 1: Template System
5. ✅ Feature flags control what's visible to users

**No code changes needed yet** - the database is now ready for the features to be built on top of it!

---

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify you're using the service role key (not anon key)
3. Check Supabase Dashboard → Logs for error details
4. Create a backup before trying again

---

## 📊 Migration Details

**File**: `migrations/20251012_230748_add_activity_tracking_system.sql`
**Size**: ~600 lines of SQL
**Tables Modified**: 2 (activities, profiles)
**Tables Created**: 5
**Indexes Created**: 15+
**Functions Created**: 1
**Breaking Changes**: None (all columns nullable or have defaults)
**Data Loss Risk**: None (only adds, doesn't remove)

**Reversible**: Yes (see Rollback section)
**Idempotent**: Yes (safe to run multiple times with IF NOT EXISTS checks)
