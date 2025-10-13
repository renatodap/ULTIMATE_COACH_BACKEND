-- ============================================================================
-- Desserts Extended Seeding Migration
-- ============================================================================
-- Version: 1.0.0
-- Created: 2025-10-13
-- Description: Comprehensive desserts - ice cream, cakes, pies, brownies, puddings
--
-- COVERS: Ice cream, cakes, pies, brownies, pudding, donuts, cupcakes, cheesecake
-- All nutrition converted to per-100g for consistency
-- ============================================================================

-- ============================================================================
-- ICE CREAM
-- ============================================================================

-- Vanilla Ice Cream (Regular)
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, sugar_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Ice Cream, Vanilla, Regular',
    'ingredient',
    207.00, 3.50, 23.60, 11.00,
    0.70, 21.20, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 0.50, 'cup', '1/2 cup', 66.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'scoop', '1 scoop', 72.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Chocolate Ice Cream
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, sugar_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Ice Cream, Chocolate',
    'ingredient',
    216.00, 3.80, 28.20, 11.00,
    1.60, 25.40, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 0.50, 'cup', '1/2 cup', 66.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'scoop', '1 scoop', 72.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Strawberry Ice Cream
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, sugar_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Ice Cream, Strawberry',
    'ingredient',
    192.00, 3.20, 27.60, 8.40,
    0.90, 24.40, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 0.50, 'cup', '1/2 cup', 66.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'scoop', '1 scoop', 72.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Ben & Jerry's Half Baked
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Ben & Jerry''s Half Baked',
    'Ben & Jerry''s',
    'branded',
    270.00, 4.50, 33.00, 13.00,
    1.50, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 0.50, 'cup', '1/2 cup', 100.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Häagen-Dazs Vanilla
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Häagen-Dazs Vanilla Ice Cream',
    'Häagen-Dazs',
    'branded',
    270.00, 5.00, 23.00, 18.00,
    0.00, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 0.50, 'cup', '1/2 cup', 106.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Ice Cream Sandwich
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Ice Cream Sandwich, Vanilla',
    'ingredient',
    237.00, 3.70, 37.00, 8.60,
    0.90, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'sandwich', '1 sandwich', 81.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- ============================================================================
-- CAKES
-- ============================================================================

-- Chocolate Cake with Frosting
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, sugar_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Chocolate Cake with Chocolate Frosting',
    'ingredient',
    370.00, 4.00, 52.00, 17.00,
    2.00, 40.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'slice', 'slice (1/12 of 9" cake)', 95.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Vanilla Cake with Frosting
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, sugar_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Vanilla Cake with Vanilla Frosting',
    'ingredient',
    390.00, 3.50, 57.00, 16.00,
    0.50, 45.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'slice', 'slice (1/12 of 9" cake)', 92.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Carrot Cake with Cream Cheese Frosting
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, sugar_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Carrot Cake with Cream Cheese Frosting',
    'ingredient',
    350.00, 4.00, 48.00, 16.00,
    1.50, 35.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'slice', 'slice (1/12 of cake)', 100.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Red Velvet Cake
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, sugar_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Red Velvet Cake with Cream Cheese Frosting',
    'ingredient',
    360.00, 3.80, 50.00, 16.50,
    0.80, 38.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'slice', 'slice (1/12 of cake)', 95.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Cheesecake (Plain)
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, sugar_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Cheesecake, Plain',
    'ingredient',
    321.00, 5.50, 25.50, 22.50,
    0.80, 19.40, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'slice', 'slice (1/12 of 9" cake)', 125.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- ============================================================================
-- PIES
-- ============================================================================

