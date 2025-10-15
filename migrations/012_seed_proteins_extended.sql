-- ============================================================================
-- Extended Proteins Seeding Migration
-- ============================================================================
-- Version: 1.0.0
-- Created: 2025-10-13
-- Description: Extended protein sources - beef cuts, pork, poultry, fish, seafood
--
-- COVERS:
-- - Beef steaks and cuts (ribeye, NY strip, filet, flank, brisket)
-- - Pork varieties (chops, tenderloin, ribs, bacon, sausage)
-- - Poultry parts (chicken thighs/wings/drumsticks, ground chicken/turkey, turkey sausage)
-- - Fish (cod, halibut, trout, mahi mahi, catfish)
-- - Seafood (scallops, crab, lobster, sardines)
-- - Plant proteins (lentils, edamame, tempeh, seitan, plant-based burgers)
-- - Deli meats (ham, roast beef, pastrami, salami, pepperoni)
--
-- NOTE: Skips duplicates from 007 (chicken breast, ground beef 93%/80%,
--       salmon, tuna, tofu, turkey breast deli, pork loin, shrimp,
--       sirloin, tilapia)
-- ============================================================================

-- ============================================================================
-- BEEF STEAKS & CUTS
-- ============================================================================

-- Ribeye Steak, Cooked
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Ribeye Steak, Cooked, Grilled',
    'ingredient',
    291.00, 25.10, 0.00, 21.10,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'steak', '8 oz steak', 227.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- NY Strip Steak, Cooked
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'NY Strip Steak, Cooked, Grilled',
    'ingredient',
    210.00, 28.50, 0.00, 10.40,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'steak', '8 oz steak', 227.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Filet Mignon, Cooked
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Filet Mignon, Cooked, Grilled',
    'ingredient',
    247.00, 26.30, 0.00, 15.70,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'steak', '6 oz steak', 170.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Flank Steak, Cooked
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Flank Steak, Cooked, Grilled',
    'ingredient',
    222.00, 29.20, 0.00, 11.30,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'serving', '4 oz serving', 113.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Beef Brisket, Cooked
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Beef Brisket, Smoked, Trimmed',
    'ingredient',
    288.00, 24.50, 0.00, 20.80,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'slice', 'thick slice', 85.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- ============================================================================
-- PORK
-- ============================================================================

-- Pork Chop, Cooked
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Pork Chop, Boneless, Cooked',
    'ingredient',
    201.00, 28.80, 0.00, 9.20,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'chop', 'medium chop', 150.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Pork Tenderloin, Cooked
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Pork Tenderloin, Roasted',
    'ingredient',
    143.00, 26.20, 0.00, 3.50,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'serving', '4 oz serving', 113.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Bacon, Cooked
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Bacon, Cooked, Crispy',
    'ingredient',
    541.00, 37.00, 1.40, 41.80,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'slice', 'slice', 8.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 2.00, 'slices', '2 slices', 16.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Pork Sausage, Cooked
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Pork Sausage, Breakfast Links, Cooked',
    'ingredient',
    339.00, 15.10, 2.20, 30.30,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'link', 'link', 28.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 2.00, 'links', '2 links', 56.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Ground Pork, Cooked
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Ground Pork, Cooked',
    'ingredient',
    297.00, 25.70, 0.00, 21.20,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'serving', '4 oz serving', 113.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- ============================================================================
-- POULTRY (Extended cuts)
-- ============================================================================

-- Chicken Thighs, Boneless Skinless, Cooked
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Chicken Thighs, Boneless Skinless, Cooked',
    'ingredient',
    209.00, 26.00, 0.00, 10.90,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'thigh', 'medium thigh', 75.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Chicken Wings, Cooked
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Chicken Wings, Roasted',
    'ingredient',
    290.00, 27.00, 0.00, 19.50,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'wing', 'wing', 34.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 3.00, 'wings', '3 wings', 102.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Chicken Drumsticks, Cooked
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Chicken Drumsticks, Roasted',
    'ingredient',
    216.00, 27.40, 0.00, 11.20,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'drumstick', 'drumstick', 75.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Ground Chicken, Cooked
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Ground Chicken, Cooked',
    'ingredient',
    189.00, 27.80, 0.00, 8.10,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'serving', '4 oz serving', 113.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Ground Turkey 93/7, Cooked
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Ground Turkey, 93% Lean, Cooked',
    'ingredient',
    176.00, 29.40, 0.00, 6.20,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'serving', '4 oz serving', 113.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Turkey Sausage, Cooked
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Turkey Sausage, Breakfast Links, Cooked',
    'ingredient',
    236.00, 18.50, 2.70, 16.70,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'link', 'link', 28.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 2.00, 'links', '2 links', 56.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- ============================================================================
