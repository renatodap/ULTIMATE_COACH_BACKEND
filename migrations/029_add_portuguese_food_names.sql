-- Migration: Add Portuguese language support for food names
-- This adds Portuguese columns to the foods table and populates them with translations

-- Add Portuguese name columns
ALTER TABLE foods
  ADD COLUMN IF NOT EXISTS name_pt TEXT,
  ADD COLUMN IF NOT EXISTS brand_name_pt TEXT;

-- Create GIN index for Portuguese full-text search
CREATE INDEX IF NOT EXISTS idx_foods_name_pt_gin
  ON foods USING gin(to_tsvector('portuguese', COALESCE(name_pt, '')));

-- Comment the columns
COMMENT ON COLUMN foods.name_pt IS 'Portuguese translation of food name';
COMMENT ON COLUMN foods.brand_name_pt IS 'Portuguese translation of brand name';

-- ============================================================================
-- POPULATE PORTUGUESE TRANSLATIONS FOR EXISTING FOODS
-- ============================================================================
-- Note: Translations generated using AI, verified for Brazilian Portuguese
-- ============================================================================

-- Brazilian Foods (from migration 019) - Already have Portuguese in name field
UPDATE foods SET name_pt = 'Pão de Queijo' WHERE name = 'Pão de Queijo, Cheese Bread';
UPDATE foods SET name_pt = 'Feijoada' WHERE name = 'Feijoada, Brazilian Black Bean Stew';
UPDATE foods SET name_pt = 'Farofa' WHERE name = 'Farofa, Toasted Cassava Flour';
UPDATE foods SET name_pt = 'Açaí na Tigela' WHERE name = 'Açaí Bowl';
UPDATE foods SET name_pt = 'Coxinha' WHERE name = 'Coxinha, Chicken Croquette';
UPDATE foods SET name_pt = 'Brigadeiro' WHERE name = 'Brigadeiro, Chocolate Truffle';
UPDATE foods SET name_pt = 'Moqueca' WHERE name = 'Moqueca, Brazilian Fish Stew';
UPDATE foods SET name_pt = 'Tapioca' WHERE name = 'Tapioca, Cassava Crepe';
UPDATE foods SET name_pt = 'Pastel' WHERE name = 'Pastel, Fried Pastry';
UPDATE foods SET name_pt = 'Acarajé' WHERE name = 'Acarajé, Black-Eyed Pea Fritter';
UPDATE foods SET name_pt = 'Picanha' WHERE name = 'Picanha, Top Sirloin Cap';
UPDATE foods SET name_pt = 'Caipirinha' WHERE name = 'Caipirinha';
UPDATE foods SET name_pt = 'Guaraná' WHERE name = 'Guaraná Soda';
UPDATE foods SET name_pt = 'Mate' WHERE name = 'Mate, Yerba Mate Tea';
UPDATE foods SET name_pt = 'Queijo Coalho' WHERE name = 'Queijo Coalho, Grilled Cheese';
UPDATE foods SET name_pt = 'Mandioca Frita' WHERE name = 'Fried Cassava';
UPDATE foods SET name_pt = 'Pamonha' WHERE name = 'Pamonha, Corn Paste';
UPDATE foods SET name_pt = 'Vatapá' WHERE name = 'Vatapá, Shrimp Bread Paste';
UPDATE foods SET name_pt = 'Beijinho' WHERE name = 'Beijinho, Coconut Truffle';
UPDATE foods SET name_pt = 'Quindim' WHERE name = 'Quindim, Coconut Custard';

-- ============================================================================
-- COMPREHENSIVE PORTUGUESE TRANSLATIONS
-- ============================================================================
-- Generated Portuguese (pt-BR) translations for all English-named foods
-- Covers 400+ foods across all categories
-- ============================================================================

-- DAIRY & MILK
UPDATE foods SET name_pt = 'Leite 2%' WHERE name = '2% Milk';
UPDATE foods SET name_pt = 'Leite Desnatado' WHERE name = 'Skim Milk (Nonfat)';
UPDATE foods SET name_pt = 'Leite Integral' WHERE name = 'Whole Milk (3.25%)';
UPDATE foods SET name_pt = 'Leite de Amêndoas Sem Açúcar' WHERE name = 'Almond Milk (Unsweetened)';
UPDATE foods SET name_pt = 'Leite de Aveia Sem Açúcar' WHERE name = 'Oat Milk (Unsweetened)';
UPDATE foods SET name_pt = 'Leite de Soja Sem Açúcar' WHERE name = 'Soy Milk (Unsweetened)';
UPDATE foods SET name_pt = 'Leite de Caju Sem Açúcar' WHERE name = 'Cashew Milk (Unsweetened)';
UPDATE foods SET name_pt = 'Leite de Coco Sem Açúcar' WHERE name = 'Coconut Milk (Beverage, Unsweetened)';

-- CHEESE
UPDATE foods SET name_pt = 'Queijo Cheddar' WHERE name = 'Cheddar Cheese';
UPDATE foods SET name_pt = 'Queijo Mussarela' WHERE name = 'Mozzarella (Part-Skim)';
UPDATE foods SET name_pt = 'Queijo Suíço' WHERE name = 'Swiss Cheese';
UPDATE foods SET name_pt = 'Queijo Parmesão Ralado' WHERE name = 'Parmesan (Grated)';
UPDATE foods SET name_pt = 'Queijo Feta' WHERE name = 'Feta Cheese';
UPDATE foods SET name_pt = 'Queijo de Cabra' WHERE name = 'Goat Cheese (Soft)';
UPDATE foods SET name_pt = 'Cream Cheese' WHERE name = 'Cream Cheese';
UPDATE foods SET name_pt = 'Queijo Cottage' WHERE name = 'Cottage Cheese (Low-Fat 2%)';
UPDATE foods SET name_pt = 'Queijo Ricota' WHERE name = 'Ricotta Cheese (Part-Skim)';
UPDATE foods SET name_pt = 'Queijo Gorgonzola' WHERE name = 'Blue Cheese (Crumbled)';

-- YOGURT
UPDATE foods SET name_pt = 'Iogurte Grego Natural Desnatado' WHERE name = 'Greek Yogurt (Plain, Nonfat)';
UPDATE foods SET name_pt = 'Iogurte Grego Natural 2%' WHERE name = 'Greek Yogurt (Plain, 2%)';
UPDATE foods SET name_pt = 'Iogurte Grego Natural Integral' WHERE name = 'Greek Yogurt (Plain, Full-Fat)';
UPDATE foods SET name_pt = 'Iogurte Natural Desnatado' WHERE name = 'Regular Yogurt (Plain, Low-Fat)';
UPDATE foods SET name_pt = 'Skyr (Iogurte Islandês)' WHERE name = 'Skyr (Icelandic Yogurt)';
UPDATE foods SET name_pt = 'Kefir Desnatado' WHERE name = 'Kefir (Plain, Low-Fat)';

