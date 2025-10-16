-- ============================================================================
-- Migration 038: Fix Profile Creation
-- ============================================================================
-- Date: 2025-10-15
-- Description: Adds missing INSERT policy and trigger to auto-create profiles
--
-- PROBLEM:
-- - Users cannot create their own profiles (no INSERT policy)
-- - No trigger to auto-create profile when user signs up
-- - Onboarding fails with "Profile not found" error
--
-- SOLUTION:
-- 1. Add INSERT policy on profiles table (allow users to create own profile)
-- 2. Create trigger function to auto-create profile on signup
-- 3. Create trigger on auth.users table
-- ============================================================================

-- Add missing INSERT policy for profiles table
CREATE POLICY "Users can insert own profile"
  ON profiles FOR INSERT
  WITH CHECK (auth.uid() = id);

-- ============================================================================
-- Auto-create profile when user signs up
-- ============================================================================

-- Function to create profile when new user is created
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
SECURITY DEFINER  -- Run with privileges of function creator
SET search_path = public
LANGUAGE plpgsql
AS $$
BEGIN
  -- Insert new profile with user ID from auth.users
  INSERT INTO public.profiles (id, full_name, created_at, updated_at)
  VALUES (
    NEW.id,
    COALESCE(NEW.raw_user_meta_data->>'full_name', NULL),
    NOW(),
    NOW()
  );

  RETURN NEW;
EXCEPTION
  WHEN unique_violation THEN
    -- Profile already exists, ignore
    RETURN NEW;
  WHEN OTHERS THEN
    -- Log error but don't fail user creation
    RAISE WARNING 'Failed to create profile for user %: %', NEW.id, SQLERRM;
    RETURN NEW;
END;
$$;

-- Create trigger on auth.users table to auto-create profile
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_new_user();

-- ============================================================================
-- Verification
-- ============================================================================
-- After applying this migration:
-- 1. New users will automatically get a profile created on signup
-- 2. Users can INSERT their own profile if needed (RLS policy)
-- 3. Users can UPDATE their own profile (existing policy)
-- 4. Users can SELECT their own profile (existing policy)
--
-- To test:
-- 1. Create a new user via signup
-- 2. Check profiles table - should have a row with user's ID
-- 3. Try onboarding - should work without "Profile not found" error
-- ============================================================================
