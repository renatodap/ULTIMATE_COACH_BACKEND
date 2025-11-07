"""
Meal Adjustments Tool

Suggests meal adjustments to hit macro targets.

Responsibilities:
- Compare current meal macros to targets
- Calculate macro differences
- Generate actionable suggestions
- Recommend specific foods to add/remove

Usage:
    tool = MealAdjustmentsTool(supabase)
    result = await tool.execute(user_id, {
        "current_meal": {
            "protein": 30,
            "carbs": 50,
            "fats": 15
        },
        "target_macros": {
            "protein": 40,
            "carbs": 60,
            "fats": 20
        }
    })
"""

from typing import Dict, Any, Optional
from app.services.tools.base_tool import BaseTool
import structlog

logger = structlog.get_logger()


class MealAdjustmentsTool(BaseTool):
    """Suggest meal adjustments to hit macro targets."""

    def get_definition(self) -> Dict[str, Any]:
        """
        Get tool definition for LLM.

        Returns:
            Tool definition dict
        """
        return {
            "name": "suggest_meal_adjustments",
            "description": (
                "Suggest specific adjustments to a meal to better hit macro targets. "
                "Provides actionable recommendations (add/remove foods) based on macro differences."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "current_meal": {
                        "type": "object",
                        "description": "Current meal macros",
                        "properties": {
                            "protein": {"type": "number", "description": "Protein in grams"},
                            "carbs": {"type": "number", "description": "Carbs in grams"},
                            "fats": {"type": "number", "description": "Fats in grams"}
                        },
                        "required": ["protein", "carbs", "fats"]
                    },
                    "target_macros": {
                        "type": "object",
                        "description": "Target macros (optional, uses user's daily goals if not provided)",
                        "properties": {
                            "protein": {"type": "number"},
                            "carbs": {"type": "number"},
                            "fats": {"type": "number"}
                        }
                    }
                },
                "required": ["current_meal"]
            }
        }

    async def execute(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Suggest meal adjustments.

        Args:
            user_id: User UUID
            params: {
                "current_meal": {"protein": 30, "carbs": 50, "fats": 15},
                "target_macros": {"protein": 40, "carbs": 60, "fats": 20} (optional)
            }

        Returns:
            {
                "suggestions": [
                    "Add 10g more protein (chicken, fish, or protein powder)",
                    "Add 10g more carbs (rice, oats, or fruit)"
                ],
                "differences": {
                    "protein_diff": 10.0,
                    "carbs_diff": 10.0,
                    "fats_diff": 5.0
                },
                "is_balanced": false
            }
        """
        try:
            current_meal = params.get("current_meal", {})
            target_macros = params.get("target_macros")

            # Validate current meal
            if not current_meal or not all(k in current_meal for k in ["protein", "carbs", "fats"]):
                return {
                    "error": "Missing or invalid current_meal. Must include protein, carbs, and fats.",
                    "suggestions": []
                }

            # Get target macros from user profile if not provided
            if not target_macros:
                logger.debug(
                    "fetching_user_targets",
                    user_id=user_id
                )

                profile = self.supabase.table("profiles")\
                    .select("daily_protein_goal, daily_carbs_goal, daily_fat_goal")\
                    .eq("id", user_id)\
                    .single()\
                    .execute()

                if profile.data:
                    target_macros = {
                        "protein": profile.data.get("daily_protein_goal") or 150,
                        "carbs": profile.data.get("daily_carbs_goal") or 200,
                        "fats": profile.data.get("daily_fat_goal") or 60
                    }
                else:
                    # Default targets if profile not found
                    target_macros = {
                        "protein": 150,
                        "carbs": 200,
                        "fats": 60
                    }

            # Calculate differences
            protein_diff = target_macros["protein"] - current_meal["protein"]
            carbs_diff = target_macros["carbs"] - current_meal["carbs"]
            fats_diff = target_macros["fats"] - current_meal["fats"]

            suggestions = []

            # Protein suggestions
            if protein_diff > 10:
                suggestions.append(
                    f"Add {int(protein_diff)}g more protein (chicken, fish, or protein powder)"
                )
            elif protein_diff < -10:
                suggestions.append(
                    f"Reduce protein by {int(abs(protein_diff))}g"
                )

            # Carbs suggestions
            if carbs_diff > 20:
                suggestions.append(
                    f"Add {int(carbs_diff)}g more carbs (rice, oats, or fruit)"
                )
            elif carbs_diff < -20:
                suggestions.append(
                    f"Reduce carbs by {int(abs(carbs_diff))}g"
                )

            # Fats suggestions
            if fats_diff > 5:
                suggestions.append(
                    f"Add {int(fats_diff)}g more fats (nuts, avocado, or olive oil)"
                )
            elif fats_diff < -5:
                suggestions.append(
                    f"Reduce fats by {int(abs(fats_diff))}g"
                )

            # Check if meal is well-balanced
            is_balanced = (
                abs(protein_diff) <= 10 and
                abs(carbs_diff) <= 20 and
                abs(fats_diff) <= 5
            )

            if is_balanced:
                suggestions.append("Meal is well-balanced!")

            logger.info(
                "meal_adjustments_suggested",
                user_id=user_id,
                protein_diff=round(protein_diff, 1),
                carbs_diff=round(carbs_diff, 1),
                fats_diff=round(fats_diff, 1),
                is_balanced=is_balanced
            )

            return {
                "suggestions": suggestions,
                "differences": {
                    "protein_diff": round(protein_diff, 1),
                    "carbs_diff": round(carbs_diff, 1),
                    "fats_diff": round(fats_diff, 1)
                },
                "is_balanced": is_balanced,
                "target_macros": target_macros,
                "current_meal": current_meal
            }

        except Exception as e:
            logger.error(
                "meal_adjustments_failed",
                user_id=user_id,
                error=str(e),
                exc_info=True
            )
            return {
                "error": f"Failed to suggest meal adjustments: {str(e)}",
                "suggestions": []
            }
