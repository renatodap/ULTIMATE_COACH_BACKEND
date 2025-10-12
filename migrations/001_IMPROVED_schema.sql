-- ============================================================================
-- ULTIMATE COACH - IMPROVED Core Database Schema
-- ============================================================================
-- Version: 2.0.0
-- Created: 2025-10-12
-- Description: Production-grade schema with precise unit handling
--
-- KEY IMPROVEMENTS:
-- 1. Multiple serving sizes per food (scoop, cup, piece, oz, g)
-- 2. Explicit unit conversions (no ambiguity)
-- 3. Grams as canonical unit for calculations
-- 4. User can log in ANY unit, system converts precisely
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. USER PROFILES
-- ============================================================================

CREATE TABLE IF NOT EXISTS profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Basic Info
  full_name TEXT,
  avatar_url TEXT,

  -- Goals & Preferences
  primary_goal TEXT CHECK (primary_goal IN ('lose_weight', 'build_muscle', 'maintain', 'improve_performance')),
  experience_level TEXT CHECK (experience_level IN ('beginner', 'intermediate', 'advanced')) DEFAULT 'beginner',

  -- Calculated Metrics
  estimated_tdee INTEGER CHECK (estimated_tdee >= 1000 AND estimated_tdee <= 10000),
  daily_calorie_goal INTEGER CHECK (daily_calorie_goal >= 1000 AND daily_calorie_goal <= 10000),
  daily_protein_goal INTEGER CHECK (daily_protein_goal >= 50 AND daily_protein_goal <= 500),
  daily_carbs_goal INTEGER CHECK (daily_carbs_goal >= 50 AND daily_carbs_goal <= 800),
  daily_fat_goal INTEGER CHECK (daily_fat_goal >= 20 AND daily_fat_goal <= 300),

  -- Onboarding
  onboarding_completed BOOLEAN DEFAULT FALSE,
  onboarding_completed_at TIMESTAMPTZ,

  -- Preferences
  unit_system TEXT CHECK (unit_system IN ('metric', 'imperial')) DEFAULT 'imperial',
  timezone TEXT DEFAULT 'America/New_York',

  -- Metadata
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile"
  ON profiles FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON profiles FOR UPDATE USING (auth.uid() = id);

-- ============================================================================
-- 2. FOODS (Base food without serving info)
-- ============================================================================
-- CHANGED: Removed serving_size/unit, moved to food_servings table
-- ============================================================================

