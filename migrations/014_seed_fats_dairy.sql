-- ============================================================================
-- Fats & Dairy Extended Seeding Migration
-- ============================================================================
-- Version: 1.0.0
-- Created: 2025-10-13
-- Description: Extended fats, oils, nuts, seeds, and dairy products
--
-- COVERS:
-- - Cheese varieties (mozzarella, parmesan, feta, swiss, provolone, gouda)
-- - Nut butters (almond, cashew, sunflower seed)
-- - Nuts (pecans, pistachios, macadamia, brazil nuts, hazelnuts)
-- - Seeds (flax, pumpkin, sunflower, hemp, sesame)
-- - Dairy (heavy cream, sour cream, half and half, milk varieties, yogurt)
-- - Oils (sesame, canola, vegetable)
--
-- NOTE: Skips duplicates from 007 (peanut butter, olive oil, butter, almonds,
--       walnuts, cashews, coconut oil, avocado oil, cheddar, cream cheese,
--       chia seeds, Greek yogurt, cottage cheese)
-- ============================================================================

-- ============================================================================
-- CHEESE VARIETIES
-- ============================================================================

-- Mozzarella Cheese, Part-Skim
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Mozzarella Cheese, Part-Skim',
    'ingredient',
    280.00, 24.30, 3.10, 17.10,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'oz', '1 oz', 28.35, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'cup', '1 cup shredded', 113.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Parmesan Cheese, Grated
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Parmesan Cheese, Grated',
    'ingredient',
    431.00, 38.50, 4.10, 28.60,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 2.00, 'tbsp', '2 tbsp', 10.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', '1 oz', 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Feta Cheese
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Feta Cheese',
    'ingredient',
    264.00, 14.20, 4.09, 21.30,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'oz', '1 oz', 28.35, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 0.25, 'cup', '1/4 cup crumbled', 38.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Swiss Cheese
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Swiss Cheese',
    'ingredient',
    380.00, 26.90, 5.40, 27.80,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'slice', 'slice', 28.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', '1 oz', 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Provolone Cheese
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Provolone Cheese',
    'ingredient',
    351.00, 25.60, 2.10, 26.60,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'slice', 'slice', 28.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', '1 oz', 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Blue Cheese
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Blue Cheese',
    'ingredient',
    353.00, 21.40, 2.34, 28.70,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'oz', '1 oz', 28.35, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 2.00, 'tbsp', '2 tbsp crumbled', 17.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- ============================================================================
-- NUT BUTTERS
-- ============================================================================

-- Almond Butter
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Almond Butter, Plain',
    'ingredient',
    614.00, 20.96, 18.82, 55.50,
    10.30, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 2.00, 'tbsp', '2 tbsp', 32.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'tbsp', '1 tbsp', 16.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Cashew Butter
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Cashew Butter, Plain',
    'ingredient',
    587.00, 17.60, 27.60, 49.40,
    2.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 2.00, 'tbsp', '2 tbsp', 32.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'tbsp', '1 tbsp', 16.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Sunflower Seed Butter
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Sunflower Seed Butter',
    'ingredient',
    582.00, 19.40, 24.10, 48.50,
    6.80, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 2.00, 'tbsp', '2 tbsp', 32.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'tbsp', '1 tbsp', 16.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- ============================================================================
-- NUTS
-- ============================================================================

