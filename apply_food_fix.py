"""
Apply Food Search Fix Migration

This script applies the 039_fix_food_search_corruption.sql migration
to clean up corrupted data that causes "JSON could not be generated" errors.

Usage:
    python apply_food_fix.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.supabase_service import supabase_service
import structlog

logger = structlog.get_logger()


def main():
    """Apply the food search corruption fix migration."""

    print("=" * 80)
    print("FOOD SEARCH CORRUPTION FIX")
    print("=" * 80)
    print()

    # Read the migration file
    migration_path = Path(__file__).parent / "migrations" / "039_fix_food_search_corruption.sql"

    if not migration_path.exists():
        print(f"❌ Migration file not found: {migration_path}")
        return 1

    print(f"📄 Reading migration: {migration_path.name}")
    with open(migration_path, "r", encoding="utf-8") as f:
        sql = f.read()

    print()
    print("This migration will:")
    print("  1. Clean up NULL/invalid JSONB data in recipe_items")
    print("  2. Fix NULL values in dietary_flags array")
    print("  3. Remove malformed array entries")
    print("  4. Clean up text encoding issues")
    print("  5. Remove orphaned food_servings")
    print("  6. Fix NaN/Infinity values in numeric columns")
    print("  7. Create a safe foods_search_safe view")
    print("  8. Add helpful search indexes")
    print()

    response = input("Do you want to proceed? (yes/no): ")
    if response.lower() not in ["yes", "y"]:
        print("❌ Migration cancelled.")
        return 0

    print()
    print("🔄 Applying migration...")
    print()

    try:
        # Execute the migration using Supabase service role
        # Note: This uses the service role client which bypasses RLS
        client = supabase_service.client

        # Execute the SQL
        result = client.rpc("exec_sql", {"sql": sql}).execute()

        print("✅ Migration applied successfully!")
        print()
        print("Next steps:")
        print("  1. Test the food search in the UI")
        print("  2. Search for 'chicken' to verify it works")
        print("  3. Check backend logs for any remaining errors")
        print()

        return 0

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print()
        print("Manual application required:")
        print(f"  1. Open Supabase SQL Editor")
        print(f"  2. Copy contents of: {migration_path}")
        print(f"  3. Execute the SQL manually")
        print()

        return 1


if __name__ == "__main__":
    sys.exit(main())
