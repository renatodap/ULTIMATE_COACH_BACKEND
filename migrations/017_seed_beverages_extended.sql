-- ============================================================================
-- Beverages Extended Seeding Migration
-- ============================================================================
-- Version: 1.0.0
-- Created: 2025-10-13
-- Description: Extended beverage options including sodas, juices, energy drinks, sports drinks, coffee drinks
--
-- COVERS: Sodas, juices, energy drinks, sports drinks, coffee beverages, protein shakes
-- All nutrition converted to per-100g for consistency
-- ============================================================================

-- ============================================================================
-- SODAS & SOFT DRINKS
-- ============================================================================

-- Coca-Cola
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Coca-Cola Classic',
    'Coca-Cola',
    'branded',
    39.00, 0.00, 10.58, 0.00,
    0.00, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'can', '12 oz can', 355.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'bottle', '20 oz bottle', 591.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'ml', NULL, 100.00, FALSE, 3 FROM new_food;

-- Pepsi
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Pepsi Cola',
    'Pepsi',
    'branded',
    41.00, 0.00, 11.00, 0.00,
    0.00, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'can', '12 oz can', 355.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'bottle', '20 oz bottle', 591.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'ml', NULL, 100.00, FALSE, 3 FROM new_food;

-- Sprite
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Sprite',
    'Coca-Cola',
    'branded',
    37.00, 0.00, 10.00, 0.00,
    0.00, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'can', '12 oz can', 355.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'ml', NULL, 100.00, FALSE, 2 FROM new_food;

-- ============================================================================
-- JUICES
-- ============================================================================

-- Apple Juice
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, sugar_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Apple Juice, 100% Juice',
    'ingredient',
    46.00, 0.10, 11.30, 0.13,
    0.20, 9.62, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', '1 cup (8 oz)', 248.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'ml', NULL, 100.00, FALSE, 2 FROM new_food;

-- Cranberry Juice
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, sugar_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Cranberry Juice Cocktail',
    'ingredient',
    54.00, 0.00, 13.52, 0.10,
    0.00, 13.52, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', '1 cup (8 oz)', 253.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'ml', NULL, 100.00, FALSE, 2 FROM new_food;

-- ============================================================================
-- ENERGY DRINKS
-- ============================================================================

-- Red Bull
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Red Bull Energy Drink',
    'Red Bull',
    'branded',
    45.00, 0.40, 11.00, 0.00,
    0.00, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'can', '8.4 oz can', 248.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'ml', NULL, 100.00, FALSE, 2 FROM new_food;

-- Monster Energy
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Monster Energy Original',
    'Monster',
    'branded',
    46.00, 0.40, 11.20, 0.00,
    0.00, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'can', '16 oz can', 473.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'ml', NULL, 100.00, FALSE, 2 FROM new_food;

-- Celsius Energy Drink
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Celsius Energy Drink',
    'Celsius',
    'branded',
    4.00, 0.00, 0.80, 0.00,
    0.00, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'can', '12 oz can', 355.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'ml', NULL, 100.00, FALSE, 2 FROM new_food;

-- ============================================================================
-- SPORTS DRINKS
-- ============================================================================

-- Gatorade
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Gatorade Thirst Quencher',
    'Gatorade',
    'branded',
    24.00, 0.00, 6.00, 0.00,
    0.00, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'bottle', '20 oz bottle', 591.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'bottle', '32 oz bottle', 946.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'ml', NULL, 100.00, FALSE, 3 FROM new_food;

-- Powerade
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Powerade Sports Drink',
    'Powerade',
    'branded',
    27.00, 0.00, 7.00, 0.00,
    0.00, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'bottle', '20 oz bottle', 591.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'ml', NULL, 100.00, FALSE, 2 FROM new_food;

-- ============================================================================
-- PROTEIN SHAKES (Ready-to-Drink)
-- ============================================================================

-- Premier Protein Shake
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Premier Protein Shake, Chocolate',
    'Premier Protein',
    'branded',
    49.00, 9.23, 1.54, 0.92,
    0.31, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'bottle', '11 oz bottle', 325.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'ml', NULL, 100.00, FALSE, 2 FROM new_food;

-- Muscle Milk Pro Series
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Muscle Milk Pro Series, Vanilla',
    'Muscle Milk',
    'branded',
    56.00, 9.66, 1.93, 0.97,
    0.24, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'bottle', '14 oz bottle', 414.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'ml', NULL, 100.00, FALSE, 2 FROM new_food;

-- Fairlife Core Power
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Fairlife Core Power, Chocolate',
    'Fairlife',
    'branded',
    50.00, 7.65, 2.65, 1.32,
    0.00, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'bottle', '11.5 oz bottle', 340.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'ml', NULL, 100.00, FALSE, 2 FROM new_food;

-- ============================================================================
-- COFFEE DRINKS
-- ============================================================================

-- Starbucks Frappuccino Bottled
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Starbucks Frappuccino, Mocha',
    'Starbucks',
    'branded',
    64.00, 2.49, 11.74, 1.07,
    0.00, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'bottle', '9.5 oz bottle', 281.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'ml', NULL, 100.00, FALSE, 2 FROM new_food;

-- Cold Brew Coffee (Unsweetened)
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Cold Brew Coffee, Black, Unsweetened',
    'ingredient',
    2.00, 0.12, 0.00, 0.00,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', '8 oz', 237.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'bottle', '16 oz', 473.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'ml', NULL, 100.00, FALSE, 3 FROM new_food;

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
