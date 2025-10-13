-- ============================================================================
-- Condiments & Sauces Seeding Migration
-- ============================================================================
-- Version: 1.0.0
-- Created: 2025-10-13
-- Description: Comprehensive condiments, sauces, dressings for nutrition tracking
--
-- COVERS: Ketchup, mustard, mayo, salad dressings, BBQ sauce, hot sauce, pasta sauces, Asian sauces
-- All nutrition converted to per-100g for consistency
-- ============================================================================

-- ============================================================================
-- KETCHUP & MUSTARD
-- ============================================================================

-- Heinz Tomato Ketchup
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, sugar_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Heinz Tomato Ketchup',
    'Heinz',
    'branded',
    100.00, 1.00, 25.00, 0.00,
    0.50, 22.00, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'tbsp', '1 tbsp', 17.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'packet', '1 packet', 9.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Yellow Mustard
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Yellow Mustard',
    'ingredient',
    60.00, 3.70, 5.30, 3.30,
    3.30, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'tsp', '1 tsp', 5.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'tbsp', '1 tbsp', 15.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Dijon Mustard
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Dijon Mustard',
    'ingredient',
    67.00, 4.00, 5.30, 4.00,
    4.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'tsp', '1 tsp', 5.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'tbsp', '1 tbsp', 15.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Spicy Brown Mustard
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Spicy Brown Mustard',
    'ingredient',
    67.00, 4.00, 6.70, 4.00,
    3.30, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'tsp', '1 tsp', 5.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- ============================================================================
-- MAYONNAISE
-- ============================================================================

-- Regular Mayonnaise
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Mayonnaise, Regular',
    'ingredient',
    680.00, 1.00, 2.70, 75.00,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'tbsp', '1 tbsp', 13.80, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'tsp', '1 tsp', 4.60, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Light Mayonnaise
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Mayonnaise, Light',
    'ingredient',
    360.00, 0.70, 13.30, 33.30,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'tbsp', '1 tbsp', 15.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Hellmann's Real Mayonnaise
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Hellmann''s Real Mayonnaise',
    'Hellmann''s',
    'branded',
    720.00, 0.00, 0.00, 80.00,
    0.00, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'tbsp', '1 tbsp', 13.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- ============================================================================
-- SALAD DRESSINGS
-- ============================================================================

-- Ranch Dressing
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Ranch Dressing',
    'ingredient',
    480.00, 1.40, 5.50, 50.00,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 2.00, 'tbsp', '2 tbsp', 30.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'tbsp', '1 tbsp', 15.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Caesar Dressing
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Caesar Dressing',
    'ingredient',
    467.00, 2.70, 6.70, 48.00,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 2.00, 'tbsp', '2 tbsp', 30.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'tbsp', '1 tbsp', 15.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Italian Dressing
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Italian Dressing',
    'ingredient',
    400.00, 0.00, 13.30, 40.00,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 2.00, 'tbsp', '2 tbsp', 30.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'tbsp', '1 tbsp', 15.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Balsamic Vinaigrette
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Balsamic Vinaigrette',
    'ingredient',
    267.00, 0.00, 20.00, 20.00,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 2.00, 'tbsp', '2 tbsp', 30.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'tbsp', '1 tbsp', 15.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Thousand Island Dressing
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Thousand Island Dressing',
    'ingredient',
    400.00, 0.70, 16.70, 36.70,
    0.70, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 2.00, 'tbsp', '2 tbsp', 30.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'tbsp', '1 tbsp', 15.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Blue Cheese Dressing
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Blue Cheese Dressing',
    'ingredient',
    500.00, 4.70, 7.00, 52.00,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 2.00, 'tbsp', '2 tbsp', 30.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'tbsp', '1 tbsp', 15.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Honey Mustard Dressing
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Honey Mustard Dressing',
    'ingredient',
    400.00, 0.70, 26.70, 32.00,
    0.70, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 2.00, 'tbsp', '2 tbsp', 30.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'tbsp', '1 tbsp', 15.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- ============================================================================
-- BBQ & HOT SAUCES
-- ============================================================================

