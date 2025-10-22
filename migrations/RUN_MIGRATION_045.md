# Migration 045: Add completed_at columns

## ⚠️ REQUIRED - Run this migration before testing the program display system

### What this migration does:
- Adds `completed_at` columns to `session_instances` and `meal_instances` tables
- Adds indexes for efficient queries on completed sessions/meals
- Enables the "Mark Complete" functionality in the frontend

### How to run:

#### Option 1: Supabase Dashboard (Recommended)
1. Go to your Supabase project: https://supabase.com/dashboard
2. Click on your project
3. Navigate to **SQL Editor** in the left sidebar
4. Click "**New Query**"
5. Copy the entire contents of `045_add_completed_at_columns.sql`
6. Paste into the SQL editor
7. Click "**Run**" button
8. Verify you see "Success. No rows returned"

#### Option 2: Command Line (if you have psql installed)
```bash
# From the backend directory
psql $DATABASE_URL -f migrations/045_add_completed_at_columns.sql
```

### Verification:
After running, verify the migration worked by running this query in SQL Editor:

```sql
-- Check that columns exist
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name IN ('session_instances', 'meal_instances')
  AND column_name = 'completed_at';
```

You should see 2 rows returned (one for each table).

### What happens if you don't run this migration:
- The "Mark Complete" buttons will return 500 errors
- Backend will try to update a column that doesn't exist
- Error: "column completed_at does not exist"

### Migration file location:
`migrations/045_add_completed_at_columns.sql`

---

**After running this migration, the program display system will be fully functional!**