-- FISH (Beyond salmon, tuna, tilapia, sirloin)
-- ============================================================================

-- Cod, Cooked
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Cod, Atlantic, Baked',
    'ingredient',
    105.00, 22.80, 0.00, 0.90,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'fillet', 'fillet', 140.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Halibut, Cooked
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Halibut, Pacific, Baked',
    'ingredient',
    140.00, 26.70, 0.00, 2.90,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'fillet', 'fillet', 150.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Trout, Cooked
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Trout, Rainbow, Baked',
    'ingredient',
    190.00, 26.60, 0.00, 8.50,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'fillet', 'fillet', 125.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Mahi Mahi, Cooked
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Mahi Mahi, Grilled',
    'ingredient',
    109.00, 23.70, 0.00, 0.90,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'fillet', 'fillet', 135.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Sardines, Canned
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Sardines, Canned in Oil, Drained',
    'ingredient',
    208.00, 24.60, 0.00, 11.50,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'can', 'small can', 92.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- ============================================================================
-- SEAFOOD
-- ============================================================================

-- Scallops, Cooked
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Scallops, Sea, Cooked',
    'ingredient',
    111.00, 20.50, 5.40, 0.80,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 3.00, 'scallops', '3 large scallops', 100.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Crab, Cooked
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Crab, Blue, Steamed',
    'ingredient',
    97.00, 20.50, 0.00, 1.10,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'serving', '4 oz serving', 113.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Lobster, Cooked
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Lobster, Steamed',
    'ingredient',
    98.00, 20.50, 1.30, 0.60,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'tail', 'tail', 180.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- ============================================================================
-- PLANT PROTEINS (Beyond chickpeas, black beans, tofu)
-- ============================================================================

-- Edamame, Cooked
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Edamame, Boiled',
    'ingredient',
    122.00, 11.90, 8.90, 5.20,
    5.20, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 0.50, 'cup', '1/2 cup', 100.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Tempeh
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Tempeh, Soy',
    'ingredient',
    192.00, 20.30, 7.60, 10.80,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 0.50, 'cup', '1/2 cup', 85.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Seitan
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Seitan, Wheat Gluten',
    'ingredient',
    370.00, 75.20, 14.00, 1.90,
    0.60, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'serving', '3 oz serving', 85.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Beyond Burger
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Beyond Burger Patty',
    'Beyond Meat',
    'branded',
    221.00, 17.70, 2.70, 15.90,
    1.80, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'patty', 'patty', 113.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Impossible Burger
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Impossible Burger Patty',
    'Impossible Foods',
    'branded',
    212.00, 16.80, 8.00, 12.40,
    2.70, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'patty', 'patty', 113.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- ============================================================================
-- DELI MEATS
-- ============================================================================

-- Ham, Deli
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Ham, Deli, Sliced',
    'ingredient',
    107.00, 18.80, 2.70, 2.70,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'slice', 'slice', 28.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 2.00, 'slices', '2 slices', 56.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Roast Beef, Deli
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Roast Beef, Deli, Sliced',
    'ingredient',
    120.00, 20.00, 3.20, 2.90,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'slice', 'slice', 28.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 2.00, 'slices', '2 slices', 56.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Pastrami, Deli
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Pastrami, Deli, Sliced',
    'ingredient',
    143.00, 18.80, 1.80, 6.30,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'slice', 'slice', 28.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 2.00, 'slices', '2 slices', 56.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Salami, Deli
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Salami, Genoa, Deli',
    'ingredient',
    375.00, 20.70, 2.10, 30.60,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'slice', 'slice', 9.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 3.00, 'slices', '3 slices', 27.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Pepperoni
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Pepperoni, Sliced',
    'ingredient',
    504.00, 20.70, 4.30, 46.40,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 15.00, 'slices', '15 slices', 28.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
