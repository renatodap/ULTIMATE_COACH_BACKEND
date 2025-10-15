-- ============================================================================
-- Complete Meals Seeding Migration
-- ============================================================================
-- Version: 1.0.0
-- Created: 2025-10-13
-- Description: Full complete meals - stir-fries, pasta dishes, casseroles, bowls, comfort food
--
-- COVERS: Stir-fries, pasta entrees, casseroles, rice bowls, pot roast, stews, chili
-- All nutrition converted to per-100g for consistency
-- ============================================================================

-- ============================================================================
-- STIR-FRIES
-- ============================================================================

-- Beef and Broccoli
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Beef and Broccoli Stir-Fry',
    'ingredient',
    110.00, 10.00, 6.00, 5.00,
    1.50, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', '1 cup', 200.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'serving', '1 serving', 300.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- General Tso's Chicken
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'General Tso''s Chicken',
    'ingredient',
    195.00, 12.00, 18.00, 8.00,
    1.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', '1 cup', 146.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'serving', '1 serving', 220.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Kung Pao Chicken
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Kung Pao Chicken',
    'ingredient',
    160.00, 14.00, 10.00, 8.00,
    1.50, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', '1 cup', 162.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'serving', '1 serving', 243.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Teriyaki Chicken Stir-Fry
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Teriyaki Chicken Stir-Fry',
    'ingredient',
    130.00, 13.00, 11.00, 3.50,
    1.50, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', '1 cup', 200.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'serving', '1 serving', 300.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- ============================================================================
-- PASTA DISHES
-- ============================================================================

-- Spaghetti with Meatballs
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Spaghetti with Meatballs',
    'ingredient',
    134.00, 7.00, 16.00, 5.00,
    1.50, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', '1 cup', 248.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'serving', '1 serving', 372.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Baked Ziti
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Baked Ziti with Cheese',
    'ingredient',
    155.00, 8.00, 18.00, 6.00,
    1.50, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', '1 cup', 200.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'serving', '1 serving', 300.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Chicken Parmesan with Pasta
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Chicken Parmesan with Pasta',
    'ingredient',
    150.00, 11.00, 14.00, 6.00,
    1.50, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'serving', '1 serving (chicken + pasta)', 340.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Macaroni and Cheese (Homemade)
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Macaroni and Cheese, Homemade',
    'ingredient',
    164.00, 7.00, 18.00, 7.00,
    1.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', '1 cup', 200.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- ============================================================================
-- CASSEROLES
-- ============================================================================

-- Tuna Casserole
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Tuna Noodle Casserole',
    'ingredient',
    133.00, 8.00, 14.00, 5.00,
    1.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', '1 cup', 202.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Green Bean Casserole
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Green Bean Casserole',
    'ingredient',
    97.00, 2.50, 9.00, 6.00,
    1.80, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', '1 cup', 170.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Shepherd's Pie
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Shepherd''s Pie (with beef)',
    'ingredient',
    110.00, 7.00, 10.00, 5.00,
    1.50, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', '1 cup', 218.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'serving', '1 serving', 327.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- ============================================================================
-- RICE BOWLS
-- ============================================================================

-- Teriyaki Chicken Bowl
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Teriyaki Chicken Bowl (with rice and vegetables)',
    'ingredient',
    130.00, 10.00, 18.00, 2.50,
    1.50, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'bowl', '1 bowl', 400.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Beef Burrito Bowl
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Beef Burrito Bowl (with rice, beans, vegetables)',
    'ingredient',
    125.00, 8.00, 14.00, 4.50,
    3.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'bowl', '1 bowl', 450.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Poke Bowl (Ahi Tuna)
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Poke Bowl with Ahi Tuna (with rice)',
    'ingredient',
    140.00, 12.00, 15.00, 3.50,
    2.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'bowl', '1 bowl', 380.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- ============================================================================
-- COMFORT FOOD
-- ============================================================================

-- Pot Roast with Vegetables
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Pot Roast with Vegetables',
    'ingredient',
    120.00, 12.00, 6.00, 5.00,
    1.50, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'serving', '1 serving (4 oz meat + vegetables)', 200.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Meatloaf
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Meatloaf, Homemade',
    'ingredient',
    200.00, 16.00, 8.00, 11.00,
    0.80, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'slice', '1 slice (1" thick)', 108.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Chicken Pot Pie
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Chicken Pot Pie',
    'ingredient',
    200.00, 7.00, 18.00, 11.00,
    1.50, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', '1 cup', 252.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'serving', '1 serving (1/6 of pie)', 378.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Beef Stew
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Beef Stew, Homemade',
    'ingredient',
    87.00, 7.50, 7.00, 3.50,
    1.50, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', '1 cup', 245.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'bowl', '1 bowl', 367.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Chili with Beans
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Chili with Beans and Beef',
    'ingredient',
    118.00, 9.00, 13.00, 3.50,
    4.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', '1 cup', 253.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Pulled Pork Sandwich
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Pulled Pork Sandwich with BBQ Sauce',
    'ingredient',
    175.00, 12.00, 18.00, 6.00,
    1.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'sandwich', '1 sandwich', 250.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- ============================================================================
-- BREAKFAST MEALS
-- ============================================================================

-- Breakfast Burrito
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Breakfast Burrito (eggs, cheese, sausage)',
    'ingredient',
    210.00, 10.00, 18.00, 11.00,
    1.50, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'burrito', '1 burrito', 220.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Breakfast Scramble (Eggs, Bacon, Potatoes)
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Breakfast Scramble (eggs, bacon, potatoes)',
    'ingredient',
    145.00, 9.00, 10.00, 8.00,
    1.20, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'serving', '1 serving', 250.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Omelette (3 Eggs with Cheese and Vegetables)
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Omelette (3 eggs, cheese, vegetables)',
    'ingredient',
    154.00, 11.00, 3.00, 11.00,
    0.80, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'omelette', '1 omelette', 195.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- ============================================================================
-- SANDWICHES & WRAPS
-- ============================================================================

-- Club Sandwich
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Club Sandwich (turkey, bacon, lettuce, tomato)',
    'ingredient',
    185.00, 12.00, 17.00, 8.00,
    1.50, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'sandwich', '1 sandwich', 280.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Chicken Caesar Wrap
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Chicken Caesar Wrap',
    'ingredient',
    180.00, 12.00, 16.00, 8.00,
    2.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'wrap', '1 wrap', 260.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- BLT Sandwich
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'BLT Sandwich (bacon, lettuce, tomato, mayo)',
    'ingredient',
    210.00, 9.00, 20.00, 11.00,
    1.50, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'sandwich', '1 sandwich', 180.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
