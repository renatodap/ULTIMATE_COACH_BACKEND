"""
Admin Key Generator Script

Simple CLI tool to generate consultation keys manually.
Run this when a user requests access.

Usage:
    python -m app.admin.key_generator --email user@example.com --uses 1
    python -m app.admin.key_generator --description "Beta tester" --uses 5 --expires 7
"""

import argparse
import sys
from datetime import datetime, timedelta
from app.services.supabase_service import SupabaseService


def generate_key(
    description: str,
    max_uses: int = 1,
    expires_days: int | None = None,
    assigned_email: str | None = None,
):
    """
    Generate a consultation key.

    Args:
        description: Internal description (e.g., "Beta tester John")
        max_uses: Maximum number of uses (default: 1)
        expires_days: Days until expiration (default: None = no expiration)
        assigned_email: Assign to specific user email (default: None = open key)
    """
    db = SupabaseService()

    # If assigned to specific user, get user_id
    assigned_user_id = None
    if assigned_email:
        user_response = db.client.table("auth.users")\
            .select("id")\
            .eq("email", assigned_email)\
            .single()\
            .execute()

        if not user_response.data:
            print(f"❌ User not found: {assigned_email}")
            return None

        assigned_user_id = user_response.data["id"]
        print(f"✅ Found user: {assigned_email} ({assigned_user_id})")

    # Calculate expiration
    expires_at = None
    if expires_days:
        expires_at = (datetime.now() + timedelta(days=expires_days)).isoformat()

    # Generate key code
    key_code_response = db.client.rpc("generate_consultation_key_code").execute()
    key_code = key_code_response.data

    # Insert key
    key_data = {
        "key_code": key_code,
        "description": description,
        "max_uses": max_uses,
        "expires_at": expires_at,
        "assigned_to_user_id": assigned_user_id,
        "is_active": True,
    }

    response = db.client.table("consultation_keys")\
        .insert(key_data)\
        .execute()

    if response.data:
        key = response.data[0]
        print("\n" + "=" * 60)
        print("✨ CONSULTATION KEY GENERATED ✨")
        print("=" * 60)
        print(f"\n📋 KEY CODE: {key_code}")
        print(f"\n📝 Description: {description}")
        print(f"🔢 Max Uses: {max_uses}")

        if expires_days:
            print(f"⏰ Expires: {expires_days} days ({expires_at})")
        else:
            print(f"⏰ Expires: Never")

        if assigned_email:
            print(f"👤 Assigned to: {assigned_email}")
        else:
            print(f"👤 Assigned to: Anyone (first come, first serve)")

        print("\n" + "=" * 60)
        print("\n💬 Share this key with the user:")
        print(f"\n   {key_code}")
        print("\n" + "=" * 60 + "\n")

        return key_code
    else:
        print("❌ Failed to generate key")
        return None


def list_keys():
    """List all active consultation keys."""
    db = SupabaseService()

    response = db.client.table("consultation_keys")\
        .select("*")\
        .eq("is_active", True)\
        .order("created_at", desc=True)\
        .execute()

    if not response.data:
        print("No active keys found.")
        return

    print("\n" + "=" * 80)
    print("ACTIVE CONSULTATION KEYS")
    print("=" * 80)

    for key in response.data:
        usage = f"{key['current_uses']}/{key['max_uses']}"
        status = "🟢" if key['current_uses'] < key['max_uses'] else "🔴"

        print(f"\n{status} {key['key_code']}")
        print(f"   Description: {key['description']}")
        print(f"   Usage: {usage}")

        if key['expires_at']:
            print(f"   Expires: {key['expires_at']}")

        if key['assigned_to_user_id']:
            print(f"   Assigned to: {key['assigned_to_user_id']}")

        print(f"   Created: {key['created_at']}")

    print("\n" + "=" * 80 + "\n")


def deactivate_key(key_code: str):
    """Deactivate a consultation key."""
    db = SupabaseService()

    response = db.client.table("consultation_keys")\
        .update({"is_active": False})\
        .eq("key_code", key_code)\
        .execute()

    if response.data:
        print(f"✅ Key deactivated: {key_code}")
    else:
        print(f"❌ Key not found: {key_code}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate consultation keys for users"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Generate key command
    generate_parser = subparsers.add_parser("generate", help="Generate a new key")
    generate_parser.add_argument(
        "--description",
        "-d",
        required=True,
        help="Internal description (e.g., 'Beta tester John')"
    )
    generate_parser.add_argument(
        "--uses",
        "-u",
        type=int,
        default=1,
        help="Maximum number of uses (default: 1)"
    )
    generate_parser.add_argument(
        "--expires",
        "-e",
        type=int,
        help="Days until expiration (default: no expiration)"
    )
    generate_parser.add_argument(
        "--email",
        "-m",
        help="Assign to specific user email (default: open key)"
    )

    # List keys command
    subparsers.add_parser("list", help="List all active keys")

    # Deactivate key command
    deactivate_parser = subparsers.add_parser("deactivate", help="Deactivate a key")
    deactivate_parser.add_argument(
        "key_code",
        help="Key code to deactivate"
    )

    args = parser.parse_args()

    if args.command == "generate":
        generate_key(
            description=args.description,
            max_uses=args.uses,
            expires_days=args.expires,
            assigned_email=args.email,
        )
    elif args.command == "list":
        list_keys()
    elif args.command == "deactivate":
        deactivate_key(args.key_code)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

"""
# Generate a single-use key for a specific user:
python -m app.admin.key_generator generate \
    --description "Beta tester - John Doe" \
    --uses 1 \
    --email john@example.com

# Generate a multi-use key with expiration:
python -m app.admin.key_generator generate \
    --description "Launch week promotion" \
    --uses 10 \
    --expires 7

# List all active keys:
python -m app.admin.key_generator list

# Deactivate a key:
python -m app.admin.key_generator deactivate COACH-2025-ABC123XYZ
"""
