-- ============================================================================
-- Snacks & Treats Seeding Migration
-- ============================================================================
-- Version: 1.0.0
-- Created: 2025-10-13
-- Description: Popular snacks, chips, cookies, crackers, candy, popcorn, pretzels
--
-- COVERS: Chips, cookies, crackers, candy bars, chocolate, popcorn, pretzels, trail mix
-- All nutrition converted to per-100g for consistency
-- ============================================================================

-- ============================================================================
-- POTATO & CORN CHIPS
-- ============================================================================

-- Lay's Classic Potato Chips
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Lay''s Classic Potato Chips',
    'Lay''s',
    'branded',
    536.00, 7.14, 53.57, 35.71,
    3.60, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'oz', '1 oz (about 15 chips)', 28.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'bag', 'small bag', 42.50, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Doritos Nacho Cheese
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Doritos, Nacho Cheese',
    'Doritos',
    'branded',
    500.00, 7.14, 64.29, 25.00,
    3.60, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'oz', '1 oz (about 12 chips)', 28.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Doritos Cool Ranch
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Doritos, Cool Ranch',
    'Doritos',
    'branded',
    500.00, 7.14, 64.29, 25.00,
    3.60, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'oz', '1 oz (about 12 chips)', 28.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Pringles Original
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Pringles, Original',
    'Pringles',
    'branded',
    536.00, 3.57, 53.57, 35.71,
    3.60, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'oz', '1 oz (about 15 chips)', 28.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Kettle Brand Sea Salt Chips
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Kettle Brand, Sea Salt Chips',
    'Kettle Brand',
    'branded',
    536.00, 7.14, 50.00, 35.71,
    7.10, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'oz', '1 oz (about 13 chips)', 28.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Tostitos Tortilla Chips
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Tostitos, Original Tortilla Chips',
    'Tostitos',
    'branded',
    500.00, 7.14, 64.29, 25.00,
    3.60, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'oz', '1 oz (about 6 chips)', 28.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Cheetos Crunchy
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Cheetos, Crunchy',
    'Cheetos',
    'branded',
    571.00, 7.14, 53.57, 35.71,
    3.60, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'oz', '1 oz (about 21 pieces)', 28.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- ============================================================================
-- COOKIES
-- ============================================================================

-- Oreo Cookies
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Oreo Cookies, Original',
    'Oreo',
    'branded',
    480.00, 4.80, 68.00, 20.00,
    3.20, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 3.00, 'cookies', '3 cookies', 34.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'cookie', '1 cookie', 11.30, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Chips Ahoy! Original
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Chips Ahoy!, Original',
    'Chips Ahoy!',
    'branded',
    500.00, 5.00, 66.67, 23.33,
    1.70, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 3.00, 'cookies', '3 cookies', 30.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'cookie', '1 cookie', 10.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Chocolate Chip Cookies (Homemade)
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Chocolate Chip Cookie, Homemade',
    'ingredient',
    488.00, 5.60, 66.00, 22.00,
    2.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cookie', 'medium cookie', 30.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'large', 'large cookie', 50.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Peanut Butter Cookies
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Peanut Butter Cookie, Homemade',
    'ingredient',
    480.00, 9.00, 53.00, 26.00,
    2.50, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cookie', 'medium cookie', 25.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Oatmeal Raisin Cookies
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Oatmeal Raisin Cookie, Homemade',
    'ingredient',
    430.00, 6.00, 66.00, 16.00,
    3.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cookie', 'medium cookie', 30.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- ============================================================================
-- CRACKERS
-- ============================================================================

-- Ritz Crackers
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Ritz Crackers, Original',
    'Ritz',
    'branded',
    500.00, 6.67, 66.67, 23.33,
    3.30, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 5.00, 'crackers', '5 crackers', 16.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Wheat Thins Original
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Wheat Thins, Original',
    'Wheat Thins',
    'branded',
    464.00, 7.14, 67.86, 17.86,
    7.10, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 16.00, 'crackers', '16 crackers', 28.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Triscuit Original
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Triscuit, Original',
    'Triscuit',
    'branded',
    429.00, 10.70, 67.90, 14.30,
    14.30, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 6.00, 'crackers', '6 crackers', 28.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Goldfish Crackers
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Goldfish Crackers, Cheddar',
    'Goldfish',
    'branded',
    500.00, 10.00, 63.33, 20.00,
    3.30, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 55.00, 'pieces', '55 pieces', 30.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Club Crackers
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Club Crackers, Original',
    'Club',
    'branded',
    500.00, 6.67, 66.67, 23.33,
    3.30, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 4.00, 'crackers', '4 crackers', 14.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- ============================================================================