CREATE TABLE IF NOT EXISTS foods (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  -- Basic Info
  name TEXT NOT NULL,
  brand_name TEXT,

  -- Nutrition per 100g (CANONICAL BASE - all conversions derive from this)
  calories_per_100g NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (calories_per_100g >= 0),
  protein_g_per_100g NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (protein_g_per_100g >= 0),
  carbs_g_per_100g NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (carbs_g_per_100g >= 0),
  fat_g_per_100g NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (fat_g_per_100g >= 0),

  -- Optional Micros (per 100g)
  fiber_g_per_100g NUMERIC(10, 2) DEFAULT 0,
  sugar_g_per_100g NUMERIC(10, 2) DEFAULT 0,
  sodium_mg_per_100g NUMERIC(10, 2) DEFAULT 0,

  -- Metadata
  food_type TEXT CHECK (food_type IN ('ingredient', 'dish', 'branded', 'restaurant')),
  dietary_flags TEXT[],
  is_public BOOLEAN DEFAULT TRUE,
  verified BOOLEAN DEFAULT FALSE,
  usage_count INTEGER DEFAULT 0,

  -- Ownership
  created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- IMMUTABLE function for text search
CREATE OR REPLACE FUNCTION to_tsvector_immutable(text)
RETURNS tsvector
LANGUAGE sql
IMMUTABLE PARALLEL SAFE
AS $$
  SELECT to_tsvector('english', $1);
$$;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_foods_name ON foods USING GIN (to_tsvector_immutable(name));
CREATE INDEX IF NOT EXISTS idx_foods_is_public ON foods (is_public) WHERE is_public = TRUE;

-- RLS
ALTER TABLE foods ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public foods visible to all"
  ON foods FOR SELECT
  USING (is_public = TRUE OR created_by = auth.uid());

CREATE POLICY "Users can create custom foods"
  ON foods FOR INSERT
  WITH CHECK (created_by = auth.uid());

-- ============================================================================
-- 3. FOOD SERVINGS (Multiple serving sizes per food)
-- ============================================================================
-- NEW TABLE: Stores all possible ways to measure a food
-- Examples:
-- - Whey protein: 1 scoop = 30g
-- - Chicken breast: 1 medium breast = 174g, 1 oz = 28.35g
-- - Rice: 1 cup cooked = 158g, 1 oz = 28.35g
-- ============================================================================

CREATE TABLE IF NOT EXISTS food_servings (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  food_id UUID NOT NULL REFERENCES foods(id) ON DELETE CASCADE,

  -- Serving Definition
  serving_size NUMERIC(10, 2) NOT NULL CHECK (serving_size > 0),  -- e.g., 1, 2, 0.5
  serving_unit TEXT NOT NULL,  -- e.g., 'scoop', 'cup', 'oz', 'piece', 'tbsp'
  serving_label TEXT,  -- Optional: e.g., 'medium breast', 'heaping scoop'

  -- Conversion to Grams (CANONICAL)
  grams_per_serving NUMERIC(10, 2) NOT NULL CHECK (grams_per_serving > 0),

  -- Metadata
  is_default BOOLEAN DEFAULT FALSE,  -- One default per food for UI
  display_order INTEGER DEFAULT 0,

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),

  -- Constraint: Only one default serving per food
  CONSTRAINT unique_default_per_food UNIQUE (food_id, is_default)
    DEFERRABLE INITIALLY DEFERRED
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_food_servings_food_id ON food_servings (food_id);
CREATE INDEX IF NOT EXISTS idx_food_servings_default ON food_servings (food_id) WHERE is_default = TRUE;

-- No RLS (protected via foods RLS)

-- ============================================================================
-- 4. MEALS
-- ============================================================================

CREATE TABLE IF NOT EXISTS meals (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Meal Info
  name TEXT,
  meal_type TEXT CHECK (meal_type IN ('breakfast', 'lunch', 'dinner', 'snack', 'other')) NOT NULL,
  logged_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  notes TEXT,

  -- Nutrition Totals (calculated from meal_items)
  total_calories NUMERIC(10, 2) DEFAULT 0,
  total_protein_g NUMERIC(10, 2) DEFAULT 0,
  total_carbs_g NUMERIC(10, 2) DEFAULT 0,
  total_fat_g NUMERIC(10, 2) DEFAULT 0,

  -- AI Tracking
  source TEXT CHECK (source IN ('manual', 'ai_text', 'ai_voice', 'ai_photo', 'coach_chat')) DEFAULT 'manual',
  ai_confidence NUMERIC(3, 2) CHECK (ai_confidence >= 0 AND ai_confidence <= 1),
  ai_cost_usd NUMERIC(10, 6) DEFAULT 0,

  -- Metadata
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes (FIXED)
CREATE INDEX IF NOT EXISTS idx_meals_user_id ON meals (user_id);
CREATE INDEX IF NOT EXISTS idx_meals_logged_at ON meals (logged_at DESC);
CREATE INDEX IF NOT EXISTS idx_meals_user_logged_at ON meals (user_id, logged_at DESC);

-- RLS
ALTER TABLE meals ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own meals" ON meals FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can create own meals" ON meals FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own meals" ON meals FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own meals" ON meals FOR DELETE USING (auth.uid() = user_id);

-- ============================================================================
-- 5. MEAL ITEMS (IMPROVED with precise unit tracking)
-- ============================================================================
-- CHANGED: Now references food_servings for precise conversions
-- ============================================================================

CREATE TABLE IF NOT EXISTS meal_items (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  meal_id UUID NOT NULL REFERENCES meals(id) ON DELETE CASCADE,
  food_id UUID NOT NULL REFERENCES foods(id) ON DELETE RESTRICT,

  -- What the user logged
  quantity NUMERIC(10, 2) NOT NULL CHECK (quantity > 0),  -- e.g., 2 (scoops)
  serving_id UUID REFERENCES food_servings(id) ON DELETE RESTRICT,  -- Which serving they used

  -- Calculated at log time (stored for history/auditing)
  grams NUMERIC(10, 2) NOT NULL CHECK (grams > 0),  -- quantity * grams_per_serving
  calories NUMERIC(10, 2) NOT NULL DEFAULT 0,
  protein_g NUMERIC(10, 2) NOT NULL DEFAULT 0,
  carbs_g NUMERIC(10, 2) NOT NULL DEFAULT 0,
  fat_g NUMERIC(10, 2) NOT NULL DEFAULT 0,

  -- Display info (for UI, denormalized)
  display_unit TEXT NOT NULL,  -- e.g., "scoop", "cup", "oz"
  display_label TEXT,  -- e.g., "medium breast", "heaping scoop"

  -- Ordering
  display_order INTEGER DEFAULT 0,

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_meal_items_meal_id ON meal_items (meal_id);
CREATE INDEX IF NOT EXISTS idx_meal_items_food_id ON meal_items (food_id);
CREATE INDEX IF NOT EXISTS idx_meal_items_serving_id ON meal_items (serving_id);

-- ============================================================================
-- 6. ACTIVITIES
-- ============================================================================

CREATE TABLE IF NOT EXISTS activities (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Basic Info
  name TEXT NOT NULL,
  activity_type TEXT NOT NULL,
  start_time TIMESTAMPTZ NOT NULL,
  duration_minutes INTEGER CHECK (duration_minutes > 0),

  -- Performance Metrics
  distance_meters NUMERIC(10, 2),
  calories INTEGER,
  average_heart_rate INTEGER,
  max_heart_rate INTEGER,

  -- Subjective
  perceived_exertion INTEGER CHECK (perceived_exertion >= 1 AND perceived_exertion <= 10),
  notes TEXT,

  -- Strength-Specific
  exercises JSONB DEFAULT '[]',

  -- Activity-Type Specific Metrics (flexible structure)
  -- Examples:
  -- Swimming: {"laps": 40, "pool_length_meters": 25, "stroke_type": "freestyle"}
  -- Cycling: {"avg_speed_kph": 28.5, "elevation_gain_meters": 450, "avg_cadence": 85, "avg_power_watts": 220}
  -- Sports: {"sport": "basketball", "score_us": 92, "score_them": 88, "stats": {"points": 18, "rebounds": 7}}
  -- Intervals: {"rounds": 5, "work_seconds": 40, "rest_seconds": 20}
  metrics JSONB DEFAULT '{}',

  -- AI Tracking
  source TEXT CHECK (source IN ('manual', 'ai_text', 'ai_voice', 'garmin', 'strava')) DEFAULT 'manual',
  ai_confidence NUMERIC(3, 2) CHECK (ai_confidence >= 0 AND ai_confidence <= 1),
  ai_cost_usd NUMERIC(10, 6) DEFAULT 0,

  -- Metadata
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes (FIXED)
CREATE INDEX IF NOT EXISTS idx_activities_user_id ON activities (user_id);
CREATE INDEX IF NOT EXISTS idx_activities_start_time ON activities (start_time DESC);
CREATE INDEX IF NOT EXISTS idx_activities_user_start_time ON activities (user_id, start_time DESC);
CREATE INDEX IF NOT EXISTS idx_activities_metrics ON activities USING GIN (metrics);  -- For querying activity-specific metrics

-- RLS
ALTER TABLE activities ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own activities" ON activities FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can create own activities" ON activities FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own activities" ON activities FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own activities" ON activities FOR DELETE USING (auth.uid() = user_id);

-- ============================================================================
-- 7. COACH CONVERSATIONS & MESSAGES
-- ============================================================================

CREATE TABLE IF NOT EXISTS coach_conversations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  title TEXT,
  message_count INTEGER DEFAULT 0 CHECK (message_count >= 0),
  archived BOOLEAN DEFAULT FALSE,
  last_message_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_coach_conversations_user_id ON coach_conversations (user_id);
CREATE INDEX IF NOT EXISTS idx_coach_conversations_last_message ON coach_conversations (user_id, last_message_at DESC);

ALTER TABLE coach_conversations ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view own conversations" ON coach_conversations FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can create own conversations" ON coach_conversations FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own conversations" ON coach_conversations FOR UPDATE USING (auth.uid() = user_id);

CREATE TABLE IF NOT EXISTS coach_messages (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  conversation_id UUID NOT NULL REFERENCES coach_conversations(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  content TEXT NOT NULL,
  ai_provider TEXT CHECK (ai_provider IN ('anthropic', 'groq', 'openai', 'deepseek')),
  ai_model TEXT,
  tokens_used INTEGER DEFAULT 0,
  cost_usd NUMERIC(10, 6) DEFAULT 0,
  context_used JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_coach_messages_conversation_id ON coach_messages (conversation_id, created_at);
CREATE INDEX IF NOT EXISTS idx_coach_messages_user_id ON coach_messages (user_id);

-- ============================================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_meals_updated_at BEFORE UPDATE ON meals FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_activities_updated_at BEFORE UPDATE ON activities FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_coach_conversations_updated_at BEFORE UPDATE ON coach_conversations FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================================
-- EXAMPLE DATA: How to use the new schema
-- ============================================================================

-- Example 1: Whey Protein with multiple serving sizes
-- INSERT INTO foods (name, brand_name, calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g, food_type, is_public)
-- VALUES ('Whey Protein', 'Optimum Nutrition Gold Standard', 400, 80, 10, 5, 'branded', TRUE)
-- RETURNING id;  -- Returns food_id

-- Add serving sizes:
-- INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default)
-- VALUES
--   (food_id, 1, 'scoop', 'level scoop', 30, TRUE),
--   (food_id, 1, 'tbsp', NULL, 15, FALSE),
--   (food_id, 1, 'oz', NULL, 28.35, FALSE);

-- When user logs "2 scoops":
-- INSERT INTO meal_items (meal_id, food_id, quantity, serving_id, grams, display_unit, calories, protein_g)
-- VALUES (meal_id, food_id, 2, scoop_serving_id, 60, 'scoop', 240, 48);

-- Example 2: Activity with flexible metrics
-- Swimming workout:
-- INSERT INTO activities (user_id, name, activity_type, start_time, duration_minutes, distance_meters, calories, metrics)
-- VALUES (user_id, 'Morning Swim', 'swimming', NOW(), 45, 1000, 350,
--   '{"laps": 40, "pool_length_meters": 25, "stroke_type": "freestyle"}'::jsonb);

-- Cycling workout:
-- INSERT INTO activities (user_id, name, activity_type, start_time, duration_minutes, distance_meters, calories, metrics)
-- VALUES (user_id, 'Hill Ride', 'cycling', NOW(), 90, 35000, 650,
--   '{"avg_speed_kph": 28.5, "elevation_gain_meters": 450, "avg_cadence": 85, "avg_power_watts": 220}'::jsonb);

-- Basketball game:
-- INSERT INTO activities (user_id, name, activity_type, start_time, duration_minutes, calories, metrics)
-- VALUES (user_id, 'Pickup Game', 'basketball', NOW(), 60, 450,
--   '{"score_us": 92, "score_them": 88, "stats": {"points": 18, "rebounds": 7, "assists": 5}}'::jsonb);

-- Query activities with specific metrics:
-- SELECT * FROM activities WHERE metrics @> '{"stroke_type": "freestyle"}'::jsonb;
-- SELECT * FROM activities WHERE metrics->>'sport' = 'basketball';

-- ============================================================================
-- SUMMARY
-- ============================================================================
-- ✅ IMPROVEMENTS OVER PREVIOUS VERSION:
-- 1. Foods now have nutrition per 100g (canonical base)
-- 2. food_servings table allows unlimited serving sizes per food
-- 3. meal_items references specific serving_id for precision
-- 4. All conversions are explicit (no ambiguity)
-- 5. User can log in ANY unit, system converts to grams
-- 6. Historical data preserved (what user logged, not just grams)
-- 7. Easy to add new servings without changing food data
-- 8. Activities support flexible metrics JSONB for activity-type specific data
--
-- EXAMPLE USE CASES SOLVED:
-- ✅ NUTRITION: Log whey in scoops, tbsp, or oz
-- ✅ NUTRITION: Log chicken as filet, oz, or grams
-- ✅ NUTRITION: Log rice as cups, oz, or grams
-- ✅ NUTRITION: All conversions are deterministic and auditable
-- ✅ ACTIVITIES: Track swimming laps, cycling power/cadence, sports scores
-- ✅ ACTIVITIES: Flexible metrics support for any activity type
-- ============================================================================
