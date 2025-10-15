"""
Database migration script for ULTIMATE COACH

Applies SQL migrations to the Supabase database using the service role key.
"""

import asyncio
import sys
from pathlib import Path
from typing import List

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
import asyncpg


async def get_db_connection() -> asyncpg.Connection:
    """Create a direct PostgreSQL connection to Supabase"""
    # Parse Supabase URL to get database connection string
    # Format: https://PROJECT_REF.supabase.co
    # Database URL: postgresql://postgres:[PASSWORD]@db.PROJECT_REF.supabase.co:5432/postgres

    supabase_url = settings.SUPABASE_URL
    project_ref = supabase_url.split("//")[1].split(".")[0]

    # Extract password from service key (it's a JWT, but we need the actual DB password)
    # For now, we'll use the Supabase service key approach
    print(f"⚠️  NOTE: To apply migrations, you need the database password.")
    print(f"   1. Go to Supabase Dashboard → Project Settings → Database")
    print(f"   2. Find 'Connection String' and use the password")
    print(f"   3. Or use Supabase CLI: supabase db push")
    print()

    # Alternative: Use psycopg2 with Supabase's REST API
    # For production, we recommend using Supabase CLI
    raise NotImplementedError(
        "Direct database connection requires DB password. "
        "Use 'supabase db push' or apply migration via Supabase dashboard."
    )


async def apply_migration(migration_file: Path) -> None:
    """Apply a single migration file"""
    print(f"Applying migration: {migration_file.name}")

    conn = await get_db_connection()

    try:
        sql = migration_file.read_text(encoding="utf-8")
        await conn.execute(sql)
        print(f"✓ Applied {migration_file.name}")
    except Exception as e:
        print(f"✗ Failed to apply {migration_file.name}: {e}")
        raise
    finally:
        await conn.close()


async def apply_all_migrations() -> None:
    """Apply all migrations in order"""
    migrations_dir = Path(__file__).parent.parent / "migrations"

    if not migrations_dir.exists():
        print(f"✗ Migrations directory not found: {migrations_dir}")
        sys.exit(1)

    # Get all .sql files sorted by name
    migration_files: List[Path] = sorted(migrations_dir.glob("*.sql"))

    if not migration_files:
        print("No migrations found.")
        return

    print(f"Found {len(migration_files)} migration(s):")
    for mf in migration_files:
        print(f"  - {mf.name}")
    print()

    for migration_file in migration_files:
        await apply_migration(migration_file)

    print(f"\n✓ All migrations applied successfully!")


async def main() -> None:
    """Main entry point"""
    print("=" * 60)
    print("ULTIMATE COACH - Database Migration Tool")
    print("=" * 60)
    print()
    print(f"Supabase URL: {settings.SUPABASE_URL}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print()

    try:
        await apply_all_migrations()
    except NotImplementedError as e:
        print(f"\n{e}")
        print()
        print("RECOMMENDED APPROACH:")
        print("1. Install Supabase CLI: https://supabase.com/docs/guides/cli")
        print("2. Link project: supabase link --project-ref YOUR_PROJECT_REF")
        print("3. Apply migration: supabase db push")
        print()
        print("ALTERNATIVE (Manual):")
        print("1. Go to Supabase Dashboard → SQL Editor")
        print("2. Copy contents of migrations/001_core_schema.sql")
        print("3. Paste and run in SQL Editor")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
