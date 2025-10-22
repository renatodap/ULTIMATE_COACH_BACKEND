-- Migration: Add completed_at columns to session_instances and meal_instances
-- Date: 2025-10-22
-- Purpose: Track completion status for workouts and meals in program plans

-- Add completed_at to session_instances
ALTER TABLE session_instances
ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ DEFAULT NULL;

-- Add completed_at to meal_instances
ALTER TABLE meal_instances
ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ DEFAULT NULL;

-- Create indexes for efficient queries on completed sessions/meals
CREATE INDEX IF NOT EXISTS idx_session_instances_completed
ON session_instances(program_id, completed_at)
WHERE completed_at IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_meal_instances_completed
ON meal_instances(program_id, completed_at)
WHERE completed_at IS NOT NULL;

-- Add comments
COMMENT ON COLUMN session_instances.completed_at IS 'Timestamp when user marked this session as complete';
COMMENT ON COLUMN meal_instances.completed_at IS 'Timestamp when user marked this meal as complete';