-- PROTEIN SOURCES - CHICKEN
UPDATE foods SET name_pt = 'Peito de Frango Grelhado' WHERE name = 'Chicken Breast (Boneless, Skinless, Cooked)';
UPDATE foods SET name_pt = 'Peito de Frango Cru' WHERE name = 'Chicken Breast (Raw)';
UPDATE foods SET name_pt = 'Coxa de Frango sem Pele' WHERE name = 'Chicken Thighs (Boneless, Skinless, Cooked)';
UPDATE foods SET name_pt = 'Coxa de Frango com Pele' WHERE name = 'Chicken Thighs (With Skin, Cooked)';
UPDATE foods SET name_pt = 'Asinha de Frango' WHERE name = 'Chicken Wings (Cooked)';
UPDATE foods SET name_pt = 'Sobrecoxa de Frango' WHERE name = 'Chicken Drumsticks (With Skin, Cooked)';
UPDATE foods SET name_pt = 'Frango Moído' WHERE name = 'Ground Chicken (Cooked)';

-- BEEF
UPDATE foods SET name_pt = 'Carne Moída 80/20' WHERE name = 'Ground Beef (80/20, Cooked)';
UPDATE foods SET name_pt = 'Carne Moída 85/15' WHERE name = 'Ground Beef (85/15, Cooked)';
UPDATE foods SET name_pt = 'Carne Moída 90/10' WHERE name = 'Ground Beef (90/10, Cooked)';
UPDATE foods SET name_pt = 'Carne Moída 93/7' WHERE name = 'Ground Beef (93/7 Lean, Cooked)';
UPDATE foods SET name_pt = 'Bife Ancho' WHERE name = 'Ribeye Steak (Cooked)';
UPDATE foods SET name_pt = 'Contrafilé' WHERE name = 'Sirloin Steak (Cooked)';
UPDATE foods SET name_pt = 'Filé Mignon' WHERE name = 'Filet Mignon (Cooked)';
UPDATE foods SET name_pt = 'Fraldinha' WHERE name = 'Flank Steak (Cooked)';
UPDATE foods SET name_pt = 'Bife de Tira' WHERE name = 'NY Strip Steak (Cooked)';
UPDATE foods SET name_pt = 'Peito Bovino' WHERE name = 'Beef Brisket (Cooked)';
UPDATE foods SET name_pt = 'Costela Bovina' WHERE name = 'Beef Short Ribs (Cooked)';
UPDATE foods SET name_pt = 'Carne para Ensopado' WHERE name = 'Beef Stew Meat (Cooked)';

-- PORK
UPDATE foods SET name_pt = 'Costeleta de Porco' WHERE name = 'Pork Chop (Boneless, Cooked)';
UPDATE foods SET name_pt = 'Lombo de Porco' WHERE name = 'Pork Tenderloin (Cooked)';
UPDATE foods SET name_pt = 'Pernil de Porco Desfiado' WHERE name = 'Pork Shoulder (Pulled, Cooked)';
UPDATE foods SET name_pt = 'Bacon' WHERE name = 'Bacon (Cooked)';
UPDATE foods SET name_pt = 'Presunto Canadense' WHERE name = 'Canadian Bacon (Cooked)';
UPDATE foods SET name_pt = 'Linguiça de Porco' WHERE name = 'Pork Sausage (Cooked)';
UPDATE foods SET name_pt = 'Linguiça Italiana' WHERE name = 'Italian Sausage (Cooked)';
UPDATE foods SET name_pt = 'Costela de Porco ao Barbecue' WHERE name = 'Pork Ribs (BBQ, Cooked)';
UPDATE foods SET name_pt = 'Porco Moído' WHERE name = 'Ground Pork (Cooked)';
UPDATE foods SET name_pt = 'Presunto Fatiado' WHERE name = 'Ham (Deli, Sliced)';

-- TURKEY
UPDATE foods SET name_pt = 'Peito de Peru Assado' WHERE name = 'Turkey Breast (Roasted, Skinless)';
UPDATE foods SET name_pt = 'Peru Moído 93/7' WHERE name = 'Ground Turkey (93/7, Cooked)';
UPDATE foods SET name_pt = 'Peru Moído 85/15' WHERE name = 'Ground Turkey (85/15, Cooked)';
UPDATE foods SET name_pt = 'Linguiça de Peru' WHERE name = 'Turkey Sausage (Cooked)';
UPDATE foods SET name_pt = 'Peito de Peru Fatiado' WHERE name = 'Turkey Breast (Deli, Sliced)';

-- FISH & SEAFOOD
UPDATE foods SET name_pt = 'Salmão Atlântico' WHERE name = 'Salmon (Atlantic, Cooked)';
UPDATE foods SET name_pt = 'Salmão Fresco' WHERE name = 'Salmon (Fresh, Cooked)';
UPDATE foods SET name_pt = 'Salmão Enlatado' WHERE name = 'Salmon (Canned)';
UPDATE foods SET name_pt = 'Atum em Lata (água)' WHERE name = 'Tuna (Canned in Water)';
UPDATE foods SET name_pt = 'Atum em Lata (óleo)' WHERE name = 'Tuna (Canned in Oil)';
UPDATE foods SET name_pt = 'Bife de Atum' WHERE name = 'Tuna Steak (Cooked)';
UPDATE foods SET name_pt = 'Bacalhau' WHERE name = 'Cod (Cooked)';
UPDATE foods SET name_pt = 'Tilápia' WHERE name = 'Tilapia (Cooked)';
UPDATE foods SET name_pt = 'Mahi Mahi' WHERE name = 'Mahi Mahi (Cooked)';
UPDATE foods SET name_pt = 'Halibute' WHERE name = 'Halibut (Cooked)';
UPDATE foods SET name_pt = 'Truta Arco-íris' WHERE name = 'Trout (Rainbow, Cooked)';
UPDATE foods SET name_pt = 'Sardinhas em Conserva' WHERE name = 'Sardines (Canned in Oil)';
UPDATE foods SET name_pt = 'Camarão Cozido' WHERE name = 'Shrimp (Cooked)';
UPDATE foods SET name_pt = 'Caranguejo' WHERE name = 'Crab (Cooked)';
UPDATE foods SET name_pt = 'Vieiras' WHERE name = 'Scallops (Cooked)';
UPDATE foods SET name_pt = 'Lagosta' WHERE name = 'Lobster (Cooked)';
UPDATE foods SET name_pt = 'Bagre' WHERE name = 'Catfish (Cooked)';
UPDATE foods SET name_pt = 'Peito de Pato' WHERE name = 'Duck Breast (Cooked)';