-- Apple Pie
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, sugar_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Apple Pie, Homemade',
    'ingredient',
    237.00, 2.00, 34.00, 11.00,
    1.60, 16.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'slice', 'slice (1/8 of 9" pie)', 125.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Pumpkin Pie
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, sugar_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Pumpkin Pie, Homemade',
    'ingredient',
    243.00, 4.50, 32.00, 11.00,
    2.90, 20.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'slice', 'slice (1/8 of 9" pie)', 155.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Pecan Pie
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, sugar_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Pecan Pie, Homemade',
    'ingredient',
    466.00, 5.00, 64.00, 21.00,
    2.00, 42.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'slice', 'slice (1/8 of 9" pie)', 122.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Key Lime Pie
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, sugar_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Key Lime Pie',
    'ingredient',
    318.00, 4.50, 36.00, 18.00,
    0.50, 28.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'slice', 'slice (1/8 of 9" pie)', 125.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- ============================================================================
-- BROWNIES & BARS
-- ============================================================================

-- Brownies (Homemade)
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, sugar_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Brownie, Chocolate, Homemade',
    'ingredient',
    466.00, 5.00, 63.00, 22.00,
    2.50, 48.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'brownie', 'medium brownie (2"x2")', 56.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'large', 'large brownie (3"x3")', 90.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Lemon Bars
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, sugar_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Lemon Bar',
    'ingredient',
    360.00, 4.00, 54.00, 14.00,
    0.50, 40.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'bar', 'medium bar (2"x2")', 50.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Rice Krispies Treats
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Rice Krispies Treats',
    'Rice Krispies',
    'branded',
    404.00, 4.00, 76.00, 8.00,
    0.00, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'bar', '1 bar', 22.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- ============================================================================
-- PUDDING & CUSTARDS
-- ============================================================================

-- Chocolate Pudding
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, sugar_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Chocolate Pudding, Ready-to-Eat',
    'ingredient',
    120.00, 2.80, 20.60, 3.50,
    0.80, 15.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', '1 snack cup', 113.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 0.50, 'cup', '1/2 cup', 56.50, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Vanilla Pudding
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, sugar_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Vanilla Pudding, Ready-to-Eat',
    'ingredient',
    110.00, 2.40, 19.80, 2.90,
    0.00, 15.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', '1 snack cup', 113.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 0.50, 'cup', '1/2 cup', 56.50, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Flan (Custard)
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, sugar_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Flan, Caramel Custard',
    'ingredient',
    151.00, 5.00, 22.00, 5.00,
    0.00, 21.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'serving', '1 serving (1/6 of recipe)', 120.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- ============================================================================
-- OTHER DESSERTS
-- ============================================================================

-- Tiramisu
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, sugar_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Tiramisu',
    'ingredient',
    240.00, 4.50, 26.00, 13.00,
    0.50, 18.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'serving', '1 serving', 110.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Glazed Donut
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, sugar_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Donut, Glazed',
    'ingredient',
    452.00, 5.00, 51.00, 25.00,
    1.20, 23.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'donut', 'medium donut', 52.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Chocolate Frosted Donut
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, sugar_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Donut, Chocolate Frosted',
    'ingredient',
    421.00, 4.70, 50.00, 23.00,
    1.60, 24.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'donut', 'medium donut', 64.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Vanilla Cupcake with Frosting
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, sugar_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Cupcake, Vanilla with Frosting',
    'ingredient',
    400.00, 3.50, 58.00, 17.00,
    0.50, 43.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cupcake', 'medium cupcake', 75.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Chocolate Cupcake with Frosting
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, sugar_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Cupcake, Chocolate with Frosting',
    'ingredient',
    380.00, 4.00, 52.00, 17.00,
    2.00, 40.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cupcake', 'medium cupcake', 75.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Blueberry Muffin
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, sugar_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Blueberry Muffin, Bakery Style',
    'ingredient',
    355.00, 5.50, 51.00, 14.50,
    1.80, 28.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'muffin', 'medium muffin', 113.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'large', 'large muffin', 150.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Chocolate Chip Muffin
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, sugar_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Chocolate Chip Muffin, Bakery Style',
    'ingredient',
    389.00, 5.30, 52.00, 17.70,
    1.80, 32.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'muffin', 'medium muffin', 113.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'large', 'large muffin', 150.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
