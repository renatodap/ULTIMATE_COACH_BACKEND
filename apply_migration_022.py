"""
Quick script to apply migration 022 - Add system AI providers

This fixes the immediate production issue where canned responses
cannot be saved due to CHECK constraint violation.

Run: python apply_migration_022.py
"""

import os
from supabase import create_client

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("[ERROR] SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

migration_sql = """
-- Drop existing constraint
ALTER TABLE coach_messages
  DROP CONSTRAINT IF EXISTS coach_messages_ai_provider_check;

-- Add new constraint with additional providers
ALTER TABLE coach_messages
  ADD CONSTRAINT coach_messages_ai_provider_check
  CHECK (ai_provider IN ('anthropic', 'groq', 'openai', 'deepseek', 'canned', 'system'));
"""

print("[INFO] Applying migration 022: Add system AI providers")
print("=" * 60)

try:
    # Execute migration
    result = supabase.rpc('exec_sql', {'sql': migration_sql}).execute()

    print("[SUCCESS] Migration applied successfully!")
    print("\nNow 'canned' and 'system' are valid ai_provider values.")
    print("The coach can now save canned responses.")

except Exception as e:
    # Supabase doesn't have exec_sql RPC by default
    # Users need to apply via SQL Editor
    print("[WARNING] Cannot apply via Python client.")
    print("\nPlease apply manually via Supabase Dashboard:")
    print("1. Go to: https://supabase.com/dashboard")
    print("2. Select your project")
    print("3. Navigate to: SQL Editor")
    print("4. Paste and run this SQL:\n")
    print(migration_sql)
    print("\n" + "=" * 60)
    print("Or use the migration file: migrations/022_add_system_ai_providers.sql")