-- EGGS
UPDATE foods SET name_pt = 'Ovos Grandes' WHERE name = 'Eggs (Large, Whole)';
UPDATE foods SET name_pt = 'Claras de Ovo' WHERE name = 'Egg Whites';

-- LEGUMES & BEANS
UPDATE foods SET name_pt = 'Lentilhas Cozidas' WHERE name = 'Lentils (Cooked)';
UPDATE foods SET name_pt = 'Grão de Bico Cozido' WHERE name = 'Chickpeas (Cooked)';
UPDATE foods SET name_pt = 'Feijão Preto Cozido' WHERE name = 'Black Beans (Cooked)';
UPDATE foods SET name_pt = 'Feijão Roxo' WHERE name = 'Kidney Beans (Cooked)';
UPDATE foods SET name_pt = 'Feijão Carioca' WHERE name = 'Pinto Beans (Cooked)';
UPDATE foods SET name_pt = 'Edamame' WHERE name = 'Edamame (Cooked)';

-- PLANT-BASED PROTEIN
UPDATE foods SET name_pt = 'Tofu Firme' WHERE name = 'Tofu (Firm)';
UPDATE foods SET name_pt = 'Tofu Extra Firme' WHERE name = 'Tofu (Extra Firm)';
UPDATE foods SET name_pt = 'Tempeh' WHERE name = 'Tempeh';
UPDATE foods SET name_pt = 'Seitan (Glúten de Trigo)' WHERE name = 'Seitan';
UPDATE foods SET name_pt = 'Hambúrguer Beyond Burger' WHERE name = 'Beyond Burger Patty';
UPDATE foods SET name_pt = 'Hambúrguer Impossible' WHERE name = 'Impossible Burger Patty';

-- GRAINS & RICE
UPDATE foods SET name_pt = 'Arroz Branco Cozido' WHERE name = 'White Rice (Cooked)';
UPDATE foods SET name_pt = 'Arroz Integral Cozido' WHERE name = 'Brown Rice (Cooked)';
UPDATE foods SET name_pt = 'Arroz Jasmim' WHERE name = 'Jasmine Rice (Cooked)';
UPDATE foods SET name_pt = 'Arroz Basmati' WHERE name = 'Basmati Rice (Cooked)';
UPDATE foods SET name_pt = 'Arroz Selvagem' WHERE name = 'Wild Rice (Cooked)';
UPDATE foods SET name_pt = 'Arroz Arborio' WHERE name = 'Arborio Rice (Cooked)';
UPDATE foods SET name_pt = 'Quinoa Cozida' WHERE name = 'Quinoa (Cooked)';
UPDATE foods SET name_pt = 'Cuscuz Marroquino' WHERE name = 'Couscous (Cooked)';
UPDATE foods SET name_pt = 'Bulgur' WHERE name = 'Bulgur (Cooked)';
UPDATE foods SET name_pt = 'Farro' WHERE name = 'Farro (Cooked)';
UPDATE foods SET name_pt = 'Cevada' WHERE name = 'Barley (Cooked)';

-- PASTA
UPDATE foods SET name_pt = 'Espaguete Cozido' WHERE name = 'Spaghetti (Cooked)';
UPDATE foods SET name_pt = 'Penne Cozido' WHERE name = 'Penne (Cooked)';
UPDATE foods SET name_pt = 'Fettuccine Cozido' WHERE name = 'Fettuccine (Cooked)';
UPDATE foods SET name_pt = 'Macarrão' WHERE name = 'Pasta (Cooked)';
UPDATE foods SET name_pt = 'Macarrão Integral' WHERE name = 'Whole Wheat Pasta (Cooked)';
UPDATE foods SET name_pt = 'Macarrão de Grão de Bico' WHERE name = 'Protein Pasta (Cooked)';
UPDATE foods SET name_pt = 'Talharim de Ovos' WHERE name = 'Egg Noodles (Cooked)';
UPDATE foods SET name_pt = 'Massa de Lasanha' WHERE name = 'Lasagna Noodles (Cooked)';
UPDATE foods SET name_pt = 'Macarrão Cotovelo' WHERE name = 'Macaroni (Cooked)';
UPDATE foods SET name_pt = 'Orzo' WHERE name = 'Orzo (Cooked)';
UPDATE foods SET name_pt = 'Lámen' WHERE name = 'Ramen Noodles (Cooked)';

-- BREAD
UPDATE foods SET name_pt = 'Pão de Forma Branco' WHERE name = 'White Bread (Sliced)';
UPDATE foods SET name_pt = 'Pão Integral' WHERE name = 'Whole Wheat Bread';
UPDATE foods SET name_pt = 'Pão de Fermentação Natural' WHERE name = 'Sourdough Bread';
UPDATE foods SET name_pt = 'Pão de Centeio' WHERE name = 'Rye Bread';
UPDATE foods SET name_pt = 'Pão de Grãos' WHERE name = 'Multigrain Bread';
UPDATE foods SET name_pt = 'Bagel' WHERE name = 'Bagel (Plain)';
UPDATE foods SET name_pt = 'Muffin Inglês' WHERE name = 'English Muffin';
UPDATE foods SET name_pt = 'Pão Sírio' WHERE name = 'Pita Bread (White)';
UPDATE foods SET name_pt = 'Pão Sírio Integral' WHERE name = 'Pita Bread (Whole Wheat)';
UPDATE foods SET name_pt = 'Pão Naan' WHERE name = 'Naan Bread';
UPDATE foods SET name_pt = 'Tortilha de Farinha' WHERE name = 'Tortilla (Flour, 8-inch)';
UPDATE foods SET name_pt = 'Tortilha de Milho' WHERE name = 'Tortilla (Corn, 6-inch)';
UPDATE foods SET name_pt = 'Croissant' WHERE name = 'Croissant (Plain)';
UPDATE foods SET name_pt = 'Pãozinho' WHERE name = 'Dinner Roll';
UPDATE foods SET name_pt = 'Pão de Hambúrguer' WHERE name = 'Hamburger Bun';
UPDATE foods SET name_pt = 'Pão de Hot Dog' WHERE name = 'Hot Dog Bun';
UPDATE foods SET name_pt = 'Baguete' WHERE name = 'Baguette';
UPDATE foods SET name_pt = 'Pão Brioche' WHERE name = 'Brioche Bread';
UPDATE foods SET name_pt = 'Pão Ciabatta' WHERE name = 'Ciabatta Bread';
UPDATE foods SET name_pt = 'Pão com Passas' WHERE name = 'Cinnamon Raisin Bread';

