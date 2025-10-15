"""
Simple migration runner using Supabase REST API
Usage: python scripts/run_migration.py migrations/002_onboarding_data.sql
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from supabase import create_client

def run_migration(sql_file: str):
    """Run a SQL migration file"""

    print(f"Loading migration: {sql_file}")

    # Read SQL file
    with open(sql_file, 'r') as f:
        sql = f.read()

    print(f"Connecting to Supabase: {settings.SUPABASE_URL}")

    # Create Supabase client with service key
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

    print("Executing migration...")

    try:
        # Execute SQL using Supabase RPC
        # Note: This requires a SQL editor or direct database access
        # For now, we'll print instructions
        print("\n" + "="*80)
        print("MIGRATION SQL:")
        print("="*80)
        print(sql)
        print("="*80)
        print("\nTo apply this migration:")
        print("1. Go to Supabase Dashboard > SQL Editor")
        print("2. Paste the SQL above")
        print("3. Click 'Run'")
        print("\nOR use psql:")
        print(f"psql {settings.SUPABASE_URL.replace('https://', 'postgresql://postgres@')} < {sql_file}")

    except Exception as e:
        print(f"Error: {e}")
        return False

    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/run_migration.py <migration_file>")
        sys.exit(1)

    sql_file = sys.argv[1]

    if not os.path.exists(sql_file):
        print(f"Error: File not found: {sql_file}")
        sys.exit(1)

    run_migration(sql_file)
