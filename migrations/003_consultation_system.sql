-- ============================================================================
-- ULTIMATE COACH - First Consultation System
-- ============================================================================
-- Version: 1.0.0
-- Created: 2025-10-12
-- Description: Comprehensive consultation system with relational structure
--
-- KEY PRINCIPLES:
-- 1. All user answers reference database entries (foreign keys)
-- 2. No free text for exercises, foods, or modalities
-- 3. Link tables for many-to-many relationships
-- 4. Enables precise program generation and tracking
-- ============================================================================

-- ============================================================================
-- 1. REFERENCE TABLES (Master Data)
-- ============================================================================

-- Training Modalities (e.g., bodybuilding, CrossFit, powerlifting, endurance, sports)
CREATE TABLE IF NOT EXISTS training_modalities (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  name TEXT NOT NULL UNIQUE,
  description TEXT,
  typical_frequency_per_week INTEGER CHECK (typical_frequency_per_week >= 1 AND typical_frequency_per_week <= 7),
  equipment_required TEXT[] DEFAULT '{}',

  -- UI Display
  icon TEXT,
  display_order INTEGER DEFAULT 0,

  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_training_modalities_display_order ON training_modalities (display_order);

-- ============================================================================

-- Exercises (Comprehensive exercise library)
CREATE TABLE IF NOT EXISTS exercises (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  -- Basic Info
  name TEXT NOT NULL,
  description TEXT,

  -- Classification
  category TEXT NOT NULL CHECK (category IN (
    'compound_strength',      -- Squat, deadlift, bench press
    'isolation_strength',     -- Bicep curl, leg extension
    'cardio_steady_state',    -- Running, cycling, swimming
    'cardio_interval',        -- HIIT, sprints, circuits
    'flexibility',            -- Stretching, yoga poses
    'mobility',               -- Dynamic stretches, flow
    'sports_specific',        -- Tennis drills, basketball drills
    'core',                   -- Planks, crunches
    'plyometric',            -- Box jumps, burpees
    'olympic_lift',          -- Clean, snatch, jerk
    'bodyweight',            -- Push-ups, pull-ups
    'functional'             -- Kettlebell swings, TRX
  )),

  -- Muscle Groups (can be multiple)
  primary_muscle_groups TEXT[] DEFAULT '{}',
  secondary_muscle_groups TEXT[] DEFAULT '{}',

  -- Equipment
  equipment_needed TEXT[] DEFAULT '{}',  -- e.g., ['barbell', 'rack'], ['dumbbells'], ['bodyweight']
  equipment_optional TEXT[] DEFAULT '{}',

  -- Difficulty
  difficulty_level TEXT CHECK (difficulty_level IN ('beginner', 'intermediate', 'advanced', 'expert')),

  -- Metadata
  video_url TEXT,
  thumbnail_url TEXT,
  instructions TEXT,
  common_mistakes TEXT,

  -- Modality Associations
  primary_modalities TEXT[] DEFAULT '{}',  -- Which modalities commonly use this

  -- Popularity
  usage_count INTEGER DEFAULT 0,

  -- Visibility
  is_public BOOLEAN DEFAULT TRUE,
  verified BOOLEAN DEFAULT TRUE,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_exercises_category ON exercises (category);
CREATE INDEX IF NOT EXISTS idx_exercises_difficulty ON exercises (difficulty_level);
CREATE INDEX IF NOT EXISTS idx_exercises_name ON exercises USING GIN (to_tsvector_immutable(name));
CREATE INDEX IF NOT EXISTS idx_exercises_primary_muscle_groups ON exercises USING GIN (primary_muscle_groups);
CREATE INDEX IF NOT EXISTS idx_exercises_equipment ON exercises USING GIN (equipment_needed);

-- ============================================================================

-- Meal Times (Structured meal timing)
CREATE TABLE IF NOT EXISTS meal_times (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  -- Time Definition
  time_of_day TEXT NOT NULL CHECK (time_of_day IN (
    'early_morning',      -- 5-7am
    'breakfast',          -- 7-9am
    'mid_morning',        -- 9-11am
    'lunch',              -- 11am-1pm
    'afternoon',          -- 1-4pm
    'pre_workout',        -- Relative to workout
    'post_workout',       -- Relative to workout
    'dinner',             -- 5-8pm
    'evening',            -- 8-10pm
    'late_night'          -- 10pm+
  )) UNIQUE,

  -- Display
  label TEXT NOT NULL,                    -- e.g., "Early Morning (5-7am)"
  typical_hour INTEGER CHECK (typical_hour >= 0 AND typical_hour <= 23),  -- Representative hour
  description TEXT,

  display_order INTEGER DEFAULT 0,

  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================

-- Event Types (Events/goals users train for)
CREATE TABLE IF NOT EXISTS event_types (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  name TEXT NOT NULL UNIQUE,
  category TEXT CHECK (category IN (
    'race',               -- Marathon, 5K, triathlon
    'competition',        -- Powerlifting meet, CrossFit comp
    'sport_season',       -- Basketball season, tennis tournament
    'personal_milestone', -- First pull-up, 2x bodyweight squat
    'aesthetic_goal',     -- Beach vacation, photoshoot
    'health_goal'         -- Lower cholesterol, improve mobility
  )),

  typical_duration_weeks INTEGER,
  description TEXT,

  display_order INTEGER DEFAULT 0,

  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- 2. USER CONSULTATION LINK TABLES
-- ============================================================================

-- User's Training Modalities
CREATE TABLE IF NOT EXISTS user_training_modalities (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  modality_id UUID NOT NULL REFERENCES training_modalities(id) ON DELETE RESTRICT,

  -- Proficiency
  is_primary BOOLEAN DEFAULT FALSE,  -- Primary modality vs secondary
  proficiency_level TEXT CHECK (proficiency_level IN ('beginner', 'intermediate', 'advanced', 'expert')),
  years_experience INTEGER CHECK (years_experience >= 0 AND years_experience <= 50),

  -- Preferences
  enjoys_it BOOLEAN,  -- Do they enjoy this modality?
  willing_to_continue BOOLEAN DEFAULT TRUE,

  created_at TIMESTAMPTZ DEFAULT NOW(),

  UNIQUE (user_id, modality_id)
);

CREATE INDEX IF NOT EXISTS idx_user_training_modalities_user_id ON user_training_modalities (user_id);
CREATE INDEX IF NOT EXISTS idx_user_training_modalities_primary ON user_training_modalities (user_id) WHERE is_primary = TRUE;

-- RLS
ALTER TABLE user_training_modalities ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage own training modalities" ON user_training_modalities FOR ALL USING (auth.uid() = user_id);

-- ============================================================================

-- User's Familiar Exercises
CREATE TABLE IF NOT EXISTS user_familiar_exercises (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  exercise_id UUID NOT NULL REFERENCES exercises(id) ON DELETE RESTRICT,

  -- Familiarity
  comfort_level INTEGER CHECK (comfort_level >= 1 AND comfort_level <= 5),  -- 1=uncomfortable, 5=mastered
  last_performed_date DATE,
  frequency TEXT CHECK (frequency IN ('never_done', 'rarely', 'occasionally', 'regularly', 'frequently')),

  -- Performance Context
  typical_weight_kg NUMERIC(10, 2),  -- For strength exercises
  typical_reps INTEGER,
  typical_duration_minutes INTEGER,  -- For cardio exercises

  -- Preferences
  enjoys_it BOOLEAN,
  willing_to_do BOOLEAN DEFAULT TRUE,

  notes TEXT,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  UNIQUE (user_id, exercise_id)
);

CREATE INDEX IF NOT EXISTS idx_user_familiar_exercises_user_id ON user_familiar_exercises (user_id);
CREATE INDEX IF NOT EXISTS idx_user_familiar_exercises_comfort ON user_familiar_exercises (user_id, comfort_level);

-- RLS
ALTER TABLE user_familiar_exercises ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage own familiar exercises" ON user_familiar_exercises FOR ALL USING (auth.uid() = user_id);

-- ============================================================================

-- User's Preferred Meal Times
CREATE TABLE IF NOT EXISTS user_preferred_meal_times (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  meal_time_id UUID NOT NULL REFERENCES meal_times(id) ON DELETE RESTRICT,

  -- Meal Details
  typical_portion_size TEXT CHECK (typical_portion_size IN ('small', 'medium', 'large')),
  flexibility_minutes INTEGER DEFAULT 30,  -- How flexible is this meal time?
  is_non_negotiable BOOLEAN DEFAULT FALSE,  -- Must eat at this time

  -- Context
  notes TEXT,  -- e.g., "Always eat breakfast after morning workout"

  created_at TIMESTAMPTZ DEFAULT NOW(),

  UNIQUE (user_id, meal_time_id)
);

CREATE INDEX IF NOT EXISTS idx_user_preferred_meal_times_user_id ON user_preferred_meal_times (user_id);

-- RLS
ALTER TABLE user_preferred_meal_times ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage own preferred meal times" ON user_preferred_meal_times FOR ALL USING (auth.uid() = user_id);

-- ============================================================================

-- User's Typical Meal Foods
CREATE TABLE IF NOT EXISTS user_typical_meal_foods (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  food_id UUID NOT NULL REFERENCES foods(id) ON DELETE RESTRICT,
  meal_time_id UUID REFERENCES meal_times(id) ON DELETE SET NULL,  -- Optional: which meal

  -- Frequency
  frequency TEXT CHECK (frequency IN ('daily', 'several_times_week', 'weekly', 'occasionally')) NOT NULL,

  -- Typical Quantity
  typical_quantity_grams NUMERIC(10, 2),
  typical_serving_id UUID REFERENCES food_servings(id) ON DELETE SET NULL,

  -- Preferences
  enjoys_it BOOLEAN DEFAULT TRUE,
  willing_to_continue BOOLEAN DEFAULT TRUE,

  created_at TIMESTAMPTZ DEFAULT NOW(),

  UNIQUE (user_id, food_id, meal_time_id)
);

CREATE INDEX IF NOT EXISTS idx_user_typical_meal_foods_user_id ON user_typical_meal_foods (user_id);
CREATE INDEX IF NOT EXISTS idx_user_typical_meal_foods_frequency ON user_typical_meal_foods (user_id, frequency);

-- RLS
ALTER TABLE user_typical_meal_foods ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage own typical meal foods" ON user_typical_meal_foods FOR ALL USING (auth.uid() = user_id);

-- ============================================================================

-- User's Upcoming Events
CREATE TABLE IF NOT EXISTS user_upcoming_events (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  event_type_id UUID REFERENCES event_types(id) ON DELETE SET NULL,

  -- Event Details
  event_name TEXT NOT NULL,  -- e.g., "New York City Marathon", "Beach Vacation"
  event_date DATE,
  priority INTEGER CHECK (priority >= 1 AND priority <= 5) DEFAULT 3,  -- 1=low, 5=critical

  -- Goals
  specific_goals TEXT[],  -- e.g., ["Finish under 4 hours", "Look shredded"]

  -- Context
  notes TEXT,
  is_completed BOOLEAN DEFAULT FALSE,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_upcoming_events_user_id ON user_upcoming_events (user_id);
CREATE INDEX IF NOT EXISTS idx_user_upcoming_events_date ON user_upcoming_events (user_id, event_date);
CREATE INDEX IF NOT EXISTS idx_user_upcoming_events_priority ON user_upcoming_events (user_id, priority DESC);

-- RLS
ALTER TABLE user_upcoming_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage own upcoming events" ON user_upcoming_events FOR ALL USING (auth.uid() = user_id);

-- ============================================================================

-- User's Training Availability
CREATE TABLE IF NOT EXISTS user_training_availability (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Schedule
  day_of_week INTEGER CHECK (day_of_week >= 1 AND day_of_week <= 7) NOT NULL,  -- 1=Monday, 7=Sunday
  time_of_day TEXT CHECK (time_of_day IN ('early_morning', 'morning', 'midday', 'afternoon', 'evening', 'night')) NOT NULL,

  -- Duration
  typical_duration_minutes INTEGER CHECK (typical_duration_minutes >= 15 AND typical_duration_minutes <= 240),
  min_duration_minutes INTEGER,
  max_duration_minutes INTEGER,

  -- Location
  location_type TEXT CHECK (location_type IN ('home', 'gym', 'outdoor', 'office', 'flexible')),

  -- Flexibility
  is_flexible BOOLEAN DEFAULT TRUE,
  is_preferred BOOLEAN DEFAULT FALSE,  -- Ideal time vs just available

  notes TEXT,

  created_at TIMESTAMPTZ DEFAULT NOW(),

  UNIQUE (user_id, day_of_week, time_of_day)
);

CREATE INDEX IF NOT EXISTS idx_user_training_availability_user_id ON user_training_availability (user_id);
CREATE INDEX IF NOT EXISTS idx_user_training_availability_day ON user_training_availability (user_id, day_of_week);

-- RLS
ALTER TABLE user_training_availability ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage own training availability" ON user_training_availability FOR ALL USING (auth.uid() = user_id);

-- ============================================================================

-- User's Improvement Goals
CREATE TABLE IF NOT EXISTS user_improvement_goals (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Goal Classification
  goal_type TEXT CHECK (goal_type IN (
    'strength',           -- e.g., "Bench press 225 lbs"
    'endurance',          -- e.g., "Run a sub-20 5K"
    'skill',              -- e.g., "Master handstand push-ups"
    'aesthetic',          -- e.g., "Visible abs"
    'body_composition',   -- e.g., "Lose 15 lbs"
    'mobility',           -- e.g., "Touch toes without bending knees"
    'performance',        -- e.g., "Increase vertical jump by 4 inches"
    'health'              -- e.g., "Lower resting heart rate to 55"
  )) NOT NULL,

  -- Goal Details
  target_description TEXT NOT NULL,  -- Free text description
  measurement_metric TEXT,  -- e.g., "weight_kg", "reps", "time_seconds", "distance_meters"
  current_value NUMERIC(10, 2),
  target_value NUMERIC(10, 2),
  target_date DATE,

  -- Priority
  priority INTEGER CHECK (priority >= 1 AND priority <= 5) DEFAULT 3,

  -- Related Exercise (optional)
  exercise_id UUID REFERENCES exercises(id) ON DELETE SET NULL,

  notes TEXT,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_improvement_goals_user_id ON user_improvement_goals (user_id);
CREATE INDEX IF NOT EXISTS idx_user_improvement_goals_type ON user_improvement_goals (user_id, goal_type);
CREATE INDEX IF NOT EXISTS idx_user_improvement_goals_priority ON user_improvement_goals (user_id, priority DESC);

-- RLS
ALTER TABLE user_improvement_goals ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage own improvement goals" ON user_improvement_goals FOR ALL USING (auth.uid() = user_id);

-- ============================================================================

-- User's Difficulties (Challenges they face)
CREATE TABLE IF NOT EXISTS user_difficulties (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Difficulty Classification
  difficulty_category TEXT CHECK (difficulty_category IN (
    'motivation',         -- Hard to stay motivated
    'time_management',    -- Can't find time
    'injury',             -- Physical limitations
    'nutrition',          -- Trouble eating right
    'knowledge',          -- Don't know what to do
    'consistency',        -- Can't stay consistent
    'energy',             -- Always tired
    'social_support',     -- Lack of support
    'equipment_access',   -- Limited equipment
    'travel',             -- Travel frequently
    'other'
  )) NOT NULL,

  -- Details
  description TEXT NOT NULL,
  severity INTEGER CHECK (severity >= 1 AND severity <= 5) DEFAULT 3,  -- 1=minor, 5=major blocker

  -- Context
  frequency TEXT CHECK (frequency IN ('daily', 'weekly', 'monthly', 'occasionally')),
  triggers TEXT[],  -- What causes this difficulty

  -- Solutions Tried
  attempted_solutions TEXT[],
  what_worked TEXT,
  what_didnt_work TEXT,

  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_difficulties_user_id ON user_difficulties (user_id);
CREATE INDEX IF NOT EXISTS idx_user_difficulties_severity ON user_difficulties (user_id, severity DESC);

-- RLS
ALTER TABLE user_difficulties ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage own difficulties" ON user_difficulties FOR ALL USING (auth.uid() = user_id);

-- ============================================================================

-- User's Non-Negotiables (Hard constraints)
CREATE TABLE IF NOT EXISTS user_non_negotiables (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Constraint Type
  constraint_type TEXT CHECK (constraint_type IN (
    'rest_days',          -- e.g., "Sunday is always rest"
    'meal_timing',        -- e.g., "Can't eat after 7pm"
    'equipment',          -- e.g., "No access to barbell"
    'exercises_excluded', -- e.g., "No running due to knee"
    'foods_excluded',     -- e.g., "No dairy"
    'time_blocks',        -- e.g., "Can't train during work hours"
    'social',             -- e.g., "Dinner with family every night"
    'religious',          -- e.g., "No training on religious holidays"
    'medical',            -- e.g., "Blood pressure medication timing"
    'other'
  )) NOT NULL,

  -- Details
  description TEXT NOT NULL,
  reason TEXT,  -- Why is this non-negotiable?

  -- Related Entities
  excluded_exercise_ids UUID[],  -- Array of exercise IDs to exclude
  excluded_food_ids UUID[],      -- Array of food IDs to exclude

  -- Flexibility
  is_permanent BOOLEAN DEFAULT TRUE,  -- Permanent vs temporary constraint
  end_date DATE,  -- If temporary, when does it end?

  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_non_negotiables_user_id ON user_non_negotiables (user_id);
CREATE INDEX IF NOT EXISTS idx_user_non_negotiables_type ON user_non_negotiables (user_id, constraint_type);

-- RLS
ALTER TABLE user_non_negotiables ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage own non-negotiables" ON user_non_negotiables FOR ALL USING (auth.uid() = user_id);

-- ============================================================================
-- 3. CONSULTATION SESSION TRACKING
-- ============================================================================

CREATE TABLE IF NOT EXISTS consultation_sessions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Progress
  started_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ,
  current_section TEXT CHECK (current_section IN (
    'training_modalities',
    'exercise_familiarity',
    'training_schedule',
    'meal_timing',
    'typical_foods',
    'goals_events',
    'challenges',
    'review'
  )),
  progress_percentage INTEGER CHECK (progress_percentage >= 0 AND progress_percentage <= 100) DEFAULT 0,

  -- Metadata
  time_spent_minutes INTEGER DEFAULT 0,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_consultation_sessions_user_id ON consultation_sessions (user_id);
CREATE INDEX IF NOT EXISTS idx_consultation_sessions_completed ON consultation_sessions (user_id, completed_at);

-- RLS
ALTER TABLE consultation_sessions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage own consultation sessions" ON consultation_sessions FOR ALL USING (auth.uid() = user_id);

-- Add consultation_completed flag to profiles
ALTER TABLE profiles
  ADD COLUMN IF NOT EXISTS consultation_completed BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS consultation_completed_at TIMESTAMPTZ;

-- ============================================================================
-- 4. SEED DATA
-- ============================================================================

-- Training Modalities
INSERT INTO training_modalities (name, description, typical_frequency_per_week, equipment_required, display_order)
VALUES
  ('Bodybuilding', 'Hypertrophy-focused resistance training with isolation and compound movements', 5, ARRAY['dumbbells', 'barbells', 'machines', 'cables'], 1),
  ('Powerlifting', 'Strength training focused on squat, bench press, and deadlift', 4, ARRAY['barbells', 'rack', 'bench'], 2),
  ('CrossFit', 'High-intensity functional movements combining weightlifting, gymnastics, and cardio', 5, ARRAY['barbells', 'pull-up bar', 'rowing machine', 'jump rope'], 3),
  ('Olympic Weightlifting', 'Focused on clean & jerk and snatch movements', 4, ARRAY['barbells', 'bumper plates', 'platform'], 4),
  ('Endurance Running', 'Distance running for cardiovascular fitness', 4, ARRAY['running shoes'], 5),
  ('Cycling', 'Road or indoor cycling for cardiovascular and leg strength', 4, ARRAY['bicycle'], 6),
  ('Swimming', 'Full-body cardiovascular exercise in water', 3, ARRAY['pool access', 'goggles'], 7),
  ('Calisthenics', 'Bodyweight strength training and skill work', 5, ARRAY['pull-up bar', 'parallettes'], 8),
  ('Yoga', 'Mind-body practice focusing on flexibility, balance, and mindfulness', 3, ARRAY['yoga mat'], 9),
  ('Martial Arts', 'Combat sports training (boxing, BJJ, Muay Thai, etc.)', 4, ARRAY['gloves', 'mats'], 10),
  ('Team Sports', 'Basketball, soccer, tennis, volleyball, etc.', 3, ARRAY['sport-specific equipment'], 11),
  ('General Fitness', 'Mixed training for overall health and wellness', 4, ARRAY['minimal equipment'], 12)
ON CONFLICT (name) DO NOTHING;

-- Meal Times
INSERT INTO meal_times (time_of_day, label, typical_hour, description, display_order)
VALUES
  ('early_morning', 'Early Morning (5-7am)', 6, 'Before sunrise or early wake up', 1),
  ('breakfast', 'Breakfast (7-9am)', 8, 'Traditional breakfast time', 2),
  ('mid_morning', 'Mid-Morning Snack (9-11am)', 10, 'Between breakfast and lunch', 3),
  ('lunch', 'Lunch (11am-1pm)', 12, 'Midday meal', 4),
  ('afternoon', 'Afternoon Snack (1-4pm)', 3, 'Between lunch and dinner', 5),
  ('pre_workout', 'Pre-Workout', NULL, 'Before training (timing varies)', 6),
  ('post_workout', 'Post-Workout', NULL, 'After training (timing varies)', 7),
  ('dinner', 'Dinner (5-8pm)', 18, 'Evening meal', 8),
  ('evening', 'Evening Snack (8-10pm)', 21, 'After dinner', 9),
  ('late_night', 'Late Night (10pm+)', 23, 'Before bed', 10)
ON CONFLICT (time_of_day) DO NOTHING;

-- Event Types
INSERT INTO event_types (name, category, typical_duration_weeks, description, display_order)
VALUES
  ('5K Race', 'race', 8, 'Running race - 5 kilometers', 1),
  ('10K Race', 'race', 12, 'Running race - 10 kilometers', 2),
  ('Half Marathon', 'race', 16, '13.1 mile / 21.1 km race', 3),
  ('Marathon', 'race', 20, '26.2 mile / 42.2 km race', 4),
  ('Triathlon (Sprint)', 'race', 12, 'Swim/bike/run - sprint distance', 5),
  ('Triathlon (Olympic)', 'race', 16, 'Swim/bike/run - Olympic distance', 6),
  ('Triathlon (Half Ironman)', 'race', 20, '1.2mi swim, 56mi bike, 13.1mi run', 7),
  ('Triathlon (Ironman)', 'race', 24, '2.4mi swim, 112mi bike, 26.2mi run', 8),
  ('Powerlifting Meet', 'competition', 12, 'Test maximal squat, bench, deadlift', 9),
  ('CrossFit Competition', 'competition', 12, 'Mixed modality fitness competition', 10),
  ('Bodybuilding Show', 'competition', 20, 'Physique competition', 11),
  ('Sport Season', 'sport_season', 16, 'Basketball, soccer, tennis, etc.', 12),
  ('First Pull-Up', 'personal_milestone', 8, 'Achieve first unassisted pull-up', 13),
  ('First Muscle-Up', 'personal_milestone', 16, 'Achieve first muscle-up', 14),
  ('Handstand Push-Up', 'personal_milestone', 12, 'Achieve first handstand push-up', 15),
  ('Double Bodyweight Squat', 'personal_milestone', 24, 'Squat 2x bodyweight', 16),
  ('Beach Vacation', 'aesthetic_goal', 12, 'Look great for vacation', 17),
  ('Wedding', 'aesthetic_goal', 16, 'Look amazing for wedding day', 18),
  ('Photo Shoot', 'aesthetic_goal', 8, 'Professional photo shoot', 19),
  ('General Health Improvement', 'health_goal', 12, 'Improve overall health markers', 20),
  ('Weight Loss Goal', 'health_goal', 16, 'Sustainable weight loss', 21),
  ('Muscle Gain Goal', 'health_goal', 16, 'Build muscle mass', 22)
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- 5. TRIGGERS
-- ============================================================================

CREATE TRIGGER update_user_familiar_exercises_updated_at
  BEFORE UPDATE ON user_familiar_exercises
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_user_upcoming_events_updated_at
  BEFORE UPDATE ON user_upcoming_events
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_user_improvement_goals_updated_at
  BEFORE UPDATE ON user_improvement_goals
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_consultation_sessions_updated_at
  BEFORE UPDATE ON consultation_sessions
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_exercises_updated_at
  BEFORE UPDATE ON exercises
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================================
-- SUMMARY
-- ============================================================================
-- ✅ CONSULTATION SYSTEM FEATURES:
-- 1. All user answers reference database entries (foreign keys)
-- 2. No free text for exercises, foods, or modalities
-- 3. Link tables enable many-to-many relationships
-- 4. Seeded with common modalities, meal times, and event types
-- 5. Ready for AI program generation with precise data
--
-- NEXT STEPS:
-- 1. Seed exercises table (will need separate migration due to size)
-- 2. Create backend Pydantic models
-- 3. Build consultation API endpoints
-- 4. Create consultation UI with search/select components
-- ============================================================================