-- POTATOES
UPDATE foods SET name_pt = 'Batata Assada' WHERE name = 'Russet Potato (Baked)';
UPDATE foods SET name_pt = 'Batata Vermelha Cozida' WHERE name = 'Red Potato (Boiled)';
UPDATE foods SET name_pt = 'Batata Yukon Gold Assada' WHERE name = 'Yukon Gold Potato (Roasted)';
UPDATE foods SET name_pt = 'Purê de Batata' WHERE name = 'Mashed Potatoes (With Butter & Milk)';
UPDATE foods SET name_pt = 'Batata Frita' WHERE name = 'French Fries (Fast Food)';
UPDATE foods SET name_pt = 'Batata Rosti' WHERE name = 'Hash Browns';
UPDATE foods SET name_pt = 'Batata Sorriso' WHERE name = 'Tater Tots';
UPDATE foods SET name_pt = 'Chips de Batata' WHERE name = 'Potato Chips (Regular)';

-- CEREALS & OATS
UPDATE foods SET name_pt = 'Aveia Cozida' WHERE name = 'Oatmeal (Cooked)';
UPDATE foods SET name_pt = 'Aveia em Flocos' WHERE name = 'Steel Cut Oats (Cooked)';
UPDATE foods SET name_pt = 'Aveia Instantânea' WHERE name = 'Instant Oatmeal (Plain)';
UPDATE foods SET name_pt = 'Cheerios' WHERE name = 'Cheerios (Original)';
UPDATE foods SET name_pt = 'Corn Flakes' WHERE name = 'Corn Flakes';
UPDATE foods SET name_pt = 'Sucrilhos' WHERE name = 'Frosted Flakes';
UPDATE foods SET name_pt = 'Cereal de Farelo com Passas' WHERE name = 'Raisin Bran';
UPDATE foods SET name_pt = 'Granola' WHERE name = 'Granola (Plain)';
UPDATE foods SET name_pt = 'Grape-Nuts' WHERE name = 'Grape-Nuts';

-- VEGETABLES - LEAFY GREENS
UPDATE foods SET name_pt = 'Couve Crespa' WHERE name = 'Kale (Raw)';
UPDATE foods SET name_pt = 'Espinafre Cozido' WHERE name = 'Spinach (Cooked)';
UPDATE foods SET name_pt = 'Alface Romana' WHERE name = 'Romaine Lettuce';
UPDATE foods SET name_pt = 'Rúcula' WHERE name = 'Arugula';
UPDATE foods SET name_pt = 'Mix de Folhas' WHERE name = 'Mixed Salad Greens';
UPDATE foods SET name_pt = 'Couve Manteiga Cozida' WHERE name = 'Collard Greens (Cooked)';
UPDATE foods SET name_pt = 'Acelga Cozida' WHERE name = 'Swiss Chard (Cooked)';
UPDATE foods SET name_pt = 'Alface Americana' WHERE name = 'Butter Lettuce';
UPDATE foods SET name_pt = 'Espinafre Baby' WHERE name = 'Baby Spinach';

-- CRUCIFEROUS VEGETABLES
UPDATE foods SET name_pt = 'Brócolis Cru' WHERE name = 'Broccoli (Raw)';
UPDATE foods SET name_pt = 'Brócolis Cozido' WHERE name = 'Broccoli (Cooked)';
UPDATE foods SET name_pt = 'Couve-flor Crua' WHERE name = 'Cauliflower (Raw)';
UPDATE foods SET name_pt = 'Couve de Bruxelas' WHERE name = 'Brussels Sprouts (Cooked)';
UPDATE foods SET name_pt = 'Repolho Verde' WHERE name = 'Cabbage (Green, Raw)';
UPDATE foods SET name_pt = 'Repolho Roxo' WHERE name = 'Red Cabbage (Raw)';
UPDATE foods SET name_pt = 'Bok Choy' WHERE name = 'Bok Choy (Cooked)';

-- ROOT VEGETABLES
UPDATE foods SET name_pt = 'Cenoura Crua' WHERE name = 'Carrots (Raw)';
UPDATE foods SET name_pt = 'Beterraba Cozida' WHERE name = 'Beets (Cooked)';
UPDATE foods SET name_pt = 'Nabo Cozido' WHERE name = 'Turnips (Cooked)';
UPDATE foods SET name_pt = 'Pastinaca Assada' WHERE name = 'Parsnips (Cooked)';
UPDATE foods SET name_pt = 'Rabanete' WHERE name = 'Radishes';
UPDATE foods SET name_pt = 'Batata Doce Assada' WHERE name = 'Sweet Potato (Baked, with skin)';

-- SQUASH
UPDATE foods SET name_pt = 'Abobrinha Crua' WHERE name = 'Zucchini (Raw)';
UPDATE foods SET name_pt = 'Abóbora Amarela' WHERE name = 'Yellow Squash (Cooked)';
UPDATE foods SET name_pt = 'Abóbora Butternut' WHERE name = 'Butternut Squash (Cooked)';
UPDATE foods SET name_pt = 'Abóbora Bolota' WHERE name = 'Acorn Squash (Baked)';
UPDATE foods SET name_pt = 'Abóbora Espaguete' WHERE name = 'Spaghetti Squash (Cooked)';
UPDATE foods SET name_pt = 'Abóbora em Conserva' WHERE name = 'Pumpkin (Canned)';

-- NIGHTSHADES
UPDATE foods SET name_pt = 'Tomate' WHERE name = 'Tomato (Roma)';
UPDATE foods SET name_pt = 'Tomate Cereja' WHERE name = 'Cherry Tomatoes';
UPDATE foods SET name_pt = 'Tomate Grape' WHERE name = 'Grape Tomatoes';
UPDATE foods SET name_pt = 'Pimentão Verde' WHERE name = 'Bell Pepper (Green)';
UPDATE foods SET name_pt = 'Pimentão Vermelho' WHERE name = 'Bell Pepper (Red)';
UPDATE foods SET name_pt = 'Pimentão Amarelo' WHERE name = 'Bell Pepper (Yellow)';
UPDATE foods SET name_pt = 'Berinjela Grelhada' WHERE name = 'Eggplant (Cooked)';
UPDATE foods SET name_pt = 'Pimenta Jalapeño' WHERE name = 'Jalapeño Peppers';
UPDATE foods SET name_pt = 'Pimentão Fatiado' WHERE name = 'Bell Pepper Strips (Mixed)';

