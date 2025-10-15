"""
Migration applier that executes SQL via Supabase REST API
Usage: python scripts/apply_migration.py migrations/002_onboarding_data.sql
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
import requests

def apply_migration(sql_file: str):
    """Apply a SQL migration file via Supabase REST API"""

    print(f"Loading migration: {sql_file}")

    # Read SQL file
    with open(sql_file, 'r') as f:
        sql = f.read()

    print(f"Connecting to Supabase: {settings.SUPABASE_URL}")

    # Supabase REST API endpoint for executing SQL
    url = f"{settings.SUPABASE_URL}/rest/v1/rpc/exec_sql"

    headers = {
        "apikey": settings.SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json"
    }

    # Try to execute via RPC
    print("Attempting to execute migration via Supabase REST API...")

    try:
        response = requests.post(url, headers=headers, json={"query": sql})

        if response.status_code == 200:
            print("✅ Migration applied successfully!")
            return True
        else:
            print(f"❌ Failed to apply migration: {response.status_code}")
            print(f"Response: {response.text}")

            # Fallback: print instructions
            print("\n" + "="*80)
            print("MANUAL MIGRATION REQUIRED")
            print("="*80)
            print("\nPlease apply this migration manually via Supabase Dashboard:")
            print("1. Go to https://supabase.com/dashboard/project/[your-project]/sql/new")
            print("2. Paste the SQL from the file below")
            print("3. Click 'Run'")
            print("\nMigration file:", sql_file)
            print("="*80)
            return False

    except Exception as e:
        print(f"❌ Error: {e}")

        # Fallback: print instructions
        print("\n" + "="*80)
        print("MANUAL MIGRATION REQUIRED")
        print("="*80)
        print("\nPlease apply this migration manually via Supabase Dashboard:")
        print("1. Go to https://supabase.com/dashboard/project/[your-project]/sql/new")
        print("2. Copy the migration SQL from:", sql_file)
        print("3. Paste and click 'Run'")
        print("\nMigration SQL preview:")
        print("-"*80)
        print(sql[:500] + "..." if len(sql) > 500 else sql)
        print("="*80)
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/apply_migration.py <migration_file>")
        sys.exit(1)

    sql_file = sys.argv[1]

    if not os.path.exists(sql_file):
        print(f"Error: File not found: {sql_file}")
        sys.exit(1)

    success = apply_migration(sql_file)
    sys.exit(0 if success else 1)