-- CANDY & CHOCOLATE BARS
-- ============================================================================

-- Snickers Bar
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Snickers Bar',
    'Snickers',
    'branded',
    488.00, 8.14, 60.47, 23.26,
    2.30, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'bar', 'regular bar', 52.70, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'fun size', 'fun size', 17.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Kit Kat
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Kit Kat Bar',
    'Kit Kat',
    'branded',
    518.00, 6.98, 65.12, 25.58,
    2.30, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'bar', '4-finger bar', 41.50, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- M&M's Plain
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'M&M''s, Milk Chocolate',
    'M&M''s',
    'branded',
    492.00, 4.92, 68.85, 21.31,
    3.30, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'pack', 'single serve pack', 47.90, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Reese's Peanut Butter Cups
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Reese''s Peanut Butter Cups',
    'Reese''s',
    'branded',
    515.00, 10.29, 55.88, 29.41,
    4.40, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 2.00, 'cups', '2 cups (1 pack)', 42.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'cup', '1 cup', 21.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Twix Bar
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Twix Bar',
    'Twix',
    'branded',
    502.00, 4.67, 64.49, 24.30,
    1.90, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 2.00, 'bars', '2 bars (1 pack)', 50.70, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'bar', '1 bar', 25.40, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Hershey's Milk Chocolate Bar
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Hershey''s Milk Chocolate Bar',
    'Hershey''s',
    'branded',
    535.00, 7.14, 57.14, 32.14,
    3.60, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'bar', 'standard bar', 43.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- ============================================================================
-- POPCORN
-- ============================================================================

-- Microwave Popcorn, Butter
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Microwave Popcorn, Butter Flavor',
    'ingredient',
    533.00, 10.00, 50.00, 33.30,
    16.70, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', '1 cup popped', 8.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 3.00, 'cups', '3 cups popped', 24.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Air-Popped Popcorn (Plain)
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Popcorn, Air-Popped, Plain',
    'ingredient',
    387.00, 12.90, 77.40, 4.50,
    15.10, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', '1 cup popped', 8.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 3.00, 'cups', '3 cups popped', 24.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Kettle Corn
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Kettle Corn, Sweet & Salty',
    'ingredient',
    467.00, 6.70, 73.30, 16.70,
    6.70, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', '1 cup', 30.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', '1 oz', 28.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Caramel Corn
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Caramel Popcorn',
    'ingredient',
    467.00, 6.70, 73.30, 16.70,
    3.30, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', '1 cup', 35.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', '1 oz', 28.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- ============================================================================
-- PRETZELS
-- ============================================================================

-- Rold Gold Pretzels (Hard Twists)
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Rold Gold Pretzels, Twists',
    'Rold Gold',
    'branded',
    393.00, 10.70, 82.10, 3.60,
    3.60, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'oz', '1 oz (about 10 twists)', 28.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Soft Pretzel (Stadium Style)
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Soft Pretzel, Plain',
    'ingredient',
    269.00, 7.00, 52.00, 3.50,
    2.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'pretzel', 'medium pretzel', 115.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'large', 'large pretzel', 170.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Pretzel Sticks
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Pretzel Sticks, Hard',
    'ingredient',
    393.00, 10.70, 82.10, 3.60,
    3.60, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'oz', '1 oz (about 47 sticks)', 28.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- ============================================================================
-- OTHER SNACKS
-- ============================================================================

-- Rice Cakes, Plain
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Rice Cakes, Plain',
    'ingredient',
    387.00, 8.10, 81.50, 2.80,
    4.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cake', '1 cake', 9.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Trail Mix (Nuts, Seeds, Dried Fruit)
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Trail Mix, Traditional (Nuts, Seeds, Dried Fruit)',
    'ingredient',
    462.00, 13.80, 46.20, 30.00,
    6.20, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 0.25, 'cup', '1/4 cup', 38.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', '1 oz', 28.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Fruit Snacks (Gummies)
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Fruit Snacks, Gummies',
    'ingredient',
    333.00, 0.00, 83.30, 0.00,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'pouch', '1 pouch', 25.50, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
