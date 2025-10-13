-- ============================================================================
-- Migration 009: Food Composition Types and Quick Meals
-- ============================================================================
-- Created: 2025-10-13
-- Description: Adds support for composed foods, branded products, and user quick meals
--
-- CHANGES:
-- 1. Add composition_type to foods table
-- 2. Add recipe_items JSONB for composed foods
-- 3. Add servings_count and composed_total_grams for composed foods
-- 4. Create quick_meals table for user-specific meal templates
-- 5. Create quick_meal_foods junction table
-- ============================================================================

-- ============================================================================
-- 1. ALTER FOODS TABLE - Add Composition Support
-- ============================================================================

-- Add composition_type column
ALTER TABLE foods
  ADD COLUMN IF NOT EXISTS composition_type TEXT
    CHECK (composition_type IN ('simple', 'composed', 'branded'))
    DEFAULT 'simple';

-- Add recipe_items for composed foods (stores array of {food_id, grams})
ALTER TABLE foods
  ADD COLUMN IF NOT EXISTS recipe_items JSONB DEFAULT NULL;

-- Add servings count for composed foods (how many servings the recipe makes)
ALTER TABLE foods
  ADD COLUMN IF NOT EXISTS servings_count NUMERIC(10, 2) DEFAULT 1
    CHECK (servings_count > 0);

-- Add total grams for composed foods (total weight of all ingredients)
ALTER TABLE foods
  ADD COLUMN IF NOT EXISTS composed_total_grams NUMERIC(10, 2) DEFAULT NULL;

-- Add comment for documentation
COMMENT ON COLUMN foods.composition_type IS 'Type of food: simple (single ingredient), composed (recipe/meal template), branded (packaged product)';
COMMENT ON COLUMN foods.recipe_items IS 'For composed foods: JSON array of {food_id: uuid, grams: number}';
COMMENT ON COLUMN foods.servings_count IS 'For composed foods: number of servings this recipe makes';
COMMENT ON COLUMN foods.composed_total_grams IS 'For composed foods: total weight of all ingredients combined';

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_foods_composition_type ON foods(composition_type);
CREATE INDEX IF NOT EXISTS idx_foods_recipe_items ON foods USING GIN(recipe_items) WHERE recipe_items IS NOT NULL;

-- ============================================================================
-- 2. CREATE QUICK_MEALS TABLE
-- ============================================================================
-- User-specific meal templates (e.g., "My Breakfast", "Post-Workout Shake")
-- These are different from composed foods in the foods table because:
-- - They're user-specific (not shared publicly)
-- - They track usage and recency for smart suggestions
-- - They're simpler (just a list of foods to log together)
-- ============================================================================