-- BBQ Sauce (Sweet)
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, sugar_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'BBQ Sauce, Sweet',
    'ingredient',
    167.00, 0.70, 40.00, 0.70,
    1.30, 33.30, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 2.00, 'tbsp', '2 tbsp', 36.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'tbsp', '1 tbsp', 18.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Hot Sauce (Tabasco Style)
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Hot Sauce, Tabasco Style',
    'ingredient',
    20.00, 1.30, 0.80, 0.60,
    0.50, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'tsp', '1 tsp', 5.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'tbsp', '1 tbsp', 15.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Frank's RedHot Sauce
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Frank''s RedHot Original Cayenne Pepper Sauce',
    'Frank''s RedHot',
    'branded',
    7.00, 0.00, 0.00, 0.00,
    0.00, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'tsp', '1 tsp', 5.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'tbsp', '1 tbsp', 15.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Sriracha Hot Chili Sauce
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, sugar_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Sriracha Hot Chili Sauce',
    'ingredient',
    93.00, 2.00, 18.00, 0.70,
    1.30, 13.30, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'tsp', '1 tsp', 5.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'tbsp', '1 tbsp', 17.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Buffalo Wing Sauce
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Buffalo Wing Sauce',
    'ingredient',
    167.00, 1.30, 3.30, 16.70,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 2.00, 'tbsp', '2 tbsp', 30.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'tbsp', '1 tbsp', 15.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- ============================================================================
-- PASTA & TOMATO SAUCES
-- ============================================================================

-- Marinara Sauce
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Marinara Sauce',
    'ingredient',
    55.00, 1.50, 8.60, 2.10,
    1.50, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 0.50, 'cup', '1/2 cup', 125.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'cup', '1 cup', 250.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Alfredo Sauce
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Alfredo Sauce',
    'ingredient',
    167.00, 3.30, 6.70, 14.00,
    0.70, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 0.25, 'cup', '1/4 cup', 62.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 0.50, 'cup', '1/2 cup', 124.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Pesto Sauce (Basil)
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Pesto Sauce, Basil',
    'ingredient',
    500.00, 5.00, 5.00, 50.00,
    1.70, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 2.00, 'tbsp', '2 tbsp', 30.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'tbsp', '1 tbsp', 15.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Vodka Sauce
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Vodka Sauce',
    'ingredient',
    100.00, 2.00, 10.00, 6.00,
    1.30, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 0.50, 'cup', '1/2 cup', 125.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- ============================================================================
-- ASIAN SAUCES
-- ============================================================================

-- Soy Sauce (Regular)
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Soy Sauce, Regular',
    'ingredient',
    53.00, 5.30, 4.70, 0.00,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'tbsp', '1 tbsp', 18.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'tsp', '1 tsp', 6.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Teriyaki Sauce
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, sugar_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Teriyaki Sauce',
    'ingredient',
    93.00, 6.00, 16.00, 0.70,
    0.00, 13.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'tbsp', '1 tbsp', 18.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 2.00, 'tbsp', '2 tbsp', 36.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Hoisin Sauce
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, sugar_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Hoisin Sauce',
    'ingredient',
    220.00, 2.00, 46.00, 2.00,
    2.00, 33.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'tbsp', '1 tbsp', 18.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Sweet Chili Sauce
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, sugar_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Sweet Chili Sauce, Thai Style',
    'ingredient',
    233.00, 0.70, 56.70, 0.00,
    0.70, 50.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'tbsp', '1 tbsp', 18.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- ============================================================================
-- OTHER CONDIMENTS
-- ============================================================================

-- Sweet Pickle Relish
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, sugar_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Sweet Pickle Relish',
    'ingredient',
    107.00, 0.50, 28.00, 0.30,
    1.00, 23.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'tbsp', '1 tbsp', 15.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Tartar Sauce
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Tartar Sauce',
    'ingredient',
    400.00, 0.70, 10.00, 40.00,
    0.70, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 2.00, 'tbsp', '2 tbsp', 28.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'tbsp', '1 tbsp', 14.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Cocktail Sauce
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, sugar_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Cocktail Sauce',
    'ingredient',
    100.00, 1.30, 24.00, 0.30,
    0.70, 18.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 2.00, 'tbsp', '2 tbsp', 31.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'tbsp', '1 tbsp', 15.50, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Worcestershire Sauce
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Worcestershire Sauce',
    'ingredient',
    78.00, 0.00, 19.00, 0.00,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'tsp', '1 tsp', 5.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'tbsp', '1 tbsp', 17.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Salsa (Mild)
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Salsa, Mild',
    'ingredient',
    30.00, 1.30, 6.70, 0.00,
    1.30, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 2.00, 'tbsp', '2 tbsp', 32.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 0.25, 'cup', '1/4 cup', 65.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