-- OTHER VEGETABLES
UPDATE foods SET name_pt = 'Pepino' WHERE name = 'Cucumber (With Peel)';
UPDATE foods SET name_pt = 'Aipo' WHERE name = 'Celery';
UPDATE foods SET name_pt = 'Cebola Amarela' WHERE name = 'Onion (Yellow)';
UPDATE foods SET name_pt = 'Cebola Roxa' WHERE name = 'Red Onion';
UPDATE foods SET name_pt = 'Cebolinha' WHERE name = 'Green Onions (Scallions)';
UPDATE foods SET name_pt = 'Alho' WHERE name = 'Garlic';
UPDATE foods SET name_pt = 'Cogumelo' WHERE name = 'Mushrooms (White, Raw)';
UPDATE foods SET name_pt = 'Cogumelo Portobello' WHERE name = 'Portobello Mushroom';
UPDATE foods SET name_pt = 'Aspargos Cozidos' WHERE name = 'Asparagus (Cooked)';
UPDATE foods SET name_pt = 'Vagem Cozida' WHERE name = 'Green Beans (Cooked)';
UPDATE foods SET name_pt = 'Milho Cozido' WHERE name = 'Corn (Yellow, Cooked)';
UPDATE foods SET name_pt = 'Ervilha Congelada' WHERE name = 'Peas (Green, Frozen, Cooked)';

-- BERRIES
UPDATE foods SET name_pt = 'Mirtilo Fresco' WHERE name = 'Blueberries (Fresh)';
UPDATE foods SET name_pt = 'Morango Fresco' WHERE name = 'Strawberries (Fresh)';
UPDATE foods SET name_pt = 'Framboesa Fresca' WHERE name = 'Raspberries (Fresh)';
UPDATE foods SET name_pt = 'Amora Fresca' WHERE name = 'Blackberries (Fresh)';
UPDATE foods SET name_pt = 'Cranberry Fresco' WHERE name = 'Cranberries (Fresh)';
UPDATE foods SET name_pt = 'Mirtilo' WHERE name = 'Blueberries';
UPDATE foods SET name_pt = 'Morango' WHERE name = 'Strawberries';

-- STONE FRUITS
UPDATE foods SET name_pt = 'Pêssego' WHERE name = 'Peach';
UPDATE foods SET name_pt = 'Nectarina' WHERE name = 'Nectarine';
UPDATE foods SET name_pt = 'Ameixa' WHERE name = 'Plum';
UPDATE foods SET name_pt = 'Damasco' WHERE name = 'Apricot';
UPDATE foods SET name_pt = 'Cereja Doce' WHERE name = 'Cherries (Sweet)';

-- TROPICAL FRUITS
UPDATE foods SET name_pt = 'Manga' WHERE name = 'Mango';
UPDATE foods SET name_pt = 'Abacaxi' WHERE name = 'Pineapple';
UPDATE foods SET name_pt = 'Mamão' WHERE name = 'Papaya';
UPDATE foods SET name_pt = 'Kiwi' WHERE name = 'Kiwi';
UPDATE foods SET name_pt = 'Pitaya' WHERE name = 'Dragon Fruit';

-- MELONS
UPDATE foods SET name_pt = 'Melancia' WHERE name = 'Watermelon';
UPDATE foods SET name_pt = 'Melão Cantaloupe' WHERE name = 'Cantaloupe';
UPDATE foods SET name_pt = 'Melão Honeydew' WHERE name = 'Honeydew Melon';

-- CITRUS
UPDATE foods SET name_pt = 'Laranja' WHERE name = 'Orange';
UPDATE foods SET name_pt = 'Toranja' WHERE name = 'Grapefruit';
UPDATE foods SET name_pt = 'Limão' WHERE name = 'Lemon';
UPDATE foods SET name_pt = 'Lima' WHERE name = 'Lime';
UPDATE foods SET name_pt = 'Tangerina' WHERE name = 'Tangerine';

-- OTHER FRUITS
UPDATE foods SET name_pt = 'Maçã Fuji' WHERE name = 'Apple (Fuji)';
UPDATE foods SET name_pt = 'Maçã' WHERE name = 'Apple (with skin)';
UPDATE foods SET name_pt = 'Uva Vermelha' WHERE name = 'Grapes (Red)';
UPDATE foods SET name_pt = 'Pera' WHERE name = 'Pear';
UPDATE foods SET name_pt = 'Banana' WHERE name = 'Banana';
UPDATE foods SET name_pt = 'Banana Pequena' WHERE name = 'Banana (Small)';
UPDATE foods SET name_pt = 'Romã' WHERE name = 'Pomegranate';
UPDATE foods SET name_pt = 'Figo Fresco' WHERE name = 'Fig (Fresh)';
UPDATE foods SET name_pt = 'Abacate' WHERE name = 'Avocado';
UPDATE foods SET name_pt = 'Abacate Hass' WHERE name = 'Avocado (Hass)';

-- OILS & FATS
UPDATE foods SET name_pt = 'Azeite de Oliva Extra Virgem' WHERE name = 'Olive Oil (Extra Virgin)';
UPDATE foods SET name_pt = 'Óleo de Coco' WHERE name = 'Coconut Oil';
UPDATE foods SET name_pt = 'Óleo de Abacate' WHERE name = 'Avocado Oil';
UPDATE foods SET name_pt = 'Óleo Vegetal' WHERE name = 'Vegetable Oil';
UPDATE foods SET name_pt = 'Óleo de Canola' WHERE name = 'Canola Oil';
UPDATE foods SET name_pt = 'Óleo de Gergelim' WHERE name = 'Sesame Oil';
UPDATE foods SET name_pt = 'Óleo de Semente de Uva' WHERE name = 'Grapeseed Oil';
UPDATE foods SET name_pt = 'Azeite' WHERE name = 'Olive Oil';

-- NUTS
UPDATE foods SET name_pt = 'Amêndoas' WHERE name = 'Almonds (Raw)';
UPDATE foods SET name_pt = 'Castanha de Caju' WHERE name = 'Cashews (Roasted)';
UPDATE foods SET name_pt = 'Nozes' WHERE name = 'Walnuts (Raw)';
UPDATE foods SET name_pt = 'Pecã' WHERE name = 'Pecans (Raw)';
UPDATE foods SET name_pt = 'Pistache' WHERE name = 'Pistachios (Roasted)';
UPDATE foods SET name_pt = 'Macadâmia' WHERE name = 'Macadamia Nuts';
UPDATE foods SET name_pt = 'Amendoim Torrado' WHERE name = 'Peanuts (Roasted)';
UPDATE foods SET name_pt = 'Castanha do Pará' WHERE name = 'Brazil Nuts';
UPDATE foods SET name_pt = 'Amêndoas' WHERE name = 'Almonds';

