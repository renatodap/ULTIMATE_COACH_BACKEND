"""
Nutrition Calculator Service

Handles all nutrition calculations with single source of truth:
- All nutrition stored as per_100g in foods table
- Calculate once at meal log time, store in meal_items
- Never recalculate historical data
"""

from typing import Dict, List, Optional
from decimal import Decimal, ROUND_HALF_UP


class NutritionData:
    """Nutrition data structure"""

    def __init__(
        self,
        calories: Decimal,
        protein_g: Decimal,
        carbs_g: Decimal,
        fat_g: Decimal,
    ):
        self.calories = calories
        self.protein_g = protein_g
        self.carbs_g = carbs_g
        self.fat_g = fat_g

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary with floats"""
        return {
            "calories": float(self.calories),
            "protein_g": float(self.protein_g),
            "carbs_g": float(self.carbs_g),
            "fat_g": float(self.fat_g),
        }

    def __add__(self, other: "NutritionData") -> "NutritionData":
        """Add two nutrition data objects"""
        return NutritionData(
            calories=self.calories + other.calories,
            protein_g=self.protein_g + other.protein_g,
            carbs_g=self.carbs_g + other.carbs_g,
            fat_g=self.fat_g + other.fat_g,
        )


def round_decimal(value: Decimal, decimals: int = 1) -> Decimal:
    """
    Round decimal to specified decimal places using ROUND_HALF_UP (banker's rounding)

    Args:
        value: Decimal value to round
        decimals: Number of decimal places (default: 1)

    Returns:
        Rounded decimal value
    """
    quantizer = Decimal(10) ** -decimals
    return value.quantize(quantizer, rounding=ROUND_HALF_UP)


def calculate_simple_food_nutrition(
    food_data: Dict,
    grams: Decimal,
) -> NutritionData:
    """
    Calculate nutrition for a simple or branded food based on grams.

    This is the fundamental calculation: scale per_100g values by grams.

    Args:
        food_data: Dict with per_100g nutrition values
        grams: Amount in grams

    Returns:
        NutritionData with calculated values

    Example:
        >>> food = {
        ...     "calories_per_100g": 165,
        ...     "protein_g_per_100g": 31,
        ...     "carbs_g_per_100g": 0,
        ...     "fat_g_per_100g": 3.6
        ... }
        >>> nutrition = calculate_simple_food_nutrition(food, Decimal("200"))
        >>> nutrition.calories
        Decimal('330.0')
        >>> nutrition.protein_g
        Decimal('62.0')
    """
    factor = grams / Decimal("100")

    calories = Decimal(str(food_data["calories_per_100g"])) * factor
    protein_g = Decimal(str(food_data["protein_g_per_100g"])) * factor
    carbs_g = Decimal(str(food_data["carbs_g_per_100g"])) * factor
    fat_g = Decimal(str(food_data["fat_g_per_100g"])) * factor

    return NutritionData(
        calories=round_decimal(calories),
        protein_g=round_decimal(protein_g),
        carbs_g=round_decimal(carbs_g),
        fat_g=round_decimal(fat_g),
    )


def calculate_composed_food_nutrition(
    recipe_items: List[Dict],
    servings: Decimal,
    get_food_by_id,  # Callable that fetches food data
) -> NutritionData:
    """
    Calculate nutrition for a composed food (meal template) based on servings.

    A composed food is made of multiple ingredients. This function:
    1. Calculates nutrition for each ingredient (recursive for nested composed foods)
    2. Sums them up to get total for 1 serving
    3. Scales by number of servings

    Args:
        recipe_items: List of {food_id: str, grams: Decimal}
        servings: Number of servings (can be fractional like 0.5, 1.5)
        get_food_by_id: Function to fetch food data by ID

    Returns:
        NutritionData with calculated values

    Example:
        >>> recipe_items = [
        ...     {"food_id": "chicken-id", "grams": 100},
        ...     {"food_id": "rice-id", "grams": 100},
        ...     {"food_id": "broccoli-id", "grams": 100}
        ... ]
        >>> nutrition = calculate_composed_food_nutrition(
        ...     recipe_items,
        ...     Decimal("1.5"),
        ...     get_food_by_id_func
        ... )
    """
    # Calculate total nutrition for 1 serving
    total_per_serving = NutritionData(
        calories=Decimal("0"),
        protein_g=Decimal("0"),
        carbs_g=Decimal("0"),
        fat_g=Decimal("0"),
    )

    for item in recipe_items:
        # Get ingredient food data
        ingredient = get_food_by_id(item["food_id"])

        # Check if ingredient itself is composed (recursive support)
        if ingredient.get("composition_type") == "composed":
            # Recursively calculate composed ingredient
            item_nutrition = calculate_composed_food_nutrition(
                ingredient["recipe_items"],
                Decimal("1"),  # Calculate for 1 serving of this ingredient
                get_food_by_id,
            )
        else:
            # Calculate from grams for simple/branded food
            item_nutrition = calculate_simple_food_nutrition(
                ingredient,
                Decimal(str(item["grams"])),
            )

        total_per_serving += item_nutrition

    # Scale by servings
    scaled = NutritionData(
        calories=round_decimal(total_per_serving.calories * servings),
        protein_g=round_decimal(total_per_serving.protein_g * servings),
        carbs_g=round_decimal(total_per_serving.carbs_g * servings),
        fat_g=round_decimal(total_per_serving.fat_g * servings),
    )

    return scaled


def calculate_food_nutrition(
    food_data: Dict,
    quantity: Decimal,
    unit: str,
    serving_data: Optional[Dict] = None,
    get_food_by_id=None,
) -> Dict:
    """
    Main entry point: Calculate nutrition for any food type.

    This function handles all three food types:
    1. Simple foods: Calculate from grams
    2. Composed foods: Calculate from servings (recursively from ingredients)
    3. Branded products: Calculate from grams

    Args:
        food_data: Complete food record with per_100g nutrition
        quantity: Amount (either grams or servings)
        unit: Either "grams" or "serving"
        serving_data: Serving info (required if unit="serving" for simple/branded foods)
        get_food_by_id: Function to fetch food data (required for composed foods)

    Returns:
        Dict with nutrition data and metadata for storage

    Raises:
        ValueError: If invalid combination of parameters
    """
    composition_type = food_data.get("composition_type", "simple")

    # Determine grams or servings based on composition type and unit
    if unit == "grams":
        # Direct grams input (simple or branded foods only)
        if composition_type == "composed":
            raise ValueError("Composed foods cannot be logged by grams, only by servings")

        nutrition = calculate_simple_food_nutrition(food_data, quantity)
        grams = quantity
        display_unit = "g"
        display_label = None

    elif unit == "serving":
        if composition_type == "composed":
            # Composed food: calculate from ingredients
            if not get_food_by_id:
                raise ValueError("get_food_by_id function required for composed foods")

            nutrition = calculate_composed_food_nutrition(
                food_data["recipe_items"],
                quantity,
                get_food_by_id,
            )

            # Calculate total grams
            grams = Decimal(str(food_data.get("composed_total_grams", 0))) * quantity
            display_unit = "serving"
            display_label = None

        else:
            # Simple/branded food with serving size
            if not serving_data:
                raise ValueError("serving_data required when unit='serving'")

            grams = Decimal(str(serving_data["grams_per_serving"])) * quantity
            nutrition = calculate_simple_food_nutrition(food_data, grams)
            display_unit = serving_data["serving_unit"]
            display_label = serving_data.get("serving_label")

    else:
        raise ValueError(f"Invalid unit: {unit}. Must be 'grams' or 'serving'")

    # Return complete data for meal_items insertion
    return {
        "grams": float(grams),
        "calories": float(nutrition.calories),
        "protein_g": float(nutrition.protein_g),
        "carbs_g": float(nutrition.carbs_g),
        "fat_g": float(nutrition.fat_g),
        "display_unit": display_unit,
        "display_label": display_label,
    }


def validate_nutrition(nutrition: NutritionData, tolerance: float = 0.15) -> bool:
    """
    Validate nutrition data using 4-4-9 calorie rule.

    Protein: 4 cal/g
    Carbs: 4 cal/g
    Fat: 9 cal/g

    Allows 15% tolerance for rounding, fiber, alcohol, and database inaccuracies.

    Args:
        nutrition: NutritionData to validate
        tolerance: Acceptable difference as percentage (default: 0.15 = 15%)

    Returns:
        True if validation passes, False otherwise

    Example:
        >>> nutrition = NutritionData(
        ...     calories=Decimal("330"),
        ...     protein_g=Decimal("62"),
        ...     carbs_g=Decimal("0"),
        ...     fat_g=Decimal("7.2")
        ... )
        >>> validate_nutrition(nutrition)
        True
    """
    calories_from_macros = (
        (nutrition.protein_g * Decimal("4"))
        + (nutrition.carbs_g * Decimal("4"))
        + (nutrition.fat_g * Decimal("9"))
    )

    diff = abs(nutrition.calories - calories_from_macros)
    allowed_diff = nutrition.calories * Decimal(str(tolerance))

    return diff <= allowed_diff
