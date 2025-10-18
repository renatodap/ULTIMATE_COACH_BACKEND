-- Migration: Add secondary_goal and fitness_notes to profiles table
-- Date: 2025-10-17
-- Purpose: Enhance onboarding to capture secondary fitness goals and user fitness notes

-- Add secondary_goal column
-- Nullable, same options as primary_goal but allows users to have a secondary objective
ALTER TABLE public.profiles
ADD COLUMN secondary_goal text
CHECK (secondary_goal = ANY (ARRAY[
  'lose_weight'::text,
  'build_muscle'::text,
  'maintain'::text,
  'improve_performance'::text
]));

-- Add fitness_notes column
-- Free-text field for users to provide any additional fitness context, considerations, injuries, etc.
ALTER TABLE public.profiles
ADD COLUMN fitness_notes text;

-- Add comment to document purpose
COMMENT ON COLUMN public.profiles.secondary_goal IS 'Optional secondary fitness goal (e.g., primary: build_muscle, secondary: lose_weight)';
COMMENT ON COLUMN public.profiles.fitness_notes IS 'Free-text field for user to provide any fitness-related context, injuries, preferences, or considerations';