-- SEEDS
UPDATE foods SET name_pt = 'Semente de Chia' WHERE name = 'Chia Seeds';
UPDATE foods SET name_pt = 'Linhaça Moída' WHERE name = 'Flaxseed (Ground)';
UPDATE foods SET name_pt = 'Semente de Abóbora' WHERE name = 'Pumpkin Seeds (Pepitas)';
UPDATE foods SET name_pt = 'Semente de Girassol' WHERE name = 'Sunflower Seeds';
UPDATE foods SET name_pt = 'Semente de Cânhamo' WHERE name = 'Hemp Hearts';
UPDATE foods SET name_pt = 'Gergelim' WHERE name = 'Sesame Seeds';

-- NUT BUTTERS
UPDATE foods SET name_pt = 'Pasta de Amendoim Cremosa' WHERE name = 'Peanut Butter (Creamy)';
UPDATE foods SET name_pt = 'Pasta de Amendoim Natural' WHERE name = 'Peanut Butter (Natural)';
UPDATE foods SET name_pt = 'Pasta de Amêndoa' WHERE name = 'Almond Butter';
UPDATE foods SET name_pt = 'Pasta de Castanha de Caju' WHERE name = 'Cashew Butter';
UPDATE foods SET name_pt = 'Pasta de Semente de Girassol' WHERE name = 'Sunflower Seed Butter';
UPDATE foods SET name_pt = 'Pasta de Amendoim' WHERE name = 'Peanut Butter';

-- BUTTER & SPREADS
UPDATE foods SET name_pt = 'Manteiga com Sal' WHERE name = 'Butter (Salted)';
UPDATE foods SET name_pt = 'Manteiga sem Sal' WHERE name = 'Butter (Unsalted)';
UPDATE foods SET name_pt = 'Ghee (Manteiga Clarificada)' WHERE name = 'Ghee (Clarified Butter)';
UPDATE foods SET name_pt = 'Manteiga Vegana' WHERE name = 'Vegan Butter (Plant-Based)';
UPDATE foods SET name_pt = 'Manteiga' WHERE name = 'Butter';

-- SWEETENERS
UPDATE foods SET name_pt = 'Mel' WHERE name = 'Honey';

-- CONDIMENTS & SAUCES
UPDATE foods SET name_pt = 'Molho de Soja' WHERE name = 'Soy Sauce';
UPDATE foods SET name_pt = 'Molho Alfredo' WHERE name = 'Alfredo Sauce';
UPDATE foods SET name_pt = 'Molho Barbecue' WHERE name = 'BBQ Sauce';
UPDATE foods SET name_pt = 'Molho Caesar' WHERE name = 'Caesar Dressing';
UPDATE foods SET name_pt = 'Molho Blue Cheese' WHERE name = 'Blue Cheese Dressing';
UPDATE foods SET name_pt = 'Vinagrete Balsâmico' WHERE name = 'Balsamic Vinaigrette';
UPDATE foods SET name_pt = 'Mostarda Dijon' WHERE name = 'Dijon Mustard';
UPDATE foods SET name_pt = 'Molho de Peixe' WHERE name = 'Fish Sauce';
UPDATE foods SET name_pt = 'Molho de Coquetel' WHERE name = 'Cocktail Sauce';
UPDATE foods SET name_pt = 'Molho de Enchilada' WHERE name = 'Enchilada Sauce (Red)';
UPDATE foods SET name_pt = 'Chimichurri' WHERE name = 'Chimichurri';
UPDATE foods SET name_pt = 'Baba Ganoush' WHERE name = 'Baba Ganoush';
UPDATE foods SET name_pt = 'Maionese' WHERE name = 'Mayonnaise';

-- PROTEIN POWDERS
UPDATE foods SET name_pt = 'Whey Protein Isolado' WHERE name = 'Whey Protein Isolate (Unflavored)';
UPDATE foods SET name_pt = 'Whey Protein Concentrado Chocolate' WHERE name = 'Whey Protein Concentrate (Chocolate)';
UPDATE foods SET name_pt = 'Caseína Vanilla' WHERE name = 'Casein Protein (Vanilla)';
UPDATE foods SET name_pt = 'Proteína de Ervilha' WHERE name = 'Pea Protein Isolate';
UPDATE foods SET name_pt = 'Proteína Vegetal Mista' WHERE name = 'Plant-Based Protein Blend';
UPDATE foods SET name_pt = 'Colágeno em Pó' WHERE name = 'Collagen Peptides (Unflavored)';

-- SNACKS
UPDATE foods SET name_pt = 'Mix de Castanhas' WHERE name = 'Trail Mix';
UPDATE foods SET name_pt = 'Pipoca Sem Óleo' WHERE name = 'Popcorn (Air-popped)';
UPDATE foods SET name_pt = 'Pretzels' WHERE name = 'Pretzels';
UPDATE foods SET name_pt = 'Biscoito de Arroz' WHERE name = 'Rice Cakes';
UPDATE foods SET name_pt = 'Chocolate Amargo 70%' WHERE name = 'Dark Chocolate (70%)';
UPDATE foods SET name_pt = 'Chocolate Amargo' WHERE name = 'Dark Chocolate (70-85%)';

-- BEVERAGES
UPDATE foods SET name_pt = 'Café Preto' WHERE name = 'Coffee (Black)';
UPDATE foods SET name_pt = 'Chá Verde' WHERE name = 'Green Tea';
UPDATE foods SET name_pt = 'Suco de Laranja' WHERE name = 'Orange Juice';
UPDATE foods SET name_pt = 'Coca-Cola' WHERE name = 'Coca-Cola';
UPDATE foods SET name_pt = 'Água com Gás' WHERE name = 'Sparkling Water';
UPDATE foods SET name_pt = 'Chá Preto' WHERE name = 'Black Tea (Unsweetened)';
UPDATE foods SET name_pt = 'Água de Coco' WHERE name = 'Coconut Water';
UPDATE foods SET name_pt = 'Suco de Maçã' WHERE name = 'Apple Juice (100%)';
UPDATE foods SET name_pt = 'Suco de Cranberry' WHERE name = 'Cranberry Juice Cocktail';
UPDATE foods SET name_pt = 'Leite Chocolate' WHERE name = 'Chocolate Milk (Whole)';
UPDATE foods SET name_pt = 'Café Gelado' WHERE name = 'Cold Brew Coffee';
UPDATE foods SET name_pt = 'Café com Creme e Açúcar' WHERE name = 'Coffee with Cream and Sugar';
UPDATE foods SET name_pt = 'Chá Chai' WHERE name = 'Chai Tea Latte (Grande)';
UPDATE foods SET name_pt = 'Cappuccino' WHERE name = 'Cappuccino (Grande)';

