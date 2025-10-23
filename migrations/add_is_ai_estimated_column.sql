-- Add is_ai_estimated column to foods table
-- This column tracks whether nutrition data was AI-estimated or manually entered

ALTER TABLE foods
ADD COLUMN IF NOT EXISTS is_ai_estimated BOOLEAN DEFAULT false;

-- Add index for filtering AI-estimated foods
CREATE INDEX IF NOT EXISTS idx_foods_is_ai_estimated ON foods(is_ai_estimated);

-- Add comment
COMMENT ON COLUMN foods.is_ai_estimated IS 'True if nutrition values were estimated by AI (from log_meals_quick), false if manually entered or from verified database';
