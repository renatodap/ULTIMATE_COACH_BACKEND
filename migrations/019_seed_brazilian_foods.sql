-- ============================================================================
-- Brazilian Foods Seeding Migration
-- ============================================================================
-- Version: 1.0.0
-- Created: 2025-10-13
-- Description: Traditional Brazilian foods, ingredients, and dishes
--
-- COVERS:
-- - Proteins: Picanha, Linguiça, Carne Seca
-- - Carbs: Pão de Queijo, Farofa, Tapioca, Polvilho
-- - Beans: Black Beans (Feijão Preto), Feijoada
-- - Dishes: Moqueca, Coxinha, Brigadeiro, Pastel
-- - Fruits: Açaí, Cupuaçu, Cashew Apple
-- - Beverages: Guaraná
-- ============================================================================

-- ============================================================================
-- BRAZILIAN PROTEINS
-- ============================================================================

-- Picanha (Top Sirloin Cap)
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Picanha, Grilled',
    'ingredient',
    280.00, 24.00, 0.00, 20.00,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'steak', '200g steak', 200.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'oz', NULL, 28.35, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Linguiça (Brazilian Sausage)
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Linguiça, Brazilian Sausage, Grilled',
    'ingredient',
    301.00, 17.00, 2.50, 24.00,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'link', 'link', 80.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Carne Seca (Dried Beef)
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Carne Seca, Brazilian Dried Beef',
    'ingredient',
    212.00, 34.00, 0.00, 8.00,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'serving', '100g serving', 100.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- ============================================================================
-- BRAZILIAN CARBS & STAPLES
-- ============================================================================

-- Pão de Queijo (Cheese Bread)
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Pão de Queijo, Cheese Bread',
    'ingredient',
    320.00, 8.50, 42.00, 12.00,
    1.20, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'piece', 'small piece', 25.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'large', 'large piece', 50.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Farofa (Toasted Cassava Flour)
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Farofa, Toasted Cassava Flour',
    'ingredient',
    360.00, 1.50, 82.00, 1.00,
    3.50, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 2.00, 'tbsp', '2 tbsp', 20.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 0.25, 'cup', '1/4 cup', 30.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Tapioca Crepe (Plain)
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Tapioca Crepe, Plain',
    'ingredient',
    130.00, 0.20, 32.00, 0.10,
    0.50, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'crepe', 'crepe', 50.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Polvilho Azedo (Sour Tapioca Starch)
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Polvilho Azedo, Sour Tapioca Starch',
    'ingredient',
    352.00, 0.30, 88.00, 0.10,
    0.20, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 0.25, 'cup', '1/4 cup', 32.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- ============================================================================
-- BRAZILIAN BEANS & LEGUMES
-- ============================================================================

-- Feijão Preto (Black Beans, Brazilian Style)
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Feijão Preto, Brazilian Black Beans, Cooked',
    'ingredient',
    77.00, 4.50, 14.00, 0.30,
    4.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', '1 cup', 200.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 0.50, 'cup', '1/2 cup', 100.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- ============================================================================
-- BRAZILIAN DISHES
-- ============================================================================

-- Feijoada (Brazilian Black Bean Stew)
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Feijoada, Brazilian Black Bean Stew',
    'dish',
    150.00, 8.50, 12.00, 7.50,
    3.50, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', '1 cup', 250.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'bowl', 'bowl', 350.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Moqueca (Brazilian Fish Stew)
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Moqueca, Brazilian Fish Stew',
    'dish',
    95.00, 10.00, 4.50, 4.00,
    1.20, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', '1 cup', 240.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'bowl', 'bowl', 350.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Coxinha (Chicken Croquette)
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Coxinha, Brazilian Chicken Croquette',
    'dish',
    245.00, 8.00, 28.00, 10.00,
    1.50, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'piece', 'medium piece', 80.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'large', 'large piece', 120.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Brigadeiro (Chocolate Truffle)
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Brigadeiro, Brazilian Chocolate Truffle',
    'dish',
    395.00, 4.00, 65.00, 13.00,
    2.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'piece', 'piece', 20.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 3.00, 'pieces', '3 pieces', 60.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Pastel (Brazilian Fried Pastry)
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Pastel, Brazilian Fried Pastry with Cheese',
    'dish',
    280.00, 7.00, 32.00, 13.00,
    1.80, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'piece', 'medium piece', 90.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Pudim (Brazilian Flan)
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Pudim, Brazilian Flan',
    'dish',
    195.00, 4.50, 35.00, 4.00,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'slice', 'slice', 100.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- ============================================================================
