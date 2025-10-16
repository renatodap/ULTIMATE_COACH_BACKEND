"""
Meal Item Transformer Service

Transforms LLM-extracted food data into proper meal items for database insertion.

Flow:
1. LLM extracts: [{name: "banana", quantity_g: 120}]
2. This service transforms to: [{food_id, quantity, serving_id, grams, calories, ...}]
3. nutrition_service.create_meal() receives proper format

This ensures coach meal logging uses the SAME calculation logic as manual logging.
"""

import structlog
from typing import List, Dict, Any, Optional
from decimal import Decimal

logger = structlog.get_logger()


class MealItemTransformerService:
    """
    Transforms extracted food names into proper meal items.

    Key Features:
    - Fuzzy search for foods by name
    - Handles gram-based logging (quantity = grams, serving_id = null)
    - Calculates nutrition using backend's per_100g logic
    - Mirrors manual meal logging format
    """

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    async def transform_foods_to_items(
        self,
        foods: List[Dict[str, Any]],
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Transform extracted food data to meal items.

        Args:
            foods: List of {name: str, quantity_g: float}
            user_id: User UUID for custom food access

        Returns:
            List of meal items ready for nutrition_service.create_meal():
            [{
                food_id: str,
                quantity: float,  # For gram-based: equals grams
                serving_id: None,  # Gram-based logging
                grams: float,
                calories: int,
                protein_g: float,
                carbs_g: float,
                fat_g: float,
                display_unit: "g",
                display_label: None
            }]

        Raises:
            ValueError: If food not found in database
        """
        logger.info(f"[MealTransformer] 🔄 Transforming {len(foods)} foods to items")

        items = []

        for idx, food_data in enumerate(foods):
            food_name = food_data.get("name")
            quantity_g = float(food_data.get("quantity_g", 100))

            logger.info(f"[MealTransformer] 🔍 Searching for '{food_name}' ({quantity_g}g)")

            # STEP 1: Search for food in database
            food = await self._search_food(food_name, user_id)

            if not food:
                logger.warning(f"[MealTransformer] ❌ Food not found: '{food_name}'")
                raise ValueError(f"Food not found in database: '{food_name}'")

            logger.info(f"[MealTransformer] ✅ Found: {food['name']} (ID: {food['id'][:8]}...)")

            # STEP 2: Calculate nutrition
            # Use GRAM-BASED LOGGING (same as manual logging when user selects "grams" mode)
            # quantity = grams, serving_id = null
            item = self._calculate_item_nutrition(food, quantity_g)

            logger.info(
                f"[MealTransformer] 📊 Calculated: "
                f"{quantity_g}g = {item['calories']}cal, "
                f"{item['protein_g']}g protein"
            )

            items.append(item)

        logger.info(f"[MealTransformer] ✅ Transformed {len(items)} items successfully")
        return items

    async def _search_food(
        self,
        food_name: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Search for food by name in database.

        Uses RPC function search_foods_safe() for PostgREST stability.

        Args:
            food_name: Food name to search for
            user_id: User UUID (for custom foods)

        Returns:
            Food dict with nutrition data, or None if not found
        """
        try:
            # Use RPC function to search foods (same as manual logging)
            result = self.supabase.rpc(
                'search_foods_safe',
                {
                    'search_query': food_name,
                    'user_id_param': user_id,
                    'result_limit': 1  # Get top match only
                }
            ).execute()

            if result.data and len(result.data) > 0:
                # Return best match
                food = result.data[0]

                # Validate required fields
                required = ['id', 'name', 'calories_per_100g', 'protein_g_per_100g',
                           'carbs_g_per_100g', 'fat_g_per_100g']
                if all(field in food for field in required):
                    return food
                else:
                    logger.warning(f"[MealTransformer] ⚠️ Food missing required fields: {food}")
                    return None

            return None

        except Exception as e:
            logger.error(f"[MealTransformer] ❌ Food search failed: {e}", exc_info=True)
            return None

    def _calculate_item_nutrition(
        self,
        food: Dict[str, Any],
        grams: float
    ) -> Dict[str, Any]:
        """
        Calculate nutrition for a food item using gram-based logging.

        Uses THE SAME LOGIC as nutrition_service.create_meal() for gram-based items.

        Args:
            food: Food dict from database
            grams: Amount in grams

        Returns:
            Meal item dict ready for create_meal()
        """
        # GRAM-BASED LOGGING LOGIC
        # This mirrors nutrition_service.py lines 634-666 (quantity semantic fix)
        # For gram-based: quantity = grams, serving_id = null

        # Calculate nutrition from per_100g values
        multiplier = Decimal(str(grams)) / Decimal("100")

        calories = float(Decimal(str(food['calories_per_100g'])) * multiplier)
        protein_g = float(Decimal(str(food['protein_g_per_100g'])) * multiplier)
        carbs_g = float(Decimal(str(food['carbs_g_per_100g'])) * multiplier)
        fat_g = float(Decimal(str(food['fat_g_per_100g'])) * multiplier)

        # Round for display
        # Backend will recalculate, but we provide reasonable values for preview
        calories_rounded = round(calories)
        protein_g_rounded = round(protein_g, 1)
        carbs_g_rounded = round(carbs_g, 1)
        fat_g_rounded = round(fat_g, 1)

        return {
            "food_id": food['id'],
            "quantity": float(grams),  # For gram-based: quantity = grams
            "serving_id": None,  # Gram-based logging has no serving
            "grams": float(grams),
            "calories": calories_rounded,
            "protein_g": protein_g_rounded,
            "carbs_g": carbs_g_rounded,
            "fat_g": fat_g_rounded,
            "display_unit": "g",  # Gram-based display
            "display_label": None  # No serving label for gram-based
        }


# Singleton
_meal_item_transformer: Optional[MealItemTransformerService] = None

def get_meal_item_transformer(supabase_client=None) -> MealItemTransformerService:
    """Get singleton MealItemTransformerService instance."""
    global _meal_item_transformer
    if _meal_item_transformer is None:
        if supabase_client is None:
            from app.services.supabase_service import get_service_client
            supabase_client = get_service_client()
        _meal_item_transformer = MealItemTransformerService(supabase_client)
    return _meal_item_transformer