CREATE TABLE IF NOT EXISTS quick_meals (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Basic Info
  name TEXT NOT NULL,
  description TEXT,

  -- Usage Tracking
  is_favorite BOOLEAN DEFAULT FALSE,
  usage_count INTEGER DEFAULT 0 CHECK (usage_count >= 0),
  last_used_at TIMESTAMPTZ,

  -- Metadata
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- 3. CREATE QUICK_MEAL_FOODS TABLE
-- ============================================================================
-- Junction table between quick_meals and foods
-- Stores what foods are in each quick meal and their quantities
-- ============================================================================

CREATE TABLE IF NOT EXISTS quick_meal_foods (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  quick_meal_id UUID NOT NULL REFERENCES quick_meals(id) ON DELETE CASCADE,
  food_id UUID NOT NULL REFERENCES foods(id) ON DELETE RESTRICT,

  -- Quantity Info
  quantity NUMERIC(10, 2) NOT NULL CHECK (quantity > 0),
  serving_id UUID REFERENCES food_servings(id) ON DELETE RESTRICT,

  -- Display Order
  display_order INTEGER DEFAULT 0,

  -- Metadata
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- 4. INDEXES FOR PERFORMANCE
-- ============================================================================

-- Quick Meals - Optimize for user's recent and favorite meals
CREATE INDEX IF NOT EXISTS idx_quick_meals_user_id ON quick_meals(user_id);
CREATE INDEX IF NOT EXISTS idx_quick_meals_user_usage ON quick_meals(user_id, usage_count DESC, last_used_at DESC);
CREATE INDEX IF NOT EXISTS idx_quick_meals_user_favorites ON quick_meals(user_id, is_favorite DESC, last_used_at DESC);

-- Quick Meal Foods
CREATE INDEX IF NOT EXISTS idx_quick_meal_foods_quick_meal_id ON quick_meal_foods(quick_meal_id);
CREATE INDEX IF NOT EXISTS idx_quick_meal_foods_food_id ON quick_meal_foods(food_id);

-- ============================================================================
-- 5. ROW LEVEL SECURITY
-- ============================================================================

-- Quick Meals - Users can only see their own
ALTER TABLE quick_meals ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own quick meals"
  ON quick_meals FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can create own quick meals"
  ON quick_meals FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own quick meals"
  ON quick_meals FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own quick meals"
  ON quick_meals FOR DELETE
  USING (auth.uid() = user_id);

-- Quick Meal Foods - Inherit permissions from quick_meals
ALTER TABLE quick_meal_foods ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view foods in own quick meals"
  ON quick_meal_foods FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM quick_meals
      WHERE quick_meals.id = quick_meal_foods.quick_meal_id
      AND quick_meals.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can add foods to own quick meals"
  ON quick_meal_foods FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM quick_meals
      WHERE quick_meals.id = quick_meal_foods.quick_meal_id
      AND quick_meals.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update foods in own quick meals"
  ON quick_meal_foods FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM quick_meals
      WHERE quick_meals.id = quick_meal_foods.quick_meal_id
      AND quick_meals.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can delete foods from own quick meals"
  ON quick_meal_foods FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM quick_meals
      WHERE quick_meals.id = quick_meal_foods.quick_meal_id
      AND quick_meals.user_id = auth.uid()
    )
  );

-- ============================================================================
-- 6. TRIGGERS
-- ============================================================================

-- Update updated_at on quick_meals
CREATE TRIGGER update_quick_meals_updated_at
  BEFORE UPDATE ON quick_meals
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();

-- ============================================================================
-- 7. EXAMPLE DATA INSERTS (commented out)
-- ============================================================================

-- Example 1: Simple food (already supported, no changes needed)
-- INSERT INTO foods (name, calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g, composition_type)
-- VALUES ('Chicken Breast (Raw)', 165, 31, 0, 3.6, 'simple');

-- Example 2: Composed food (meal template)
-- First, get the food_ids for chicken, rice, and broccoli
-- Then insert:
-- INSERT INTO foods (
--   name,
--   composition_type,
--   servings_count,
--   composed_total_grams,
--   recipe_items,
--   food_type,
--   is_public
-- ) VALUES (
--   'Grilled Chicken Rice Bowl',
--   'composed',
--   1,
--   300,
--   '[
--     {"food_id": "chicken-uuid-here", "grams": 100},
--     {"food_id": "rice-uuid-here", "grams": 100},
--     {"food_id": "broccoli-uuid-here", "grams": 100}
--   ]'::jsonb,
--   'dish',
--   TRUE
-- );

-- Example 3: Branded product
-- INSERT INTO foods (
--   name,
--   brand_name,
--   calories_per_100g,
--   protein_g_per_100g,
--   carbs_g_per_100g,
--   fat_g_per_100g,
--   composition_type,
--   food_type
-- ) VALUES (
--   'Chicken Bowl',
--   'Chipotle',
--   180,  -- 900 calories per 500g bowl = 180 per 100g
--   10,
--   20,
--   8,
--   'branded',
--   'restaurant'
-- );

-- Example 4: User quick meal
-- INSERT INTO quick_meals (user_id, name, description, is_favorite)
-- VALUES ('user-uuid-here', 'My Breakfast', 'Oats + Protein + Banana', TRUE)
-- RETURNING id;

-- Then add foods to the quick meal:
-- INSERT INTO quick_meal_foods (quick_meal_id, food_id, quantity, serving_id, display_order)
-- VALUES
--   ('quick-meal-id', 'oats-uuid', 50, 'grams-serving-id', 0),
--   ('quick-meal-id', 'protein-uuid', 1, 'scoop-serving-id', 1),
--   ('quick-meal-id', 'banana-uuid', 1, 'medium-serving-id', 2);

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
