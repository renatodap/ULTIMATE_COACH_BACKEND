"""
Quick Meal Log Tool

Logs meals using AI nutrition estimates (no database lookups).

This is a complex tool that creates meals on-the-fly from AI-estimated nutrition data.
It's designed for conversational meal logging where the AI provides nutrition estimates.

Responsibilities:
- Create custom food entries with AI-estimated nutrition
- Detect and create serving units from food names
- Create meal items with proper validation
- Use nutrition_service for meal creation
- Support multiple meals in one call

Usage:
    tool = QuickMealLogTool(supabase)
    result = await tool.execute(user_id, {
        "meals": [
            {
                "meal_type": "lunch",
                "items": [
                    {
                        "food_name": "grilled chicken breast",
                        "grams": 200,
                        "calories": 330,
                        "protein_g": 62,
                        "carbs_g": 0,
                        "fat_g": 7
                    }
                ]
            }
        ]
    })

Note: This tool is complex and tightly coupled with nutrition_service.
      Consider further refactoring if it grows beyond its current scope.
"""

from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime
from uuid import UUID
import re
import structlog

from app.services.tools.base_tool import BaseTool

logger = structlog.get_logger()


class QuickMealLogTool(BaseTool):
    """Log meals quickly using AI nutrition estimates."""

    def get_definition(self) -> Dict[str, Any]:
        """
        Get tool definition for LLM.

        Returns:
            Tool definition dict
        """
        return {
            "name": "log_meals_quick",
            "description": (
                "Log one or more meals using AI-provided nutrition estimates. "
                "Creates custom food entries on-the-fly without requiring database lookups. "
                "Supports multi-item meals and multi-meal logging in one call. "
                "Use this when the user describes a meal conversationally and you have nutrition estimates."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "meals": {
                        "type": "array",
                        "description": "Array of meals to log",
                        "items": {
                            "type": "object",
                            "properties": {
                                "meal_type": {
                                    "type": "string",
                                    "description": "Meal type",
                                    "enum": ["breakfast", "lunch", "dinner", "snack", "other"]
                                },
                                "items": {
                                    "type": "array",
                                    "description": "Food items in this meal",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "food_name": {"type": "string"},
                                            "grams": {"type": "number"},
                                            "calories": {"type": "number"},
                                            "protein_g": {"type": "number"},
                                            "carbs_g": {"type": "number"},
                                            "fat_g": {"type": "number"}
                                        },
                                        "required": ["food_name", "grams", "calories", "protein_g", "carbs_g", "fat_g"]
                                    }
                                },
                                "notes": {
                                    "type": "string",
                                    "description": "Optional notes about the meal"
                                },
                                "logged_at": {
                                    "type": "string",
                                    "description": "ISO timestamp (defaults to now)"
                                }
                            },
                            "required": ["meal_type", "items"]
                        }
                    }
                },
                "required": ["meals"]
            }
        }

    def _parse_serving_info(self, food_name: str) -> Optional[Dict[str, Any]]:
        """
        Parse food name to detect serving units for better UX.

        Examples:
            "large mozzarella pizza" → unit="pizza", label="large"
            "2 slices pepperoni pizza" → unit="slice", quantity=2
            "medium burger" → unit="burger", label="medium"
            "300g chicken breast" → None (gram-based)

        Args:
            food_name: Food name to parse

        Returns:
            Dict with unit, label, quantity, base_name or None
        """
        # Common serving units
        serving_units = {
            # Whole items
            'pizza': 'pizza', 'burger': 'burger', 'sandwich': 'sandwich',
            'taco': 'taco', 'burrito': 'burrito', 'wrap': 'wrap',
            'bagel': 'bagel', 'muffin': 'muffin', 'donut': 'donut',
            'cookie': 'cookie', 'brownie': 'brownie',
            # Portions
            'slice': 'slice', 'slices': 'slice',
            'piece': 'piece', 'pieces': 'piece',
            'serving': 'serving', 'servings': 'serving',
            # Bowls/containers
            'bowl': 'bowl', 'cup': 'cup', 'plate': 'plate',
            'bar': 'bar',
        }

        # Size descriptors
        size_descriptors = ['small', 'medium', 'large', 'extra large', 'xl', 'jumbo']

        food_lower = food_name.lower()

        # Check for serving units
        detected_unit = None
        for key, unit in serving_units.items():
            if key in food_lower:
                detected_unit = unit
                break

        if not detected_unit:
            return None

        # Check for size descriptor
        detected_label = None
        for size in size_descriptors:
            if size in food_lower:
                detected_label = size
                break

        # Extract quantity (e.g., "2 slices")
        quantity_match = re.match(r'^(\d+)\s+', food_lower)
        quantity = int(quantity_match.group(1)) if quantity_match else 1

        # Clean base name
        base_name = food_name
        if quantity_match:
            base_name = base_name[quantity_match.end():]
        if detected_label:
            base_name = re.sub(detected_label, '', base_name, flags=re.IGNORECASE)
        base_name = base_name.strip()

        return {
            'unit': detected_unit,
            'label': detected_label,
            'quantity': quantity,
            'base_name': base_name
        }

    async def execute(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Log meals quickly with AI estimates.

        Args:
            user_id: User UUID
            params: {
                "meals": [
                    {
                        "meal_type": "lunch",
                        "items": [
                            {
                                "food_name": "grilled chicken",
                                "grams": 200,
                                "calories": 330,
                                "protein_g": 62,
                                "carbs_g": 0,
                                "fat_g": 7
                            }
                        ],
                        "notes": "Post-workout meal",
                        "logged_at": "2025-11-04T12:00:00Z"
                    }
                ]
            }

        Returns:
            {
                "success": true,
                "meals_logged": 1,
                "meals": [
                    {
                        "meal_id": "uuid",
                        "meal_type": "lunch",
                        "items_count": 1,
                        "total_calories": 330
                    }
                ]
            }
        """
        try:
            # Import here to avoid circular dependencies
            from app.services.nutrition_service import nutrition_service
            from app.models.meal import MealItemBase

            # Validate params
            if "meals" not in params:
                return {"success": False, "error": "Missing 'meals' parameter"}

            meals_data = params["meals"]
            if not isinstance(meals_data, list) or len(meals_data) == 0:
                return {"success": False, "error": "'meals' must be a non-empty array"}

            logged_meals = []

            # Process each meal
            for meal_data in meals_data:
                # Validate required fields
                if "meal_type" not in meal_data:
                    return {"success": False, "error": "Missing 'meal_type' in meal data"}
                if "items" not in meal_data:
                    return {"success": False, "error": "Missing 'items' in meal data"}

                meal_type = meal_data["meal_type"]
                items_data = meal_data["items"]
                notes = meal_data.get("notes")
                logged_at = meal_data.get("logged_at")

                # Parse logged_at timestamp
                if logged_at:
                    try:
                        logged_at_dt = datetime.fromisoformat(logged_at.replace('Z', '+00:00'))
                    except:
                        logged_at_dt = datetime.utcnow()
                else:
                    logged_at_dt = datetime.utcnow()

                # Validate meal_type
                valid_meal_types = ["breakfast", "lunch", "dinner", "snack", "other"]
                if meal_type not in valid_meal_types:
                    return {
                        "success": False,
                        "error": f"Invalid meal_type '{meal_type}'. Must be one of: {valid_meal_types}"
                    }

                # Validate items
                if not isinstance(items_data, list) or len(items_data) == 0:
                    return {"success": False, "error": f"'{meal_type}' meal must have at least one item"}

                # Process each food item
                meal_items = []

                for idx, item in enumerate(items_data):
                    # Validate required fields
                    required_fields = ["food_name", "grams", "calories", "protein_g", "carbs_g", "fat_g"]
                    missing_fields = [f for f in required_fields if f not in item]
                    if missing_fields:
                        return {
                            "success": False,
                            "error": f"Missing fields in item {idx+1}: {', '.join(missing_fields)}"
                        }

                    food_name = item["food_name"]
                    grams = Decimal(str(item["grams"]))
                    calories = int(item["calories"])
                    protein_g = round(Decimal(str(item["protein_g"])), 1)
                    carbs_g = round(Decimal(str(item["carbs_g"])), 1)
                    fat_g = round(Decimal(str(item["fat_g"])), 1)

                    # Validate values
                    if grams <= 0:
                        return {"success": False, "error": f"Grams must be > 0 for {food_name}"}
                    if calories < 0 or protein_g < 0 or carbs_g < 0 or fat_g < 0:
                        return {"success": False, "error": f"Nutrition values must be >= 0 for {food_name}"}

                    # Calculate per-100g values
                    per_100g_calories = float((Decimal(str(calories)) / grams) * 100)
                    per_100g_protein = float((protein_g / grams) * 100)
                    per_100g_carbs = float((carbs_g / grams) * 100)
                    per_100g_fat = float((fat_g / grams) * 100)

                    # Create custom food entry
                    food_result = self.supabase.table("foods").insert({
                        "created_by": user_id,
                        "name": food_name,
                        "composition_type": "simple",
                        "calories_per_100g": round(per_100g_calories, 1),
                        "protein_g_per_100g": round(per_100g_protein, 1),
                        "carbs_g_per_100g": round(per_100g_carbs, 1),
                        "fat_g_per_100g": round(per_100g_fat, 1),
                        "is_public": False,
                        "is_ai_estimated": True
                    }).execute()

                    if not food_result.data:
                        return {"success": False, "error": f"Failed to create custom food: {food_name}"}

                    custom_food_id = food_result.data[0]["id"]

                    # Detect serving units for better UX
                    serving_info = self._parse_serving_info(food_name)
                    serving_id = None
                    display_unit = "g"
                    display_label = None
                    quantity_val = grams

                    if serving_info:
                        # Create food_serving entry
                        try:
                            serving_result = self.supabase.table("food_servings").insert({
                                "food_id": custom_food_id,
                                "serving_size": Decimal(str(serving_info['quantity'])),
                                "serving_unit": serving_info['unit'],
                                "serving_label": serving_info['label'],
                                "grams_per_serving": float(grams / serving_info['quantity']),
                                "is_default": True,
                                "display_order": 0
                            }).execute()

                            if serving_result.data:
                                serving_id = serving_result.data[0]["id"]
                                display_unit = serving_info['unit']
                                display_label = serving_info['label']
                                quantity_val = Decimal(str(serving_info['quantity']))
                        except Exception as e:
                            logger.warning(
                                "serving_creation_failed",
                                user_id=user_id,
                                food_name=food_name,
                                error=str(e)
                            )

                    # Create meal item
                    meal_items.append(MealItemBase(
                        food_id=custom_food_id,
                        quantity=quantity_val,
                        serving_id=serving_id,
                        grams=grams,
                        calories=calories,
                        protein_g=protein_g,
                        carbs_g=carbs_g,
                        fat_g=fat_g,
                        display_unit=display_unit,
                        display_label=display_label,
                        display_order=idx
                    ))

                # Create meal using nutrition_service
                meal = await nutrition_service.create_meal(
                    user_id=UUID(user_id),
                    name=None,
                    meal_type=meal_type,
                    logged_at=logged_at_dt,
                    notes=notes,
                    items=meal_items,
                    source="coach_chat",
                    ai_confidence=0.85
                )

                logger.info(
                    "quick_meal_logged",
                    user_id=user_id,
                    meal_id=str(meal.id),
                    meal_type=meal_type,
                    items_count=len(meal_items),
                    total_calories=float(meal.total_calories)
                )

                logged_meals.append({
                    "meal_id": str(meal.id),
                    "meal_type": meal_type,
                    "items_count": len(meal_items),
                    "total_calories": int(meal.total_calories),
                    "total_protein_g": float(meal.total_protein_g),
                    "logged_at": meal.logged_at.isoformat()
                })

            return {
                "success": True,
                "meals_logged": len(logged_meals),
                "meals": logged_meals,
                "message": f"Logged {len(logged_meals)} meal(s) successfully"
            }

        except ValueError as e:
            logger.warning(
                "quick_meal_log_validation_error",
                user_id=user_id,
                error=str(e)
            )
            return {"success": False, "error": f"Validation failed: {str(e)}"}

        except Exception as e:
            logger.error(
                "quick_meal_log_failed",
                user_id=user_id,
                error=str(e),
                exc_info=True
            )
            return {"success": False, "error": f"Failed to log meals: {str(e)}"}