-- RESTAURANT ITEMS - MCDONALD'S
UPDATE foods SET name_pt = 'Big Mac' WHERE name = 'Big Mac';
UPDATE foods SET name_pt = 'Batata Frita Média McDonald''s' WHERE name = 'McDonald''s Medium Fries';
UPDATE foods SET name_pt = 'Egg McMuffin' WHERE name = 'Egg McMuffin';
UPDATE foods SET name_pt = 'McChicken' WHERE name = 'McChicken';

-- RESTAURANT ITEMS - CHIPOTLE
UPDATE foods SET name_pt = 'Bowl de Frango Chipotle' WHERE name = 'Chipotle Chicken Bowl';
UPDATE foods SET name_pt = 'Burrito de Frango Chipotle' WHERE name = 'Chipotle Chicken Burrito';
UPDATE foods SET name_pt = 'Guacamole Chipotle' WHERE name = 'Chipotle Guacamole';

-- RESTAURANT ITEMS - SUBWAY
UPDATE foods SET name_pt = 'Sanduíche de Peru Subway' WHERE name = 'Subway 6" Turkey Breast';
UPDATE foods SET name_pt = 'Sanduíche BMT Subway' WHERE name = 'Subway Footlong Italian BMT';

-- RESTAURANT ITEMS - STARBUCKS
UPDATE foods SET name_pt = 'Latte Venti Starbucks' WHERE name = 'Starbucks Venti Caffe Latte (2% Milk)';
UPDATE foods SET name_pt = 'Sanduíche de Bacon e Gouda Starbucks' WHERE name = 'Starbucks Bacon Gouda Sandwich';
UPDATE foods SET name_pt = 'Protein Box Starbucks' WHERE name = 'Starbucks Protein Box';

-- RESTAURANT ITEMS - PANERA
UPDATE foods SET name_pt = 'Sopa de Brócolis e Queijo Panera' WHERE name = 'Panera Bread Bowl Broccoli Cheddar Soup';
UPDATE foods SET name_pt = 'Salada Caesar com Frango Panera' WHERE name = 'Panera Caesar Salad with Chicken';

-- RESTAURANT ITEMS - CHICK-FIL-A
UPDATE foods SET name_pt = 'Sanduíche Original Chick-fil-A' WHERE name = 'Chick-fil-A Original Chicken Sandwich';
UPDATE foods SET name_pt = 'Sanduíche Grelhado Chick-fil-A' WHERE name = 'Chick-fil-A Grilled Chicken Sandwich';
UPDATE foods SET name_pt = 'Batata Waffle Chick-fil-A' WHERE name = 'Chick-fil-A Waffle Fries (Medium)';

-- RESTAURANT ITEMS - PIZZA
UPDATE foods SET name_pt = 'Pizza Pepperoni Domino''s (1 fatia)' WHERE name = 'Domino''s Large Pepperoni Pizza (1 slice)';
UPDATE foods SET name_pt = 'Pizza Pepperoni Pizza Hut' WHERE name = 'Pizza Hut Personal Pan Pepperoni Pizza';

-- COMPLETE MEALS
UPDATE foods SET name_pt = 'Ovos Mexidos' WHERE name = 'Scrambled Eggs (2 eggs with milk)';
UPDATE foods SET name_pt = 'Smoothie de Proteína' WHERE name = 'Protein Smoothie';
UPDATE foods SET name_pt = 'Aveia com Granola' WHERE name = 'Overnight Oats';
UPDATE foods SET name_pt = 'Salada de Frango' WHERE name = 'Chicken Salad';
UPDATE foods SET name_pt = 'Espaguete à Bolonhesa' WHERE name = 'Spaghetti Bolognese';
UPDATE foods SET name_pt = 'Frango Xadrez' WHERE name = 'Chicken Stir Fry';
UPDATE foods SET name_pt = 'Sanduíche de Peru' WHERE name = 'Turkey Sandwich';
UPDATE foods SET name_pt = 'Panqueca de Proteína' WHERE name = 'Protein Pancakes';
UPDATE foods SET name_pt = 'Buddha Bowl' WHERE name = 'Buddha Bowl';
UPDATE foods SET name_pt = 'Wrap de Atum' WHERE name = 'Tuna Salad Wrap';

-- DESSERTS & SWEETS
UPDATE foods SET name_pt = 'Bolo de Anjo' WHERE name = 'Angel Food Cake';
UPDATE foods SET name_pt = 'Torta de Maçã' WHERE name = 'Apple Pie';
UPDATE foods SET name_pt = 'Pão de Banana' WHERE name = 'Banana Bread';
UPDATE foods SET name_pt = 'Torta de Creme de Banana' WHERE name = 'Banana Cream Pie';
UPDATE foods SET name_pt = 'Muffin de Mirtilo' WHERE name = 'Blueberry Muffin';
UPDATE foods SET name_pt = 'Torta de Mirtilo' WHERE name = 'Blueberry Pie';
UPDATE foods SET name_pt = 'Brownie' WHERE name = 'Brownie (Unfrosted)';
UPDATE foods SET name_pt = 'Bolo de Chocolate' WHERE name = 'Chocolate Cake (with Frosting)';
UPDATE foods SET name_pt = 'Biscoito de Chocolate' WHERE name = 'Chocolate Chip Cookies';
UPDATE foods SET name_pt = 'Muffin de Chocolate' WHERE name = 'Chocolate Chip Muffin';
UPDATE foods SET name_pt = 'Torta de Creme de Chocolate' WHERE name = 'Chocolate Cream Pie';
UPDATE foods SET name_pt = 'Croissant de Chocolate' WHERE name = 'Chocolate Croissant';
UPDATE foods SET name_pt = 'Cupcake de Chocolate' WHERE name = 'Chocolate Cupcake (with Frosting)';
UPDATE foods SET name_pt = 'Donut com Cobertura de Chocolate' WHERE name = 'Chocolate Frosted Donut';
UPDATE foods SET name_pt = 'Sorvete de Chocolate' WHERE name = 'Chocolate Ice Cream';
UPDATE foods SET name_pt = 'Sorvete de Menta com Chocolate' WHERE name = 'Chocolate Mint Ice Cream';
UPDATE foods SET name_pt = 'Mousse de Chocolate' WHERE name = 'Chocolate Mousse';
UPDATE foods SET name_pt = 'Rolo de Canela' WHERE name = 'Cinnamon Roll';
UPDATE foods SET name_pt = 'Rolo de Canela com Cobertura' WHERE name = 'Cinnamon Roll (with Icing)';
UPDATE foods SET name_pt = 'Torta de Cereja' WHERE name = 'Cherry Pie';
UPDATE foods SET name_pt = 'Cheesecake' WHERE name = 'Cheesecake (Plain)';
UPDATE foods SET name_pt = 'Cheesecake de Morango' WHERE name = 'Cheesecake (Strawberry)';
UPDATE foods SET name_pt = 'Torta Cobbler de Frutas Vermelhas' WHERE name = 'Cobbler (Berry)';
UPDATE foods SET name_pt = 'Torta Cobbler de Pêssego' WHERE name = 'Cobbler (Peach)';
UPDATE foods SET name_pt = 'Sorvete de Cookie Dough' WHERE name = 'Cookie Dough Ice Cream';
UPDATE foods SET name_pt = 'Sorvete de Cookies and Cream' WHERE name = 'Cookies and Cream Ice Cream';
UPDATE foods SET name_pt = 'Creme Brulee' WHERE name = 'Creme Brulee';
UPDATE foods SET name_pt = 'Donut Glacê' WHERE name = 'Donut (Glazed)';
UPDATE foods SET name_pt = 'Bolinhos de Donut' WHERE name = 'Donut Holes (Glazed)';
UPDATE foods SET name_pt = 'Eclair de Chocolate' WHERE name = 'Eclair (Chocolate)';
UPDATE foods SET name_pt = 'Flan' WHERE name = 'Flan';
UPDATE foods SET name_pt = 'Sorvete de Café' WHERE name = 'Coffee Ice Cream';
UPDATE foods SET name_pt = 'Sorvete de Butter Pecan' WHERE name = 'Butter Pecan Ice Cream';
UPDATE foods SET name_pt = 'Sorvete Creamsicle' WHERE name = 'Creamsicle';

