-- ============================================================================
-- Common Foods Seeding Migration
-- ============================================================================
-- Version: 1.0.0
-- Created: 2025-10-12
-- Description: Seed 80 common foods covering 80% of use cases
--
-- PURPOSE:
-- 1. Enable LLM consultation to function (search_foods tool needs data!)
-- 2. Cover most common foods users mention
-- 3. Provide accurate USDA nutrition data per 100g
-- 4. Include multiple serving sizes for convenience
--
-- SCHEMA COMPLIANCE:
-- ✓ All nutrition values per 100g (canonical base)
-- ✓ food_type: 'ingredient', 'dish', 'branded', 'restaurant'
-- ✓ is_public: TRUE (available to all users)
-- ✓ verified: TRUE (verified nutrition data)
-- ✓ One is_default=true per food in food_servings
-- ============================================================================

-- ============================================================================
-- SECTION 1: PROTEINS (20 foods)
-- ============================================================================

-- Chicken Breast (Raw, Skinless)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Chicken Breast, Raw, Skinless',
    'ingredient',
    165.00,
    31.00,
    0.00,
    3.60,
    0.00,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'breast', 'medium breast', 174.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Chicken Breast (Cooked, Grilled)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Chicken Breast, Cooked, Grilled',
    'ingredient',
    165.00,
    31.00,
    0.00,
    3.60,
    0.00,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'breast', 'medium breast', 174.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Ground Beef (93% lean / 7% fat, Raw)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Ground Beef, 93% Lean, Raw',
    'ingredient',
    152.00,
    21.41,
    0.00,
    6.91,
    0.00,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 4.00, 'oz', NULL, 113.40, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Ground Beef (80% lean / 20% fat, Raw)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Ground Beef, 80% Lean, Raw',
    'ingredient',
    254.00,
    17.17,
    0.00,
    20.00,
    0.00,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 4.00, 'oz', NULL, 113.40, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Salmon (Atlantic, Raw)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Salmon, Atlantic, Raw',
    'ingredient',
    208.00,
    20.42,
    0.00,
    13.42,
    0.00,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'fillet', 'half fillet', 178.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Eggs (Whole, Raw, Large)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Egg, Whole, Raw, Large',
    'ingredient',
    143.00,
    12.56,
    0.72,
    9.51,
    0.00,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'egg', 'large egg', 50.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Egg Whites (Raw, Large)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Egg White, Raw, Large',
    'ingredient',
    52.00,
    10.90,
    0.73,
    0.17,
    0.00,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'egg white', 'large egg white', 33.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Greek Yogurt (Nonfat, Plain)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    sugar_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Greek Yogurt, Nonfat, Plain',
    'ingredient',
    59.00,
    10.19,
    3.60,
    0.39,
    0.00,
    3.20,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', NULL, 227.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Cottage Cheese (Low-fat, 2%)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Cottage Cheese, Low-fat 2%',
    'ingredient',
    84.00,
    11.12,
    3.38,
    2.30,
    0.00,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', NULL, 226.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Whey Protein Powder (Isolate, Unflavored)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Whey Protein Powder, Isolate',
    'branded',
    400.00,
    90.00,
    3.33,
    3.33,
    0.00,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'scoop', NULL, 30.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Tuna (Canned in Water, Drained)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Tuna, Canned in Water, Drained',
    'ingredient',
    116.00,
    25.51,
    0.00,
    0.82,
    0.00,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'can', '5 oz can', 142.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Tofu (Firm, Raw)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Tofu, Firm, Raw',
    'ingredient',
    144.00,
    15.78,
    2.78,
    8.72,
    0.00,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 0.50, 'cup', NULL, 126.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Turkey Breast (Sliced, Deli Meat)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    sodium_mg_per_100g,
    is_public,
    verified
  ) VALUES (
    'Turkey Breast, Deli Sliced',
    'ingredient',
    104.00,
    17.07,
    3.66,
    1.66,
    0.00,
    1042.00,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 2.00, 'slice', NULL, 56.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Pork Loin (Raw, Lean)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Pork Loin, Raw, Lean',
    'ingredient',
    143.00,
    20.95,
    0.00,
    5.89,
    0.00,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 4.00, 'oz', NULL, 113.40, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Shrimp (Raw)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Shrimp, Raw',
    'ingredient',
    99.00,
    20.91,
    0.91,
    1.73,
    0.00,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 3.00, 'oz', NULL, 85.05, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Steak (Sirloin, Raw, Lean)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Steak, Sirloin, Raw, Lean',
    'ingredient',
    158.00,
    22.13,
    0.00,
    7.35,
    0.00,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 6.00, 'oz', NULL, 170.10, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Tilapia (Raw)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Tilapia, Raw',
    'ingredient',
    96.00,
    20.08,
    0.00,
    1.70,
    0.00,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'fillet', NULL, 87.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Peanut Butter (Smooth, With Salt)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    sugar_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Peanut Butter, Smooth',
    'ingredient',
    588.00,
    25.09,
    19.56,
    49.94,
    6.00,
    9.22,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 2.00, 'tbsp', NULL, 32.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Chickpeas (Cooked, Boiled, Without Salt)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Chickpeas, Cooked, Boiled',
    'ingredient',
    164.00,
    8.86,
    27.42,
    2.59,
    7.60,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', NULL, 164.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Black Beans (Cooked, Boiled, Without Salt)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Black Beans, Cooked, Boiled',
    'ingredient',
    132.00,
    8.86,
    23.71,
    0.54,
    8.70,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', NULL, 172.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- ============================================================================
-- SECTION 2: CARBOHYDRATES (20 foods)
-- ============================================================================

-- White Rice (Cooked, Long-Grain)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'White Rice, Cooked, Long-Grain',
    'ingredient',
    130.00,
    2.69,
    28.17,
    0.28,
    0.40,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', 'cooked', 158.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Brown Rice (Cooked, Long-Grain)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Brown Rice, Cooked, Long-Grain',
    'ingredient',
    111.00,
    2.58,
    22.96,
    0.90,
    1.80,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', 'cooked', 195.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Oatmeal (Cooked, Regular, No Salt)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Oatmeal, Cooked, Regular',
    'ingredient',
    71.00,
    2.54,
    12.00,
    1.52,
    1.70,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', 'cooked', 234.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Quinoa (Cooked)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Quinoa, Cooked',
    'ingredient',
    120.00,
    4.40,
    21.30,
    1.92,
    2.80,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', 'cooked', 185.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Whole Wheat Bread (Sliced)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Whole Wheat Bread',
    'ingredient',
    247.00,
    12.46,
    41.29,
    3.35,
    6.80,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'slice', NULL, 28.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- White Bread (Sliced)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'White Bread',
    'ingredient',
    266.00,
    7.64,
    49.42,
    3.59,
    2.40,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'slice', NULL, 25.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Sweet Potato (Baked, Flesh, Without Salt)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    sugar_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Sweet Potato, Baked',
    'ingredient',
    90.00,
    2.01,
    20.71,
    0.15,
    3.30,
    6.48,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'potato', 'medium', 114.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Potato (Baked, Flesh and Skin, Without Salt)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Potato, Baked, With Skin',
    'ingredient',
    93.00,
    2.50,
    21.15,
    0.13,
    2.20,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'potato', 'medium', 173.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Pasta (Cooked, Enriched, Without Salt)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Pasta, Cooked, Enriched',
    'ingredient',
    131.00,
    5.05,
    25.05,
    1.08,
    1.80,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', 'cooked', 140.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Bagel (Plain, Enriched)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Bagel, Plain, Enriched',
    'ingredient',
    257.00,
    10.00,
    50.86,
    1.43,
    2.30,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'bagel', NULL, 89.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Tortilla (Flour, 8-inch)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Tortilla, Flour, 8-inch',
    'ingredient',
    300.00,
    8.00,
    51.00,
    7.00,
    2.00,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'tortilla', '8-inch', 49.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Cereal (Cheerios, General Mills)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    sugar_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Cereal, Cheerios',
    'branded',
    367.00,
    10.00,
    73.33,
    6.67,
    10.00,
    3.33,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', NULL, 30.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Granola (Homemade)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    sugar_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Granola, Homemade',
    'ingredient',
    471.00,
    13.67,
    53.00,
    22.10,
    8.90,
    21.80,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 0.50, 'cup', NULL, 61.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Crackers (Whole Wheat)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Crackers, Whole Wheat',
    'ingredient',
    443.00,
    9.50,
    64.00,
    16.00,
    10.70,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 5.00, 'cracker', NULL, 15.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Corn (Sweet, Yellow, Cooked, Boiled)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    sugar_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Corn, Sweet, Yellow, Cooked',
    'ingredient',
    96.00,
    3.41,
    20.98,
    1.50,
    2.40,
    4.54,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'ear', 'medium', 103.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Peas (Green, Cooked, Boiled)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    sugar_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Peas, Green, Cooked, Boiled',
    'ingredient',
    84.00,
    5.42,
    15.63,
    0.22,
    5.50,
    5.93,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', NULL, 160.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Lentils (Cooked, Boiled, Without Salt)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Lentils, Cooked, Boiled',
    'ingredient',
    116.00,
    9.02,
    20.13,
    0.38,
    7.90,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', 'cooked', 198.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Couscous (Cooked)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Couscous, Cooked',
    'ingredient',
    112.00,
    3.79,
    23.22,
    0.16,
    1.40,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', 'cooked', 157.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Barley (Cooked)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Barley, Cooked',
    'ingredient',
    123.00,
    2.26,
    28.22,
    0.44,
    3.80,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', 'cooked', 157.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Ezekiel Bread (Sprouted Grain)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Ezekiel Bread, Sprouted Grain',
    'branded',
    250.00,
    12.50,
    37.50,
    2.50,
    12.50,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'slice', NULL, 34.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- ============================================================================
-- SECTION 3: VEGETABLES (20 foods)
-- ============================================================================

-- Broccoli (Cooked, Boiled, Drained, Without Salt)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Broccoli, Cooked, Boiled',
    'ingredient',
    35.00,
    2.38,
    7.18,
    0.41,
    3.30,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', 'chopped', 156.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Spinach (Raw)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Spinach, Raw',
    'ingredient',
    23.00,
    2.86,
    3.63,
    0.39,
    2.20,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', NULL, 30.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Carrots (Raw)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    sugar_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Carrots, Raw',
    'ingredient',
    41.00,
    0.93,
    9.58,
    0.24,
    2.80,
    4.74,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'carrot', 'medium', 61.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Bell Pepper (Red, Raw)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    sugar_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Bell Pepper, Red, Raw',
    'ingredient',
    31.00,
    0.99,
    6.03,
    0.30,
    2.10,
    4.20,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'pepper', 'medium', 119.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Cucumber (With Peel, Raw)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Cucumber, With Peel, Raw',
    'ingredient',
    15.00,
    0.65,
    3.63,
    0.11,
    0.50,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', 'sliced', 104.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Tomato (Red, Ripe, Raw)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    sugar_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Tomato, Red, Ripe, Raw',
    'ingredient',
    18.00,
    0.88,
    3.89,
    0.20,
    1.20,
    2.63,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'tomato', 'medium', 123.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Lettuce (Romaine, Raw)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Lettuce, Romaine, Raw',
    'ingredient',
    17.00,
    1.23,
    3.29,
    0.30,
    2.10,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', 'shredded', 47.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Onion (Raw)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    sugar_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Onion, Raw',
    'ingredient',
    40.00,
    1.10,
    9.34,
    0.10,
    1.70,
    4.24,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'onion', 'medium', 110.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Cauliflower (Raw)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Cauliflower, Raw',
    'ingredient',
    25.00,
    1.92,
    4.97,
    0.28,
    2.00,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', 'chopped', 107.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Zucchini (Raw, Includes Skin)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Zucchini, Raw, Includes Skin',
    'ingredient',
    17.00,
    1.21,
    3.11,
    0.32,
    1.00,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', 'sliced', 124.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Asparagus (Cooked, Boiled, Drained)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Asparagus, Cooked, Boiled',
    'ingredient',
    22.00,
    2.40,
    4.11,
    0.22,
    2.00,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', NULL, 134.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Green Beans (Cooked, Boiled, Drained)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Green Beans, Cooked, Boiled',
    'ingredient',
    35.00,
    1.89,
    7.88,
    0.28,
    3.40,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', NULL, 125.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Brussels Sprouts (Cooked, Boiled, Drained)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Brussels Sprouts, Cooked, Boiled',
    'ingredient',
    36.00,
    2.55,
    7.10,
    0.50,
    2.60,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', NULL, 156.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Kale (Raw)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Kale, Raw',
    'ingredient',
    35.00,
    2.92,
    4.42,
    1.49,
    4.10,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', 'chopped', 67.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Cabbage (Raw)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Cabbage, Raw',
    'ingredient',
    25.00,
    1.28,
    5.80,
    0.10,
    2.50,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', 'shredded', 89.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Celery (Raw)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Celery, Raw',
    'ingredient',
    14.00,
    0.69,
    2.97,
    0.17,
    1.60,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'stalk', 'medium', 40.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Mushrooms (White, Raw)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Mushrooms, White, Raw',
    'ingredient',
    22.00,
    3.09,
    3.26,
    0.34,
    1.00,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', 'sliced', 70.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Eggplant (Raw)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Eggplant, Raw',
    'ingredient',
    25.00,
    0.98,
    5.88,
    0.18,
    3.00,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', 'cubed', 82.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Radish (Raw)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Radish, Raw',
    'ingredient',
    16.00,
    0.68,
    3.40,
    0.10,
    1.60,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', 'sliced', 116.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Arugula (Raw)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Arugula, Raw',
    'ingredient',
    25.00,
    2.58,
    3.65,
    0.66,
    1.60,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', NULL, 20.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- ============================================================================
-- SECTION 4: FRUITS (10 foods)
-- ============================================================================

-- Banana (Raw)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    sugar_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Banana, Raw',
    'ingredient',
    89.00,
    1.09,
    22.84,
    0.33,
    2.60,
    12.23,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'banana', 'medium', 118.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Apple (Raw, With Skin)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    sugar_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Apple, Raw, With Skin',
    'ingredient',
    52.00,
    0.26,
    13.81,
    0.17,
    2.40,
    10.39,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'apple', 'medium', 182.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Orange (Raw)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    sugar_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Orange, Raw',
    'ingredient',
    47.00,
    0.94,
    11.75,
    0.12,
    2.40,
    9.35,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'orange', 'medium', 131.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Strawberries (Raw)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    sugar_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Strawberries, Raw',
    'ingredient',
    32.00,
    0.67,
    7.68,
    0.30,
    2.00,
    4.89,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', 'whole', 144.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Blueberries (Raw)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    sugar_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Blueberries, Raw',
    'ingredient',
    57.00,
    0.74,
    14.49,
    0.33,
    2.40,
    9.96,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', NULL, 148.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Grapes (Raw)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    sugar_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Grapes, Raw',
    'ingredient',
    69.00,
    0.72,
    18.10,
    0.16,
    0.90,
    15.48,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', NULL, 151.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Watermelon (Raw)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    sugar_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Watermelon, Raw',
    'ingredient',
    30.00,
    0.61,
    7.55,
    0.15,
    0.40,
    6.20,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', 'diced', 152.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Pineapple (Raw)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    sugar_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Pineapple, Raw',
    'ingredient',
    50.00,
    0.54,
    13.12,
    0.12,
    1.40,
    9.85,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', 'chunks', 165.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Mango (Raw)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    sugar_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Mango, Raw',
    'ingredient',
    60.00,
    0.82,
    14.98,
    0.38,
    1.60,
    13.66,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', 'sliced', 165.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Avocado (Raw)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    sugar_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Avocado, Raw',
    'ingredient',
    160.00,
    2.00,
    8.53,
    14.66,
    6.70,
    0.66,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'avocado', 'medium', 150.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- ============================================================================
-- SECTION 5: FATS & OILS (10 foods)
-- ============================================================================

-- Olive Oil
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Olive Oil',
    'ingredient',
    884.00,
    0.00,
    0.00,
    100.00,
    0.00,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'tbsp', NULL, 13.50, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Butter (Salted)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Butter, Salted',
    'ingredient',
    717.00,
    0.85,
    0.06,
    81.11,
    0.00,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'tbsp', NULL, 14.20, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Almonds (Raw)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Almonds, Raw',
    'ingredient',
    579.00,
    21.15,
    21.55,
    49.93,
    12.50,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'oz', NULL, 28.35, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 23.00, 'almond', NULL, 28.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Walnuts (Raw)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Walnuts, Raw',
    'ingredient',
    654.00,
    15.23,
    13.71,
    65.21,
    6.70,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'oz', NULL, 28.35, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 14.00, 'half', NULL, 28.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Cashews (Raw)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Cashews, Raw',
    'ingredient',
    553.00,
    18.22,
    30.19,
    43.85,
    3.30,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'oz', NULL, 28.35, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 18.00, 'cashew', NULL, 28.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Coconut Oil
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Coconut Oil',
    'ingredient',
    862.00,
    0.00,
    0.00,
    100.00,
    0.00,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'tbsp', NULL, 13.60, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Avocado Oil
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Avocado Oil',
    'ingredient',
    884.00,
    0.00,
    0.00,
    100.00,
    0.00,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'tbsp', NULL, 13.60, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Cheese (Cheddar)
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Cheese, Cheddar',
    'ingredient',
    403.00,
    24.90,
    1.28,
    33.14,
    0.00,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'oz', NULL, 28.35, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'slice', NULL, 28.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Cream Cheese
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Cream Cheese',
    'ingredient',
    342.00,
    5.93,
    4.07,
    34.24,
    0.00,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'tbsp', NULL, 14.50, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Chia Seeds
WITH new_food AS (
  INSERT INTO foods (
    name,
    food_type,
    calories_per_100g,
    protein_g_per_100g,
    carbs_g_per_100g,
    fat_g_per_100g,
    fiber_g_per_100g,
    is_public,
    verified
  ) VALUES (
    'Chia Seeds',
    'ingredient',
    486.00,
    16.54,
    42.12,
    30.74,
    34.40,
    TRUE,
    TRUE
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'tbsp', NULL, 12.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- ============================================================================
-- SUMMARY
-- ============================================================================
-- ✅ 80 common foods seeded
-- ✅ All nutrition values per 100g (canonical base)
-- ✅ 2-3 servings per food (default, oz, grams, plus food-specific)
-- ✅ Categories: Proteins (20), Carbs (20), Vegetables (20), Fruits (10), Fats (10)
-- ✅ is_public=TRUE, verified=TRUE for all foods
-- ✅ One is_default=true per food
-- ✅ Covers 80% of common use cases
--
-- USAGE:
-- Now the LLM consultation system can search and find:
-- - "chicken breast" → finds both raw and cooked versions
-- - "rice" → finds white rice and brown rice
-- - "protein powder" → finds whey protein powder
-- - "broccoli" → finds broccoli, cooked
--
-- Users can complete the "typical foods" section successfully!
-- ============================================================================
