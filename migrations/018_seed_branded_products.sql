-- ============================================================================
-- Branded Products Seeding Migration
-- ============================================================================
-- Version: 1.0.0
-- Created: 2025-10-13
-- Description: Popular branded food products - protein bars, granola bars, snacks, frozen meals
--
-- COVERS: Protein bars (Quest, RXBAR, Kind, Clif), granola bars, snack bars, frozen meals, yogurt products
-- All nutrition converted to per-100g for consistency
-- ============================================================================

-- ============================================================================
-- PROTEIN BARS
-- ============================================================================

-- Quest Bar - Chocolate Chip Cookie Dough
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Quest Protein Bar, Chocolate Chip Cookie Dough',
    'Quest Nutrition',
    'branded',
    333.00, 35.00, 35.00, 13.30,
    23.30, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'bar', 'bar', 60.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- RXBAR - Chocolate Sea Salt
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'RXBAR, Chocolate Sea Salt',
    'RXBAR',
    'branded',
    404.00, 23.10, 46.15, 13.46,
    5.77, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'bar', 'bar', 52.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Pure Protein Bar - Chocolate Peanut Butter
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Pure Protein Bar, Chocolate Peanut Butter',
    'Pure Protein',
    'branded',
    400.00, 40.00, 34.00, 12.00,
    2.00, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'bar', 'bar', 50.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- ONE Protein Bar - Birthday Cake
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'ONE Protein Bar, Birthday Cake',
    'ONE Brands',
    'branded',
    364.00, 29.10, 32.70, 12.70,
    14.50, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'bar', 'bar', 60.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- ============================================================================
-- GRANOLA & SNACK BARS
-- ============================================================================

-- KIND Bar - Dark Chocolate Nuts & Sea Salt
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'KIND Bar, Dark Chocolate Nuts & Sea Salt',
    'KIND',
    'branded',
    450.00, 15.00, 40.00, 32.50,
    7.50, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'bar', 'bar', 40.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Nature Valley Crunchy Granola Bar - Oats & Honey
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Nature Valley Granola Bar, Oats & Honey',
    'Nature Valley',
    'branded',
    429.00, 9.50, 66.70, 16.70,
    4.80, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 2.00, 'bars', '2 bars', 42.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'bar', '1 bar', 21.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Clif Bar - Chocolate Chip
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Clif Bar, Chocolate Chip',
    'Clif Bar',
    'branded',
    382.00, 14.70, 66.20, 7.40,
    7.40, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'bar', 'bar', 68.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- ============================================================================
-- YOGURT PRODUCTS
-- ============================================================================

-- Chobani Greek Yogurt - Strawberry
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Chobani Greek Yogurt, Strawberry',
    'Chobani',
    'branded',
    73.00, 8.00, 9.30, 0.00,
    0.00, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'container', 'container', 150.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Dannon Light & Fit Greek - Vanilla
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Dannon Light & Fit Greek, Vanilla',
    'Dannon',
    'branded',
    53.00, 8.00, 6.00, 0.00,
    0.00, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'container', 'container', 150.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- ============================================================================
-- FROZEN MEALS
-- ============================================================================

-- Lean Cuisine - Chicken Teriyaki
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Lean Cuisine, Chicken Teriyaki',
    'Lean Cuisine',
    'branded',
    87.00, 6.70, 12.00, 1.70,
    1.30, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'meal', 'meal', 283.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Healthy Choice - Grilled Chicken Marinara
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Healthy Choice, Grilled Chicken Marinara',
    'Healthy Choice',
    'branded',
    82.00, 7.30, 11.00, 1.80,
    2.40, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'meal', 'meal', 292.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- ============================================================================
-- SNACKS
-- ============================================================================

-- Hummus - Sabra Classic
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Hummus, Classic',
    'Sabra',
    'branded',
    250.00, 7.10, 14.30, 17.90,
    3.60, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 2.00, 'tbsp', '2 tbsp', 28.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Guacamole - Wholly Guacamole Classic
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Guacamole, Classic',
    'Wholly Guacamole',
    'branded',
    140.00, 2.00, 8.00, 12.00,
    5.00, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 2.00, 'tbsp', '2 tbsp', 28.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- String Cheese - Sargento
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'String Cheese, Mozzarella',
    'Sargento',
    'branded',
    286.00, 25.00, 3.60, 17.90,
    0.00, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'stick', 'stick', 28.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Pita Chips - Stacy''s Simply Naked
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Pita Chips, Simply Naked',
    'Stacy''s',
    'branded',
    464.00, 10.70, 64.30, 17.90,
    3.60, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'oz', '1 oz (about 10 chips)', 28.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
