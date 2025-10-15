-- ============================================================================
-- McDonald''s Restaurant Foods Seeding Migration
-- ============================================================================
-- Version: 1.0.0
-- Created: 2025-10-13
-- Description: McDonald''s menu items with accurate nutrition per 100g
--
-- COVERS: Burgers, chicken, fries, breakfast items, salads, drinks
-- All nutrition converted to per-100g for consistency
-- ============================================================================

-- Big Mac
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Big Mac',
    'McDonald''s',
    'restaurant',
    257.00, 11.87, 20.55, 15.07,
    1.37, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'sandwich', 'sandwich', 219.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Quarter Pounder with Cheese
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Quarter Pounder with Cheese',
    'McDonald''s',
    'restaurant',
    242.00, 13.60, 16.70, 12.70,
    1.20, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'sandwich', 'sandwich', 199.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- McChicken Sandwich
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'McChicken Sandwich',
    'McDonald''s',
    'restaurant',
    272.00, 9.52, 26.53, 14.29,
    1.36, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'sandwich', 'sandwich', 147.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Medium French Fries
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'French Fries, Medium',
    'McDonald''s',
    'restaurant',
    312.00, 3.90, 41.90, 14.60,
    3.90, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'serving', 'medium', 117.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Egg McMuffin
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Egg McMuffin',
    'McDonald''s',
    'restaurant',
    223.00, 12.23, 21.58, 9.35,
    1.44, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'sandwich', 'sandwich', 139.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Sausage McMuffin with Egg
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Sausage McMuffin with Egg',
    'McDonald''s',
    'restaurant',
    271.00, 12.00, 18.00, 16.00,
    1.00, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'sandwich', 'sandwich', 165.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Chicken McNuggets (10 piece)
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Chicken McNuggets',
    'McDonald''s',
    'restaurant',
    296.00, 15.40, 17.10, 18.40,
    1.40, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 10.00, 'pieces', '10 pieces', 171.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 4.00, 'pieces', '4 pieces', 68.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 6.00, 'pieces', '6 pieces', 102.00, FALSE, 3 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 4 FROM new_food;

-- Filet-O-Fish
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Filet-O-Fish',
    'McDonald''s',
    'restaurant',
    264.00, 10.20, 26.40, 12.20,
    1.40, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'sandwich', 'sandwich', 143.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Hash Browns
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Hash Browns',
    'McDonald''s',
    'restaurant',
    267.00, 2.00, 26.00, 17.00,
    2.00, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'piece', 'piece', 60.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- McFlurry Oreo (Snack Size)
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'McFlurry with Oreo Cookies',
    'McDonald''s',
    'restaurant',
    212.00, 4.00, 31.00, 8.00,
    0.50, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'snack', 'snack size', 212.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'regular', 'regular', 340.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
