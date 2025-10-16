# URGENT: Apply Migration 038 to Fix Profile Creation

## Problem
Users signing up and completing onboarding are getting a "Profile not found" error.

**Root Cause:**
1. The `profiles` table is missing an INSERT policy (users can't create their own profiles)
2. No trigger exists to automatically create profiles when users sign up
3. The `update_profile()` method tries to INSERT but RLS blocks it

## Solution
Migration `038_fix_profile_creation.sql` fixes this by:
1. Adding INSERT policy on profiles table
2. Creating `handle_new_user()` trigger function
3. Creating trigger on `auth.users` table to auto-create profiles

## How to Apply (Choose ONE option)

### Option 1: Supabase Dashboard (RECOMMENDED - Easiest)

1. Go to https://supabase.com/dashboard
2. Select your SHARPENED project
3. Navigate to **SQL Editor** (left sidebar)
4. Click **New Query**
5. Open `migrations/038_fix_profile_creation.sql` from this repo
6. Copy the entire file contents
7. Paste into the SQL Editor
8. Click **Run** (or press Ctrl/Cmd + Enter)
9. You should see "Success. No rows returned" or similar success message

**Verification:**
After applying, test by:
1. Create a new user via signup
2. Check the `profiles` table - should have a row with the user's ID
3. Try completing onboarding - should work without errors

---

### Option 2: Supabase CLI (If you have CLI installed)

```bash
# Navigate to backend directory
cd ULTIMATE_COACH_BACKEND

# Link to your project (if not already linked)
supabase link --project-ref YOUR_PROJECT_REF

# Apply the migration
psql "YOUR_DATABASE_CONNECTION_STRING" -f migrations/038_fix_profile_creation.sql
```

---

### Option 3: Direct PostgreSQL (Advanced)

```bash
# Get your database password from Supabase Dashboard
# Settings → Database → Connection string

psql "postgresql://postgres:[PASSWORD]@db.PROJECT_REF.supabase.co:5432/postgres" \
  -f migrations/038_fix_profile_creation.sql
```

---

## What This Migration Does

### 1. Adds INSERT Policy
```sql
CREATE POLICY "Users can insert own profile"
  ON profiles FOR INSERT
  WITH CHECK (auth.uid() = id);
```
**Effect:** Users can now create their own profile row (previously blocked by RLS)

### 2. Creates Trigger Function
```sql
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER ...
```
**Effect:** Automatically creates a profile when a new user signs up in Supabase Auth

### 3. Creates Trigger
```sql
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_new_user();
```
**Effect:** Links the function to the `auth.users` table

---

## After Applying

### Expected Behavior
- **New users:** Profile automatically created on signup ✓
- **Existing users:** Can update their profile (existing policy) ✓
- **Onboarding:** Will work without "Profile not found" error ✓

### Testing
1. Sign up a new test user
2. Check database: `SELECT * FROM profiles WHERE id = 'USER_ID';`
3. Should see a row with the user's ID and full_name (if provided)
4. Complete onboarding
5. Should save all onboarding data without errors

---

## Existing Users (Already Signed Up)

If you have existing users who signed up before this migration, they won't have profiles yet. The trigger only runs on **new** user creation.

**To fix existing users:**

Option A: They complete onboarding (the fallback INSERT in `update_profile()` will create the profile)

Option B: Manually create profiles for existing users:
```sql
INSERT INTO profiles (id, created_at, updated_at)
SELECT id, created_at, created_at
FROM auth.users
WHERE id NOT IN (SELECT id FROM profiles);
```

---

## Need Help?

If you encounter issues:
1. Check the Supabase logs (Dashboard → Logs → Database)
2. Verify RLS policies: `SELECT * FROM pg_policies WHERE tablename = 'profiles';`
3. Check trigger exists: `SELECT * FROM pg_trigger WHERE tgname = 'on_auth_user_created';`

**Contact:** persimmonautomation@gmail.com
