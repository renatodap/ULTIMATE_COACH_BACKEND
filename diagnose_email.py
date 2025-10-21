"""
Email Verification Diagnostic Script

Run this script to diagnose why verification emails are not being sent.
It will check all possible causes and provide specific fixes.

Usage:
    python diagnose_email.py
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")

def check_environment_variables():
    """Check if all required environment variables are set"""
    print_header("1. Checking Environment Variables")

    issues = []

    # Check SUPABASE_URL
    supabase_url = os.getenv('SUPABASE_URL')
    if not supabase_url:
        print_error("SUPABASE_URL is not set")
        issues.append("SUPABASE_URL missing")
    elif not supabase_url.startswith('https://'):
        print_error(f"SUPABASE_URL is invalid: {supabase_url}")
        issues.append("SUPABASE_URL invalid")
    else:
        print_success(f"SUPABASE_URL: {supabase_url}")

    # Check SUPABASE_SERVICE_KEY
    service_key = os.getenv('SUPABASE_SERVICE_KEY')
    if not service_key:
        print_error("SUPABASE_SERVICE_KEY is not set")
        issues.append("SUPABASE_SERVICE_KEY missing")
    else:
        print_success(f"SUPABASE_SERVICE_KEY: {service_key[:20]}...{service_key[-20:]}")

    # Check FRONTEND_URL
    frontend_url = os.getenv('FRONTEND_URL')
    if not frontend_url:
        print_warning("FRONTEND_URL is not set (emails will be sent without redirect URL)")
        print_info("  Add to .env: FRONTEND_URL=http://localhost:3000")
        issues.append("FRONTEND_URL missing (non-critical)")
    else:
        print_success(f"FRONTEND_URL: {frontend_url}")

    return issues, supabase_url, service_key

def check_supabase_connection(supabase_url, service_key):
    """Test Supabase connection"""
    print_header("2. Testing Supabase Connection")

    try:
        client: Client = create_client(supabase_url, service_key)
        print_success("Successfully connected to Supabase")

        # Test a simple query
        result = client.table('profiles').select('id').limit(1).execute()
        print_success(f"Database query successful (found {len(result.data)} profiles)")

        return client, []
    except Exception as e:
        print_error(f"Failed to connect to Supabase: {str(e)}")
        return None, [f"Connection failed: {str(e)}"]

def test_signup_flow(client: Client):
    """Test the signup flow to see what happens"""
    print_header("3. Testing Signup Flow")

    test_email = "test-diagnostic-" + str(os.urandom(4).hex()) + "@example.com"
    test_password = "TestPassword123!"

    print_info(f"Creating test account: {test_email}")

    issues = []

    try:
        # Get FRONTEND_URL for redirect
        frontend_url = os.getenv('FRONTEND_URL')

        signup_options = {
            "email": test_email,
            "password": test_password,
            "options": {
                "data": {
                    "full_name": "Diagnostic Test User"
                }
            }
        }

        if frontend_url:
            signup_options["options"]["email_redirect_to"] = f"{frontend_url}/auth/callback"
            print_info(f"Email redirect URL: {frontend_url}/auth/callback")
        else:
            print_warning("No FRONTEND_URL set - email will not have redirect URL")

        # Attempt signup
        response = client.auth.sign_up(signup_options)

        if not response.user:
            print_error("Signup failed - no user created")
            issues.append("Signup failed")
            return issues

        print_success(f"User created: {response.user.id}")

        # Check if session was created (indicates email confirmation is DISABLED)
        if response.session:
            print_warning("⚠️ CRITICAL: Session tokens were returned immediately")
            print_warning("⚠️ This means EMAIL CONFIRMATION is DISABLED in Supabase")
            print_warning("⚠️ NO EMAIL will be sent because Supabase skips confirmation")
            print("")
            print_error("ROOT CAUSE FOUND: Email confirmation is disabled")
            print_info("FIX: Go to Supabase Dashboard → Authentication → Providers → Email")
            print_info("     Enable 'Confirm email' toggle")
            issues.append("Email confirmation DISABLED in Supabase")
        else:
            print_success("No session returned - email confirmation is ENABLED")
            print_info("Email should have been sent (check spam folder)")
            print_info("If no email received, check Supabase dashboard → Logs → Auth logs")

        # Check email_confirmed_at
        if hasattr(response.user, 'email_confirmed_at') and response.user.email_confirmed_at:
            print_warning(f"Email already confirmed: {response.user.email_confirmed_at}")
        else:
            print_info("Email not yet confirmed (expected for new signup)")

        # Cleanup - delete test user
        try:
            # Note: We can't delete users via client SDK easily
            # User will remain in Supabase but that's okay for diagnostic
            print_info(f"Test user {test_email} created (cleanup not implemented)")
        except:
            pass

    except Exception as e:
        error_msg = str(e)
        print_error(f"Signup failed: {error_msg}")

        # Check for specific error patterns
        if "email rate limit" in error_msg.lower() or "rate limit" in error_msg.lower():
            print_error("⚠️ RATE LIMIT HIT")
            print_info("Supabase is rate limiting signups/emails")
            print_info("Wait 5-10 minutes and try again")
            issues.append("Rate limit hit")
        elif "email" in error_msg.lower() and "already" in error_msg.lower():
            print_warning("Email already registered (this is okay for diagnostic)")
        else:
            issues.append(f"Signup error: {error_msg}")

    return issues

def check_supabase_dashboard_settings():
    """Provide manual checklist for Supabase dashboard"""
    print_header("4. Supabase Dashboard Settings Checklist")

    print_info("You need to manually verify these settings in Supabase dashboard:")
    print("")
    print(f"{Colors.BOLD}Step 1: Navigate to Supabase Dashboard{Colors.ENDC}")
    print("  1. Go to https://supabase.com/dashboard")
    print("  2. Select your project")
    print("")
    print(f"{Colors.BOLD}Step 2: Check Email Confirmation Setting{Colors.ENDC}")
    print("  1. Click 'Authentication' in left sidebar")
    print("  2. Click 'Providers'")
    print("  3. Find 'Email' provider")
    print("  4. Verify 'Confirm email' toggle is ON (enabled)")
    print("     ⚠️  If this is OFF, NO verification emails will be sent!")
    print("")
    print(f"{Colors.BOLD}Step 3: Check Email Templates{Colors.ENDC}")
    print("  1. Click 'Authentication' → 'Email Templates'")
    print("  2. Find 'Confirm signup' template")
    print("  3. Verify it is ENABLED")
    print("  4. Verify it contains {{ .ConfirmationURL }} variable")
    print("")
    print(f"{Colors.BOLD}Step 4: Check URL Configuration{Colors.ENDC}")
    print("  1. Click 'Authentication' → 'URL Configuration'")
    print("  2. Verify 'Site URL' is set (e.g., http://localhost:3000)")
    print("  3. Add redirect URLs:")
    print("     - http://localhost:3000/auth/callback")
    print("     - http://localhost:3001/auth/callback (optional)")
    print("")
    print(f"{Colors.BOLD}Step 5: Check SMTP Settings (if using custom email){Colors.ENDC}")
    print("  1. Click 'Project Settings' → 'SMTP Settings'")
    print("  2. If custom SMTP configured, verify credentials are correct")
    print("  3. Send a test email to verify SMTP works")
    print("  Note: Free tier uses Supabase's default email (limited volume)")
    print("")
    print(f"{Colors.BOLD}Step 6: Check Auth Logs{Colors.ENDC}")
    print("  1. Click 'Authentication' → 'Logs' (or 'Logs' in sidebar)")
    print("  2. Look for recent signup events")
    print("  3. Check if any errors appear")
    print("  4. Look for 'email sent' events")
    print("")

def main():
    print(f"\n{Colors.BOLD}{Colors.OKCYAN}Email Verification Diagnostic Tool{Colors.ENDC}")
    print(f"{Colors.OKCYAN}This will help identify why verification emails are not being sent{Colors.ENDC}\n")

    all_issues = []

    # 1. Check environment variables
    env_issues, supabase_url, service_key = check_environment_variables()
    all_issues.extend(env_issues)

    if not supabase_url or not service_key:
        print_error("\n❌ Cannot proceed without SUPABASE_URL and SUPABASE_SERVICE_KEY")
        print_info("Add these to your .env file and run again")
        sys.exit(1)

    # 2. Test Supabase connection
    client, conn_issues = check_supabase_connection(supabase_url, service_key)
    all_issues.extend(conn_issues)

    if not client:
        print_error("\n❌ Cannot proceed without Supabase connection")
        sys.exit(1)

    # 3. Test signup flow
    signup_issues = test_signup_flow(client)
    all_issues.extend(signup_issues)

    # 4. Manual checklist
    check_supabase_dashboard_settings()

    # Summary
    print_header("Diagnostic Summary")

    if not all_issues:
        print_success("No obvious issues detected!")
        print_info("If emails still aren't being sent, check Supabase dashboard settings above")
    else:
        print_error(f"Found {len(all_issues)} potential issue(s):")
        for i, issue in enumerate(all_issues, 1):
            print(f"  {i}. {issue}")
        print("")

        # Check if critical issue found
        if any("Email confirmation DISABLED" in issue for issue in all_issues):
            print_error("⚠️  CRITICAL ISSUE FOUND: Email confirmation is disabled")
            print_info("This is why emails are not being sent!")
            print_info("Follow the fix instructions above")

    print("")
    print_info("Next steps:")
    print("  1. Review the issues above")
    print("  2. Check Supabase dashboard settings (Step 4)")
    print("  3. Enable email confirmation if disabled")
    print("  4. Test signup again")
    print("")

if __name__ == "__main__":
    main()