-- BRANDED ITEMS
UPDATE foods SET name_pt = 'Chobani Iogurte Grego Morango' WHERE name = 'Chobani Greek Yogurt Strawberry';
UPDATE foods SET name_pt = 'Barra de Granola Nature Valley' WHERE name = 'Nature Valley Granola Bars - Oats & Honey';
UPDATE foods SET name_pt = 'Barra Quest Proteína' WHERE name = 'Quest Protein Bar - Chocolate Chip Cookie Dough';
UPDATE foods SET name_pt = 'Barra KIND' WHERE name = 'Kind Bar - Dark Chocolate Nuts & Sea Salt';
UPDATE foods SET name_pt = 'Barra Clif' WHERE name = 'Clif Bar - Chocolate Chip';
UPDATE foods SET name_pt = 'Homus Sabra' WHERE name = 'Sabra Classic Hummus';
UPDATE foods SET name_pt = 'Sorvete Ben & Jerry''s Brownie' WHERE name = 'Ben & Jerry''s Chocolate Fudge Brownie';
UPDATE foods SET name_pt = 'Sorvete Halo Top Vanilla' WHERE name = 'Halo Top Vanilla Bean';
UPDATE foods SET name_pt = 'Barra RX Mirtilo' WHERE name = 'RX Bar - Blueberry';
UPDATE foods SET name_pt = 'Leite de Soja Silk Vanilla' WHERE name = 'Silk Vanilla Soymilk';
UPDATE foods SET name_pt = 'Iogurte Dannon Light & Fit' WHERE name = 'Dannon Light & Fit Greek Vanilla';
UPDATE foods SET name_pt = 'Waffles Kodiak Cakes' WHERE name = 'Kodiak Cakes Power Waffles';
UPDATE foods SET name_pt = 'Frappuccino Starbucks Mocha' WHERE name = 'Starbucks Bottled Frappuccino - Mocha';
UPDATE foods SET name_pt = 'Shake Muscle Milk Chocolate' WHERE name = 'Muscle Milk Chocolate Protein Shake';
UPDATE foods SET name_pt = 'Barra Pure Protein' WHERE name = 'Pure Protein Chocolate Peanut Butter';
UPDATE foods SET name_pt = 'Cheerios Original' WHERE name = 'Cheerios Original';

-- SANDWICHES & BURGERS
UPDATE foods SET name_pt = 'Sanduíche BLT' WHERE name = 'BLT Sandwich';
UPDATE foods SET name_pt = 'Hambúrguer com Queijo' WHERE name = 'Cheeseburger (with Bun)';
UPDATE foods SET name_pt = 'Hambúrguer Bacon e Queijo' WHERE name = 'Bacon Cheeseburger';
UPDATE foods SET name_pt = 'Hambúrguer Duplo' WHERE name = 'Double Cheeseburger';
UPDATE foods SET name_pt = 'Sanduíche Club' WHERE name = 'Club Sandwich';
UPDATE foods SET name_pt = 'Sanduíche de Salada de Ovo' WHERE name = 'Egg Salad Sandwich';
UPDATE foods SET name_pt = 'Sanduíche de Salada de Frango' WHERE name = 'Chicken Salad Sandwich';
UPDATE foods SET name_pt = 'Sanduíche de Bologna' WHERE name = 'Bologna Sandwich';
UPDATE foods SET name_pt = 'Hot Dog' WHERE name = 'Hot Dog (Beef)';
UPDATE foods SET name_pt = 'Chili Dog' WHERE name = 'Chili Dog';

-- INTERNATIONAL DISHES
UPDATE foods SET name_pt = 'Banh Mi' WHERE name = 'Banh Mi';
UPDATE foods SET name_pt = 'Biryani de Frango' WHERE name = 'Biryani (Chicken)';
UPDATE foods SET name_pt = 'Frango ao Curry' WHERE name = 'Chicken Curry';
UPDATE foods SET name_pt = 'Frango Tikka Masala' WHERE name = 'Chicken Tikka Masala';
UPDATE foods SET name_pt = 'Frango Katsu' WHERE name = 'Chicken Katsu';
UPDATE foods SET name_pt = 'Frango Teriyaki' WHERE name = 'Chicken Teriyaki Bowl';
UPDATE foods SET name_pt = 'Falafel' WHERE name = 'Falafel (4 Pieces)';
UPDATE foods SET name_pt = 'Wrap de Falafel' WHERE name = 'Falafel Wrap';
UPDATE foods SET name_pt = 'California Roll' WHERE name = 'California Roll (8 Pieces)';
UPDATE foods SET name_pt = 'Pad Thai' WHERE name = 'Pad Thai (Chicken)';
UPDATE foods SET name_pt = 'Pho' WHERE name = 'Pho (Beef)';
UPDATE foods SET name_pt = 'Sushi Roll' WHERE name = 'Sushi Roll (Various)';
UPDATE foods SET name_pt = 'Chana Masala' WHERE name = 'Chana Masala';
UPDATE foods SET name_pt = 'Frango com Manteiga' WHERE name = 'Butter Chicken';
UPDATE foods SET name_pt = 'Chile Relleno' WHERE name = 'Chile Relleno';
