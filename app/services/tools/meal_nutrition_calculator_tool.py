"""
Meal Nutrition Calculator Tool

Calculates nutrition totals for a list of foods.

Responsibilities:
- Search foods database by name
- Calculate nutrition per food item
- Sum total calories, protein, carbs, fats
- Handle unit conversions (grams, servings)

Usage:
    tool = MealNutritionCalculatorTool(supabase)
    result = await tool.execute(user_id, {
        "foods": [
            {"name": "chicken breast", "quantity": 200, "unit": "g"},
            {"name": "brown rice", "quantity": 150, "unit": "g"}
        ]
    })
"""

from typing import Dict, Any, List
from app.services.tools.base_tool import BaseTool
import structlog

logger = structlog.get_logger()


class MealNutritionCalculatorTool(BaseTool):
    """Calculate nutrition totals for a meal."""

    def get_definition(self) -> Dict[str, Any]:
        """
        Get tool definition for LLM.

        Returns:
            Tool definition dict
        """
        return {
            "name": "calculate_meal_nutrition",
            "description": (
                "Calculate total nutrition (calories, protein, carbs, fats) for a list of foods. "
                "Useful when planning meals or estimating nutrition before logging."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "foods": {
                        "type": "array",
                        "description": "List of food items to calculate",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Food name (will be searched in database)"
                                },
                                "quantity": {
                                    "type": "number",
                                    "description": "Amount of food"
                                },
                                "unit": {
                                    "type": "string",
                                    "description": "Unit (g, serving, cup, etc.)",
                                    "default": "g"
                                }
                            },
                            "required": ["name", "quantity"]
                        }
                    }
                },
                "required": ["foods"]
            }
        }

    async def execute(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate nutrition totals for foods.

        Args:
            user_id: User UUID (for logging)
            params: {
                "foods": [
                    {"name": "chicken breast", "quantity": 200, "unit": "g"},
                    {"name": "brown rice", "quantity": 150, "unit": "g"}
                ]
            }

        Returns:
            {
                "total_calories": 450,
                "total_protein_g": 52.3,
                "total_carbs_g": 32.5,
                "total_fats_g": 4.2,
                "foods_found": ["chicken breast", "brown rice"],
                "foods_not_found": []
            }
        """
        try:
            foods = params.get("foods", [])

            if not foods:
                return {
                    "error": "No foods provided",
                    "total_calories": 0,
                    "total_protein_g": 0,
                    "total_carbs_g": 0,
                    "total_fats_g": 0
                }

            total_calories = 0.0
            total_protein = 0.0
            total_carbs = 0.0
            total_fats = 0.0
            foods_found = []
            foods_not_found = []

            logger.info(
                "calculating_meal_nutrition",
                user_id=user_id,
                food_count=len(foods)
            )

            for food_item in foods:
                food_name = food_item.get("name", "")
                quantity = food_item.get("quantity", 0)
                unit = food_item.get("unit", "g")

                if not food_name or quantity <= 0:
                    continue

                # Search for food in database
                result = self.supabase.table("foods")\
                    .select("name, calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g")\
                    .ilike("name", f"%{food_name}%")\
                    .eq("is_public", True)\
                    .limit(1)\
                    .execute()

                if not result.data:
                    logger.warning(
                        "food_not_found",
                        user_id=user_id,
                        food_name=food_name
                    )
                    foods_not_found.append(food_name)
                    continue

                food = result.data[0]
                foods_found.append(food["name"])

                # Convert to grams (simplified - assumes 1 serving = 100g)
                grams = quantity if unit == "g" else quantity * 100

                # Calculate nutrition (per 100g basis)
                multiplier = grams / 100
                total_calories += food["calories_per_100g"] * multiplier
                total_protein += food["protein_g_per_100g"] * multiplier
                total_carbs += food["carbs_g_per_100g"] * multiplier
                total_fats += food["fat_g_per_100g"] * multiplier

            logger.info(
                "meal_nutrition_calculated",
                user_id=user_id,
                total_calories=round(total_calories),
                foods_found_count=len(foods_found),
                foods_not_found_count=len(foods_not_found)
            )

            return {
                "total_calories": round(total_calories),
                "total_protein_g": round(total_protein, 1),
                "total_carbs_g": round(total_carbs, 1),
                "total_fats_g": round(total_fats, 1),
                "foods_found": foods_found,
                "foods_not_found": foods_not_found
            }

        except Exception as e:
            logger.error(
                "meal_nutrition_calculation_failed",
                user_id=user_id,
                error=str(e),
                exc_info=True
            )
            return {
                "error": f"Failed to calculate meal nutrition: {str(e)}",
                "total_calories": 0,
                "total_protein_g": 0,
                "total_carbs_g": 0,
                "total_fats_g": 0
            }
