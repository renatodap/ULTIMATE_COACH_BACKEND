"""
Unit tests for nutrition_calculator service.

Tests nutrition calculations for simple, branded, and composed foods.
"""

import pytest
from decimal import Decimal
from app.services.nutrition_calculator import (
    NutritionData,
    round_decimal,
    calculate_simple_food_nutrition,
    calculate_composed_food_nutrition,
    calculate_food_nutrition,
    validate_nutrition,
)


# ============================================================================
# NUTRITION DATA TESTS
# ============================================================================

class TestNutritionData:
    """Test NutritionData class."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        nutrition = NutritionData(
            calories=Decimal('330'),
            protein_g=Decimal('62.0'),
            carbs_g=Decimal('10.5'),
            fat_g=Decimal('7.2'),
        )

        result = nutrition.to_dict()
        assert result['calories'] == 330.0
        assert result['protein_g'] == 62.0
        assert result['carbs_g'] == 10.5
        assert result['fat_g'] == 7.2

    def test_addition(self):
        """Test adding two nutrition objects."""
        n1 = NutritionData(
            calories=Decimal('100'),
            protein_g=Decimal('10'),
            carbs_g=Decimal('20'),
            fat_g=Decimal('5'),
        )
        n2 = NutritionData(
            calories=Decimal('150'),
            protein_g=Decimal('15'),
            carbs_g=Decimal('10'),
            fat_g=Decimal('8'),
        )

        total = n1 + n2
        assert total.calories == Decimal('250')
        assert total.protein_g == Decimal('25')
        assert total.carbs_g == Decimal('30')
        assert total.fat_g == Decimal('13')


# ============================================================================
# SIMPLE FOOD CALCULATION TESTS
# ============================================================================

class TestCalculateSimpleFoodNutrition:
    """Test nutrition calculation for simple foods."""

    def test_chicken_breast_200g(self):
        """Test chicken breast calculation."""
        food_data = {
            'calories_per_100g': 165,
            'protein_g_per_100g': 31,
            'carbs_g_per_100g': 0,
            'fat_g_per_100g': 3.6,
        }

        nutrition = calculate_simple_food_nutrition(food_data, Decimal('200'))

        # 200g = 2x per_100g values
        assert nutrition.calories == Decimal('330.0')
        assert nutrition.protein_g == Decimal('62.0')
        assert nutrition.carbs_g == Decimal('0.0')
        assert nutrition.fat_g == Decimal('7.2')

    def test_brown_rice_150g(self):
        """Test brown rice calculation."""
        food_data = {
            'calories_per_100g': 111,
            'protein_g_per_100g': 2.6,
            'carbs_g_per_100g': 23,
            'fat_g_per_100g': 0.9,
        }

        nutrition = calculate_simple_food_nutrition(food_data, Decimal('150'))

        # 150g = 1.5x per_100g values
        assert nutrition.calories == Decimal('166.5')
        assert nutrition.protein_g == Decimal('3.9')
        assert nutrition.carbs_g == Decimal('34.5')
        assert nutrition.fat_g == Decimal('1.4')  # 1.35 rounded to 1.4

    def test_50g_calculation(self):
        """Test calculation for 50g (half of per_100g)."""
        food_data = {
            'calories_per_100g': 200,
            'protein_g_per_100g': 20,
            'carbs_g_per_100g': 40,
            'fat_g_per_100g': 10,
        }

        nutrition = calculate_simple_food_nutrition(food_data, Decimal('50'))

        assert nutrition.calories == Decimal('100.0')
        assert nutrition.protein_g == Decimal('10.0')
        assert nutrition.carbs_g == Decimal('20.0')
        assert nutrition.fat_g == Decimal('5.0')

    def test_fractional_grams(self):
        """Test calculation with fractional grams."""
        food_data = {
            'calories_per_100g': 100,
            'protein_g_per_100g': 10,
            'carbs_g_per_100g': 20,
            'fat_g_per_100g': 5,
        }

        nutrition = calculate_simple_food_nutrition(food_data, Decimal('33.5'))

        # 33.5g = 0.335x per_100g values
        assert nutrition.calories == Decimal('33.5')
        assert nutrition.protein_g == Decimal('3.4')  # 3.35 rounded
        assert nutrition.carbs_g == Decimal('6.7')
        assert nutrition.fat_g == Decimal('1.7')  # 1.675 rounded

    def test_zero_macros(self):
        """Test food with zero carbs (like pure meat)."""
        food_data = {
            'calories_per_100g': 165,
            'protein_g_per_100g': 31,
            'carbs_g_per_100g': 0,
            'fat_g_per_100g': 3.6,
        }

        nutrition = calculate_simple_food_nutrition(food_data, Decimal('100'))

        assert nutrition.calories == Decimal('165.0')
        assert nutrition.carbs_g == Decimal('0.0')

    def test_decimal_precision(self):
        """Test that decimals are used (not floats)."""
        food_data = {
            'calories_per_100g': 165,
            'protein_g_per_100g': 31,
            'carbs_g_per_100g': 0,
            'fat_g_per_100g': 3.6,
        }

        nutrition = calculate_simple_food_nutrition(food_data, Decimal('100'))

        assert isinstance(nutrition.calories, Decimal)
        assert isinstance(nutrition.protein_g, Decimal)
        assert isinstance(nutrition.carbs_g, Decimal)
        assert isinstance(nutrition.fat_g, Decimal)


# ============================================================================
# COMPOSED FOOD CALCULATION TESTS
# ============================================================================

class TestCalculateComposedFoodNutrition:
    """Test nutrition calculation for composed foods (recipes)."""

    def test_simple_recipe_1_serving(self):
        """Test simple recipe with 1 serving."""
        # Mock recipe: 100g chicken + 100g rice
        recipe_items = [
            {'food_id': 'chicken', 'grams': 100},
            {'food_id': 'rice', 'grams': 100},
        ]

        # Mock food lookup function
        def get_food_by_id(food_id):
            foods = {
                'chicken': {
                    'composition_type': 'simple',
                    'calories_per_100g': 165,
                    'protein_g_per_100g': 31,
                    'carbs_g_per_100g': 0,
                    'fat_g_per_100g': 3.6,
                },
                'rice': {
                    'composition_type': 'simple',
                    'calories_per_100g': 111,
                    'protein_g_per_100g': 2.6,
                    'carbs_g_per_100g': 23,
                    'fat_g_per_100g': 0.9,
                },
            }
            return foods[food_id]

        nutrition = calculate_composed_food_nutrition(
            recipe_items,
            Decimal('1'),
            get_food_by_id,
        )

        # Total: 165+111=276 cal, 31+2.6=33.6g protein, 0+23=23g carbs, 3.6+0.9=4.5g fat
        assert nutrition.calories == Decimal('276.0')
        assert nutrition.protein_g == Decimal('33.6')
        assert nutrition.carbs_g == Decimal('23.0')
        assert nutrition.fat_g == Decimal('4.5')

    def test_recipe_2_servings(self):
        """Test recipe scaled to 2 servings."""
        recipe_items = [
            {'food_id': 'chicken', 'grams': 100},
        ]

        def get_food_by_id(food_id):
            return {
                'composition_type': 'simple',
                'calories_per_100g': 165,
                'protein_g_per_100g': 31,
                'carbs_g_per_100g': 0,
                'fat_g_per_100g': 3.6,
            }

        nutrition = calculate_composed_food_nutrition(
            recipe_items,
            Decimal('2'),  # 2 servings
            get_food_by_id,
        )

        # 165 cal × 2 = 330 cal
        assert nutrition.calories == Decimal('330.0')
        assert nutrition.protein_g == Decimal('62.0')

    def test_recipe_half_serving(self):
        """Test recipe with 0.5 servings."""
        recipe_items = [
            {'food_id': 'chicken', 'grams': 100},
        ]

        def get_food_by_id(food_id):
            return {
                'composition_type': 'simple',
                'calories_per_100g': 165,
                'protein_g_per_100g': 31,
                'carbs_g_per_100g': 0,
                'fat_g_per_100g': 3.6,
            }

        nutrition = calculate_composed_food_nutrition(
            recipe_items,
            Decimal('0.5'),  # Half serving
            get_food_by_id,
        )

        # 165 cal × 0.5 = 82.5 cal
        assert nutrition.calories == Decimal('82.5')
        assert nutrition.protein_g == Decimal('15.5')

    def test_complex_recipe_multiple_ingredients(self):
        """Test complex recipe with multiple ingredients."""
        recipe_items = [
            {'food_id': 'chicken', 'grams': 150},
            {'food_id': 'rice', 'grams': 200},
            {'food_id': 'broccoli', 'grams': 100},
        ]

        def get_food_by_id(food_id):
            foods = {
                'chicken': {
                    'composition_type': 'simple',
                    'calories_per_100g': 165,
                    'protein_g_per_100g': 31,
                    'carbs_g_per_100g': 0,
                    'fat_g_per_100g': 3.6,
                },
                'rice': {
                    'composition_type': 'simple',
                    'calories_per_100g': 111,
                    'protein_g_per_100g': 2.6,
                    'carbs_g_per_100g': 23,
                    'fat_g_per_100g': 0.9,
                },
                'broccoli': {
                    'composition_type': 'simple',
                    'calories_per_100g': 34,
                    'protein_g_per_100g': 2.8,
                    'carbs_g_per_100g': 7,
                    'fat_g_per_100g': 0.4,
                },
            }
            return foods[food_id]

        nutrition = calculate_composed_food_nutrition(
            recipe_items,
            Decimal('1'),
            get_food_by_id,
        )

        # Chicken: 165*1.5=247.5 cal, 31*1.5=46.5g protein
        # Rice: 111*2=222 cal, 2.6*2=5.2g protein, 23*2=46g carbs
        # Broccoli: 34*1=34 cal, 2.8*1=2.8g protein, 7*1=7g carbs
        # Total: 503.5 cal, 54.5g protein, 53g carbs
        expected_calories = Decimal('503.5')
        expected_protein = Decimal('54.5')
        expected_carbs = Decimal('53.0')

        assert nutrition.calories == expected_calories
        assert nutrition.protein_g == expected_protein
        assert nutrition.carbs_g == expected_carbs


# ============================================================================
# CALCULATE FOOD NUTRITION TESTS (MAIN ENTRY POINT)
# ============================================================================

class TestCalculateFoodNutrition:
    """Test main entry point for nutrition calculation."""

    def test_simple_food_by_grams(self):
        """Test simple food logged by grams."""
        food_data = {
            'composition_type': 'simple',
            'calories_per_100g': 165,
            'protein_g_per_100g': 31,
            'carbs_g_per_100g': 0,
            'fat_g_per_100g': 3.6,
        }

        result = calculate_food_nutrition(
            food_data,
            quantity=Decimal('200'),
            unit='grams',
        )

        assert result['grams'] == 200.0
        assert result['calories'] == 330.0
        assert result['protein_g'] == 62.0
        assert result['display_unit'] == 'g'
        assert result['display_label'] is None

    def test_simple_food_by_serving(self):
        """Test simple food logged by serving."""
        food_data = {
            'composition_type': 'simple',
            'calories_per_100g': 165,
            'protein_g_per_100g': 31,
            'carbs_g_per_100g': 0,
            'fat_g_per_100g': 3.6,
        }

        serving_data = {
            'serving_unit': 'scoop',
            'serving_label': 'large',
            'grams_per_serving': 30,
        }

        result = calculate_food_nutrition(
            food_data,
            quantity=Decimal('2'),  # 2 scoops
            unit='serving',
            serving_data=serving_data,
        )

        # 2 scoops × 30g/scoop = 60g
        # 60g × (165/100) = 99 cal
        assert result['grams'] == 60.0
        assert 98 <= result['calories'] <= 100
        assert result['display_unit'] == 'scoop'
        assert result['display_label'] == 'large'

    def test_composed_food_by_serving(self):
        """Test composed food logged by servings."""
        food_data = {
            'composition_type': 'composed',
            'recipe_items': [
                {'food_id': 'whey', 'grams': 30},
            ],
            'composed_total_grams': 30,
        }

        def get_food_by_id(food_id):
            return {
                'composition_type': 'simple',
                'calories_per_100g': 400,
                'protein_g_per_100g': 80,
                'carbs_g_per_100g': 10,
                'fat_g_per_100g': 5,
            }

        result = calculate_food_nutrition(
            food_data,
            quantity=Decimal('1.5'),  # 1.5 servings
            unit='serving',
            get_food_by_id=get_food_by_id,
        )

        # 1 serving = 30g whey = 120 cal
        # 1.5 servings = 180 cal
        assert result['grams'] == 45.0  # 30g × 1.5
        assert 179 <= result['calories'] <= 181
        assert result['display_unit'] == 'serving'

    def test_composed_food_by_grams_raises_error(self):
        """Composed foods cannot be logged by grams."""
        food_data = {'composition_type': 'composed'}

        with pytest.raises(ValueError, match="Composed foods cannot be logged by grams"):
            calculate_food_nutrition(
                food_data,
                quantity=Decimal('100'),
                unit='grams',
            )

    def test_serving_without_serving_data_raises_error(self):
        """Serving unit requires serving_data for simple foods."""
        food_data = {'composition_type': 'simple'}

        with pytest.raises(ValueError, match="serving_data required"):
            calculate_food_nutrition(
                food_data,
                quantity=Decimal('2'),
                unit='serving',
                serving_data=None,
            )

    def test_invalid_unit_raises_error(self):
        """Invalid unit should raise error."""
        food_data = {'composition_type': 'simple'}

        with pytest.raises(ValueError, match="Invalid unit"):
            calculate_food_nutrition(
                food_data,
                quantity=Decimal('100'),
                unit='liters',  # Invalid
            )


# ============================================================================
# VALIDATION TESTS
# ============================================================================

class TestValidateNutrition:
    """Test nutrition validation using 4-4-9 rule."""

    def test_valid_nutrition_chicken(self):
        """Test valid nutrition (chicken breast)."""
        nutrition = NutritionData(
            calories=Decimal('330'),
            protein_g=Decimal('62'),
            carbs_g=Decimal('0'),
            fat_g=Decimal('7.2'),
        )

        # Calculated: (62*4) + (0*4) + (7.2*9) = 248 + 64.8 = 312.8
        # Diff: 330 - 312.8 = 17.2 (5.2% of 330) ✓ within 15%
        assert validate_nutrition(nutrition) is True

    def test_valid_nutrition_mixed_meal(self):
        """Test valid nutrition (mixed meal)."""
        nutrition = NutritionData(
            calories=Decimal('500'),
            protein_g=Decimal('40'),
            carbs_g=Decimal('50'),
            fat_g=Decimal('15'),
        )

        # Calculated: (40*4) + (50*4) + (15*9) = 160 + 200 + 135 = 495
        # Diff: 500 - 495 = 5 (1% of 500) ✓ within 15%
        assert validate_nutrition(nutrition) is True

    def test_invalid_nutrition_too_high_calories(self):
        """Test invalid nutrition (calories too high)."""
        nutrition = NutritionData(
            calories=Decimal('1000'),  # Way too high
            protein_g=Decimal('40'),
            carbs_g=Decimal('50'),
            fat_g=Decimal('15'),
        )

        # Calculated: 495 cal
        # Diff: 1000 - 495 = 505 (50.5% of 1000) ✗ exceeds 15%
        assert validate_nutrition(nutrition) is False

    def test_valid_nutrition_with_fiber(self):
        """Test nutrition with implicit fiber (tolerance allows)."""
        # Foods with fiber may have lower actual calories
        nutrition = NutritionData(
            calories=Decimal('100'),
            protein_g=Decimal('5'),
            carbs_g=Decimal('20'),  # Includes fiber
            fat_g=Decimal('1'),
        )

        # Calculated: (5*4) + (20*4) + (1*9) = 20 + 80 + 9 = 109
        # Diff: 109 - 100 = 9 (9% of 100) ✓ within 15%
        assert validate_nutrition(nutrition) is True

    def test_custom_tolerance(self):
        """Test validation with custom tolerance."""
        nutrition = NutritionData(
            calories=Decimal('100'),
            protein_g=Decimal('10'),
            carbs_g=Decimal('10'),
            fat_g=Decimal('2'),
        )

        # Calculated: 40 + 40 + 18 = 98
        # Diff: 2 (2% of 100)

        assert validate_nutrition(nutrition, tolerance=0.05) is True  # 5% tolerance
        assert validate_nutrition(nutrition, tolerance=0.01) is False  # 1% tolerance


# ============================================================================
# ROUNDING TESTS
# ============================================================================

class TestRounding:
    """Test decimal rounding function."""

    def test_round_decimal_1_place(self):
        """Test rounding to 1 decimal place."""
        assert round_decimal(Decimal('1.23'), 1) == Decimal('1.2')
        assert round_decimal(Decimal('1.25'), 1) == Decimal('1.3')  # ROUND_HALF_UP
        assert round_decimal(Decimal('1.27'), 1) == Decimal('1.3')

    def test_round_decimal_0_places(self):
        """Test rounding to integer."""
        assert round_decimal(Decimal('1.4'), 0) == Decimal('1')
        assert round_decimal(Decimal('1.5'), 0) == Decimal('2')
        assert round_decimal(Decimal('1.9'), 0) == Decimal('2')

    def test_round_decimal_2_places(self):
        """Test rounding to 2 decimal places."""
        assert round_decimal(Decimal('1.234'), 2) == Decimal('1.23')
        assert round_decimal(Decimal('1.235'), 2) == Decimal('1.24')
        assert round_decimal(Decimal('1.239'), 2) == Decimal('1.24')