-- BRAZILIAN FRUITS
-- ============================================================================

-- Açaí (Frozen Pulp, Unsweetened)
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Açaí, Frozen Pulp, Unsweetened',
    'ingredient',
    70.00, 1.00, 4.00, 5.00,
    2.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', '1 cup', 240.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'packet', '100g packet', 100.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Açaí Bowl (with Granola and Fruit)
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Açaí Bowl, with Granola and Fruit',
    'dish',
    140.00, 3.00, 22.00, 5.00,
    3.50, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'bowl', 'bowl', 300.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- Cupuaçu (Frozen Pulp)
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Cupuaçu, Frozen Pulp',
    'ingredient',
    49.00, 1.10, 11.80, 0.50,
    1.70, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 100.00, 'g', '100g packet', 100.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'cup', '1 cup', 240.00, FALSE, 2 FROM new_food;

-- Caju (Cashew Apple), Fresh
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Caju, Cashew Apple, Fresh',
    'ingredient',
    43.00, 0.80, 10.30, 0.20,
    0.90, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'fruit', 'medium fruit', 120.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 2 FROM new_food;

-- ============================================================================
-- BRAZILIAN BEVERAGES
-- ============================================================================

-- Guaraná (Soda)
WITH new_food AS (
  INSERT INTO foods (
    name, brand_name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Guaraná Antarctica',
    'Antarctica',
    'branded',
    42.00, 0.00, 10.50, 0.00,
    0.00, TRUE, TRUE, 'branded'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'can', '12 oz can', 355.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'bottle', '2L bottle', 2000.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'ml', NULL, 100.00, FALSE, 3 FROM new_food;

-- Mate (Yerba Mate Tea, Unsweetened)
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Mate, Yerba Mate Tea, Unsweetened',
    'ingredient',
    1.00, 0.00, 0.00, 0.00,
    0.00, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 1.00, 'cup', '1 cup (8 oz)', 237.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 100.00, 'ml', NULL, 100.00, FALSE, 2 FROM new_food;

-- ============================================================================
-- BRAZILIAN VEGETABLES
-- ============================================================================

-- Couve (Collard Greens, Brazilian Style)
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Couve, Brazilian Collard Greens, Sautéed',
    'ingredient',
    55.00, 2.00, 4.50, 3.50,
    2.50, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 0.50, 'cup', '1/2 cup', 75.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'cup', '1 cup', 150.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- Mandioca (Cassava/Yuca, Boiled)
WITH new_food AS (
  INSERT INTO foods (
    name, food_type,
    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
    fiber_g_per_100g, is_public, verified, composition_type
  ) VALUES (
    'Mandioca, Cassava, Boiled',
    'ingredient',
    112.00, 0.80, 26.90, 0.20,
    1.20, TRUE, TRUE, 'simple'
  ) RETURNING id
)
INSERT INTO food_servings (food_id, serving_size, serving_unit, serving_label, grams_per_serving, is_default, display_order)
SELECT id, 0.50, 'cup', '1/2 cup', 103.00, TRUE, 1 FROM new_food
UNION ALL
SELECT id, 1.00, 'cup', '1 cup', 206.00, FALSE, 2 FROM new_food
UNION ALL
SELECT id, 100.00, 'g', NULL, 100.00, FALSE, 3 FROM new_food;

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