-- Pecans, Raw
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Pecans, Raw',
    'ingredient',
    691.00, 9.17, 13.86, 71.97,
    9.60, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'oz', '1 oz (19 halves)', 28.35, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 0.25, 'cup', '1/4 cup', 27.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Pistachios, Raw
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Pistachios, Raw',
    'ingredient',
    562.00, 20.27, 27.51, 45.39,
    10.30, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'oz', '1 oz (49 kernels)', 28.35, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 0.25, 'cup', '1/4 cup', 31.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Macadamia Nuts, Raw
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Macadamia Nuts, Raw',
    'ingredient',
    718.00, 7.91, 13.82, 75.77,
    8.60, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'oz', '1 oz (10-12 nuts)', 28.35, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 0.25, 'cup', '1/4 cup', 34.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Brazil Nuts, Raw
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Brazil Nuts, Raw',
    'ingredient',
    656.00, 14.32, 12.27, 66.43,
    7.50, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'oz', '1 oz (6 nuts)', 28.35, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 6.00, 'nuts', '6 nuts', 28.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Hazelnuts, Raw
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Hazelnuts, Raw',
    'ingredient',
    628.00, 14.95, 16.70, 60.75,
    9.70, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'oz', '1 oz (21 nuts)', 28.35, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 0.25, 'cup', '1/4 cup', 34.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- ============================================================================
-- SEEDS
-- ============================================================================

-- Flax Seeds, Ground
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Flax Seeds, Ground',
    'ingredient',
    534.00, 18.29, 28.88, 42.16,
    27.30, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 2.00, 'tbsp', '2 tbsp', 14.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'tbsp', '1 tbsp', 7.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Pumpkin Seeds
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Pumpkin Seeds, Roasted',
    'ingredient',
    574.00, 29.84, 14.71, 49.05,
    6.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'oz', '1 oz', 28.35, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 0.25, 'cup', '1/4 cup', 32.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Sunflower Seeds
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Sunflower Seeds, Roasted',
    'ingredient',
    582.00, 19.33, 24.07, 49.80,
    11.10, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'oz', '1 oz', 28.35, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 0.25, 'cup', '1/4 cup', 32.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Hemp Seeds
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Hemp Seeds, Hulled',
    'ingredient',
    553.00, 31.56, 10.90, 48.75,
    4.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 3.00, 'tbsp', '3 tbsp', 30.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', '1 oz', 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Sesame Seeds
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Sesame Seeds, Whole, Roasted',
    'ingredient',
    565.00, 16.96, 25.74, 48.00,
    16.90, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'tbsp', '1 tbsp', 9.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', '1 oz', 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- ============================================================================
-- DAIRY PRODUCTS
-- ============================================================================

-- Heavy Cream
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Heavy Cream',
    'ingredient',
    345.00, 2.05, 2.79, 37.00,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 2.00, 'tbsp', '2 tbsp', 30.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'tbsp', '1 tbsp', 15.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Sour Cream
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Sour Cream',
    'ingredient',
    198.00, 2.44, 4.63, 19.35,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 2.00, 'tbsp', '2 tbsp', 30.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'tbsp', '1 tbsp', 15.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Half and Half
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Half and Half Cream',
    'ingredient',
    131.00, 3.05, 4.30, 11.50,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 2.00, 'tbsp', '2 tbsp', 30.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'tbsp', '1 tbsp', 15.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Whole Milk
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Milk, Whole, 3.25% Fat',
    'ingredient',
    61.00, 3.15, 4.80, 3.25,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', '1 cup', 244.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 0.50, 'cup', '1/2 cup', 122.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Skim Milk
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Milk, Nonfat (Skim)',
    'ingredient',
    34.00, 3.37, 4.96, 0.08,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', '1 cup', 244.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 0.50, 'cup', '1/2 cup', 122.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- ============================================================================
-- OILS
-- ============================================================================

-- Sesame Oil
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Sesame Oil',
    'ingredient',
    884.00, 0.00, 0.00, 100.00,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'tbsp', '1 tbsp', 13.60, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'tsp', '1 tsp', 4.50, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Canola Oil
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Canola Oil',
    'ingredient',
    884.00, 0.00, 0.00, 100.00,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'tbsp', '1 tbsp', 13.60, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'tsp', '1 tsp', 4.50, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Vegetable Oil
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Vegetable Oil',
    'ingredient',
    884.00, 0.00, 0.00, 100.00,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'tbsp', '1 tbsp', 13.60, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'tsp', '1 tsp', 4.50, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
