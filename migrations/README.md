# Database Migrations

This directory contains SQL migration files for the ULTIMATE COACH database.

## How to Apply Migrations

### Option 1: Supabase Dashboard (Recommended)

**Step 1: Enable pgvector extension** (required for embeddings):
1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. Navigate to **Database** → **Extensions** (left sidebar)
4. Search for "vector" and enable it

**Step 2: Apply migration**:
1. Navigate to **SQL Editor** (left sidebar)
2. Click **New Query**
3. Open the migration file (e.g., `001_core_schema.sql`)
4. Copy the entire contents
5. Paste into the SQL Editor
6. Click **Run** (or press Ctrl/Cmd + Enter)
7. Verify success (you should see "Success. No rows returned")

**Alternative**: If you don't need embeddings yet, use `001_core_schema_no_vector.sql` instead (skip Step 1).

### Option 2: Supabase CLI

```bash
# Install Supabase CLI
npm install -g supabase

# Link your project
supabase link --project-ref YOUR_PROJECT_REF

# Apply migrations
supabase db push
```

### Option 3: Direct PostgreSQL Connection

```bash
# Get your database password from Supabase Dashboard
# Settings → Database → Connection string

psql "postgresql://postgres:[PASSWORD]@db.PROJECT_REF.supabase.co:5432/postgres" \
  -f migrations/001_core_schema.sql
```

## Migration Files

### 001_core_schema.sql
**Status**: ⏳ Pending
**Description**: Core database schema with 8 tables
- profiles (user data & goals)
- foods (nutrition database)
- meals (meal logs)
- meal_items (foods in meals)
- activities (workout logs)
- coach_conversations (chat sessions)
- coach_messages (chat messages)
- embeddings (vector search for RAG)

**Features**:
- Row Level Security (RLS) enabled on all user tables
- pgvector extension for semantic search
- Built-in cost tracking for AI operations
- Automatic `updated_at` timestamps
- Full-text search indexes on foods

**To Apply**: See options above

## Migration Status Tracking

After applying a migration:
1. Update the status in this README (⏳ Pending → ✅ Applied)
2. Add the date applied
3. Add any notes about issues or modifications

## Best Practices

- **Never modify applied migrations** - Create new migrations instead
- **Test migrations locally first** - Use a test project if possible
- **Backup before applying** - Supabase has automatic backups, but be cautious
- **Review migration SQL** - Ensure you understand what each migration does
- **Apply migrations in order** - Migrations should be numbered sequentially

## Rollback Strategy

If a migration causes issues:
1. Identify the specific problematic changes
2. Create a new rollback migration (e.g., `002_rollback_001.sql`)
3. Never delete or modify existing migration files
4. Document the issue and resolution

## Current Schema Status

**Tables**: 0/8 (pending first migration)

Once 001_core_schema.sql is applied, all 8 core tables will exist.
