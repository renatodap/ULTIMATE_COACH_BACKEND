"""
Tool Service - Agentic Tool Calling for AI Coach

Provides 12 tools for on-demand data fetching:
1. get_user_profile - Get user goals, macros, restrictions
2. get_daily_nutrition_summary - Get today's totals
3. get_recent_meals - Get meal history
4. get_recent_activities - Get workout history
5. search_food_database - Nutrition lookup
6. get_body_measurements - Weight/measurements
7. calculate_progress_trend - Trend analysis
8. analyze_training_volume - Volume analysis
9. semantic_search_user_data - RAG search
10. calculate_meal_nutrition - Nutrition calc
11. suggest_meal_adjustments - Macro optimization
12. estimate_activity_calories - Calorie estimation

This is 80% cheaper than full RAG - only fetches what's needed!
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# ============================================================================
# TOOL DEFINITIONS (Claude/Groq format)
# ============================================================================

COACH_TOOLS = [
    {
        "name": "get_user_profile",
        "description": "Get user's profile including goals, body stats, macro targets, dietary restrictions, and preferences. Use this to personalize advice.",
        "input_schema": {
            "type": "object",
            "properties": {
                "include_goals": {
                    "type": "boolean",
                    "description": "Include user's fitness goals",
                    "default": True
                }
            },
            "required": []
        }
    },
    {
        "name": "search_food_database",
        "description": """Search for food nutrition information. Returns per-100g data that YOU must scale.

DATABASE STRUCTURE:
- foods table: Public database (simple ingredients, recipes, branded products)
  - composition_type='simple': Single ingredients (chicken, rice, banana)
  - composition_type='composed': Public recipes (Chicken Rice Bowl)
  - composition_type='branded': Packaged products (Chipotle Bowl)
- quick_meals table: User's personal meal shortcuts (e.g., "My Breakfast")

SEARCH PRIORITY:
1. User's quick_meals (personalized shortcuts)
2. Exact matches in foods table
3. Partial matches in foods table
4. User's frequently logged foods

IMPORTANT - NUTRITION CALCULATION:
- Tool returns nutrition PER 100g
- If user says "300g of chicken", YOU must multiply: (31g protein × 3 = 93g)
- If user says "2 bananas", estimate grams first (~120g each = 240g total)
- Always show your math to the user

Example:
User: "I ate 300g grilled chicken"
Tool returns: {"per_100g": {"protein": 31, "calories": 165}}
You calculate: 31 × 3 = 93g protein, 165 × 3 = 495 calories
You respond: "Logged. 300g chicken = 93g protein, 495 cal."
""",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Food name to search for (e.g., 'chicken breast', 'banana', 'my breakfast')"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of results to return (default: 5, max: 10)",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_daily_nutrition_summary",
        "description": "Get today's nutrition totals (calories, protein, carbs, fats). Returns EMPTY in MVP - no meal logging yet.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format (default: today)"
                }
            },
            "required": []
        }
    },
    {
        "name": "get_recent_meals",
        "description": "Get user's recent meals. Returns EMPTY in MVP - no meal logging yet.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Number of days to look back",
                    "default": 7
                },
                "limit": {
                    "type": "integer",
                    "description": "Max number of meals to return",
                    "default": 20
                }
            },
            "required": []
        }
    },
    {
        "name": "get_recent_activities",
        "description": "Get user's recent workouts/activities. Returns EMPTY in MVP - no activity logging yet.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Number of days to look back",
                    "default": 7
                },
                "limit": {
                    "type": "integer",
                    "description": "Max number of activities to return",
                    "default": 20
                }
            },
            "required": []
        }
    },
    {
        "name": "get_body_measurements",
        "description": "Get user's body measurements history (weight, body fat, etc.). Returns EMPTY in MVP - no measurements yet.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Number of days to look back",
                    "default": 30
                }
            },
            "required": []
        }
    },
    {
        "name": "calculate_progress_trend",
        "description": "Calculate trend for a metric (weight, calories, etc.). Returns EMPTY in MVP - no historical data yet.",
        "input_schema": {
            "type": "object",
            "properties": {
                "metric": {
                    "type": "string",
                    "description": "Metric to analyze (e.g., 'weight', 'calories', 'protein')"
                },
                "days": {
                    "type": "integer",
                    "description": "Number of days to analyze",
                    "default": 30
                }
            },
            "required": ["metric"]
        }
    },
    {
        "name": "analyze_training_volume",
        "description": "Analyze training volume and intensity. Returns EMPTY in MVP - no activity data yet.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Number of days to analyze",
                    "default": 7
                }
            },
            "required": []
        }
    },
    {
        "name": "semantic_search_user_data",
        "description": "Search user's conversation history semantically using embeddings. Returns EMPTY in MVP - no embeddings yet.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language search query"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of results to return",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "calculate_meal_nutrition",
        "description": "Calculate nutrition for a list of foods with quantities.",
        "input_schema": {
            "type": "object",
            "properties": {
                "foods": {
                    "type": "array",
                    "description": "List of foods with quantities",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "quantity": {"type": "number"},
                            "unit": {"type": "string"}
                        }
                    }
                }
            },
            "required": ["foods"]
        }
    },
    {
        "name": "suggest_meal_adjustments",
        "description": "Suggest adjustments to a meal to hit macro targets.",
        "input_schema": {
            "type": "object",
            "properties": {
                "current_meal": {
                    "type": "object",
                    "description": "Current meal nutrition",
                    "properties": {
                        "calories": {"type": "number"},
                        "protein": {"type": "number"},
                        "carbs": {"type": "number"},
                        "fats": {"type": "number"}
                    }
                },
                "target_macros": {
                    "type": "object",
                    "description": "Target macros (optional, uses user's goals if not provided)"
                }
            },
            "required": ["current_meal"]
        }
    },
    {
        "name": "estimate_activity_calories",
        "description": "Estimate calories burned for an activity.",
        "input_schema": {
            "type": "object",
            "properties": {
                "activity_type": {
                    "type": "string",
                    "description": "Type of activity (e.g., 'running', 'cycling', 'strength training')"
                },
                "duration_minutes": {
                    "type": "number",
                    "description": "Duration in minutes"
                },
                "intensity": {
                    "type": "string",
                    "description": "Intensity level",
                    "enum": ["low", "moderate", "high"]
                }
            },
            "required": ["activity_type", "duration_minutes"]
        }
    }
]


# ============================================================================
# TOOL SERVICE
# ============================================================================

class ToolService:
    """
    Executes tools for agentic AI coach.

    Each tool is a function that can be called by Claude/Groq.
    """

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    async def execute_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        user_id: str
    ) -> Any:
        """
        Execute a tool and return result.

        Args:
            tool_name: Name of tool to execute
            tool_input: Tool input parameters
            user_id: User UUID (for data access)

        Returns:
            Tool result (any type)
        """
        logger.info(f"[ToolService] 🛠️ Executing: {tool_name}")

        # Route to appropriate handler
        if tool_name == "get_user_profile":
            return await self._get_user_profile(user_id, tool_input)
        elif tool_name == "search_food_database":
            # Pass user_id for personalized search (quick_meals)
            tool_input["user_id"] = user_id
            return await self._search_food_database(tool_input)
        elif tool_name == "get_daily_nutrition_summary":
            return await self._get_daily_nutrition_summary(user_id, tool_input)
        elif tool_name == "get_recent_meals":
            return await self._get_recent_meals(user_id, tool_input)
        elif tool_name == "get_recent_activities":
            return await self._get_recent_activities(user_id, tool_input)
        elif tool_name == "get_body_measurements":
            return await self._get_body_measurements(user_id, tool_input)
        elif tool_name == "calculate_progress_trend":
            return await self._calculate_progress_trend(user_id, tool_input)
        elif tool_name == "analyze_training_volume":
            return await self._analyze_training_volume(user_id, tool_input)
        elif tool_name == "semantic_search_user_data":
            return await self._semantic_search_user_data(user_id, tool_input)
        elif tool_name == "calculate_meal_nutrition":
            return await self._calculate_meal_nutrition(tool_input)
        elif tool_name == "suggest_meal_adjustments":
            return await self._suggest_meal_adjustments(user_id, tool_input)
        elif tool_name == "estimate_activity_calories":
            return await self._estimate_activity_calories(user_id, tool_input)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    # ========================================================================
    # TOOL IMPLEMENTATIONS
    # ========================================================================

    async def _get_user_profile(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get user profile with goals and preferences."""
        try:
            result = self.supabase.table("profiles")\
                .select("*")\
                .eq("id", user_id)\
                .single()\
                .execute()

            if not result.data:
                return {"error": "Profile not found"}

            profile = result.data

            # Format response
            return {
                "full_name": profile.get("full_name"),
                "primary_goal": profile.get("primary_goal"),
                "experience_level": profile.get("experience_level"),
                "daily_calorie_goal": profile.get("daily_calorie_goal"),
                "daily_protein_goal": profile.get("daily_protein_goal"),
                "daily_carbs_goal": profile.get("daily_carbs_goal"),
                "daily_fat_goal": profile.get("daily_fat_goal"),
                "unit_system": profile.get("unit_system", "imperial"),
                "language": profile.get("language", "en")
            }
        except Exception as e:
            logger.error(f"[ToolService] get_user_profile failed: {e}")
            return {"error": str(e)}

    async def _search_food_database(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        SMART food database search with ranking:
        1. User's quick_meals (personalized shortcuts)
        2. Exact matches in foods table
        3. Partial matches in foods table
        4. Prioritize by composition_type (simple > composed > branded)
        5. Track user frequency (future enhancement)
        """
        try:
            query = params["query"].lower().strip()
            limit = min(params.get("limit", 5), 10)  # Max 10 results
            user_id = params.get("user_id")  # Passed from execute_tool

            results = []
            seen_names = set()  # Deduplicate

            # ================================================================
            # STEP 1: Search user's quick_meals (HIGHEST PRIORITY)
            # ================================================================
            if user_id:
                try:
                    quick_meals_result = self.supabase.table("quick_meals")\
                        .select("""
                            id, name, description,
                            total_calories, total_protein_g, total_carbs_g, total_fat_g
                        """)\
                        .eq("user_id", user_id)\
                        .ilike("name", f"%{query}%")\
                        .limit(3)\
                        .execute()

                    for meal in quick_meals_result.data or []:
                        name_key = meal["name"].lower()
                        if name_key in seen_names:
                            continue
                        seen_names.add(name_key)

                        results.append({
                            "source": "quick_meal",
                            "name": meal["name"],
                            "description": meal.get("description"),
                            "is_user_meal": True,
                            "per_100g": {
                                "calories": meal["total_calories"],
                                "protein": meal["total_protein_g"],
                                "carbs": meal["total_carbs_g"],
                                "fats": meal["total_fat_g"]
                            },
                            "note": "This is YOUR saved meal. Nutrition shown is total for this meal."
                        })

                        if len(results) >= limit:
                            return results
                except Exception as e:
                    logger.warning(f"[ToolService] quick_meals search failed: {e}")

            # ================================================================
            # STEP 2: Search public foods table (with smart ranking)
            # ================================================================

            # Search with ILIKE (case-insensitive partial match)
            foods_result = self.supabase.table("foods")\
                .select("""
                    id, name, brand_name, composition_type,
                    calories_per_100g, protein_g_per_100g,
                    carbs_g_per_100g, fat_g_per_100g,
                    serving_size_g, serving_size_description
                """)\
                .or_(f"name.ilike.%{query}%,brand_name.ilike.%{query}%")\
                .eq("is_public", True)\
                .limit(20)\
                .execute()

            if not foods_result.data:
                # No results at all
                return [] if not results else results

            # ================================================================
            # STEP 3: Rank and sort results
            # ================================================================
            scored_foods = []
            for food in foods_result.data:
                name_key = food["name"].lower()
                if name_key in seen_names:
                    continue

                # Calculate relevance score
                score = self._calculate_relevance_score(
                    query=query,
                    food_name=food["name"],
                    brand_name=food.get("brand_name"),
                    composition_type=food.get("composition_type")
                )

                scored_foods.append((score, food))

            # Sort by score (highest first)
            scored_foods.sort(key=lambda x: x[0], reverse=True)

            # ================================================================
            # STEP 4: Format and return results
            # ================================================================
            for score, food in scored_foods:
                if len(results) >= limit:
                    break

                name_key = food["name"].lower()
                if name_key in seen_names:
                    continue
                seen_names.add(name_key)

                result_item = {
                    "source": "foods_database",
                    "name": food["name"],
                    "brand": food.get("brand_name"),
                    "composition_type": food.get("composition_type", "simple"),
                    "per_100g": {
                        "calories": food["calories_per_100g"],
                        "protein": food["protein_g_per_100g"],
                        "carbs": food["carbs_g_per_100g"],
                        "fats": food["fat_g_per_100g"]
                    }
                }

                # Add serving size info if available
                if food.get("serving_size_g"):
                    result_item["serving_size"] = {
                        "grams": food["serving_size_g"],
                        "description": food.get("serving_size_description")
                    }

                results.append(result_item)

            return results

        except Exception as e:
            logger.error(f"[ToolService] search_food_database failed: {e}", exc_info=True)
            return []

    def _calculate_relevance_score(
        self,
        query: str,
        food_name: str,
        brand_name: Optional[str],
        composition_type: Optional[str]
    ) -> float:
        """
        Calculate relevance score for search ranking.

        Scoring:
        - Exact match: +100
        - Starts with query: +50
        - Contains query: +20
        - composition_type='simple': +10 (ingredients prioritized)
        - composition_type='composed': +5
        - composition_type='branded': +0
        - Brand match: +15
        """
        score = 0.0
        query_lower = query.lower()
        name_lower = food_name.lower()
        brand_lower = brand_name.lower() if brand_name else ""

        # Exact match (highest priority)
        if name_lower == query_lower or brand_lower == query_lower:
            score += 100

        # Starts with query
        elif name_lower.startswith(query_lower):
            score += 50

        # Contains query
        elif query_lower in name_lower:
            score += 20

        # Brand name contains query
        if brand_name and query_lower in brand_lower:
            score += 15

        # Composition type priority
        # Simple ingredients (chicken, rice) are prioritized for basic searches
        if composition_type == "simple":
            score += 10
        elif composition_type == "composed":
            score += 5
        # branded gets +0 (lowest priority unless exact match)

        return score

    async def _get_daily_nutrition_summary(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get today's nutrition totals. MVP: Returns empty."""
        # TODO: Implement when meal logging exists
        return {
            "message": "No meal data available yet. Meal logging coming soon!",
            "totals": None
        }

    async def _get_recent_meals(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get recent meals. MVP: Returns empty."""
        # TODO: Implement when meal logging exists
        return {
            "message": "No meal history available yet. Tell me what you ate and I'll help!",
            "meals": []
        }

    async def _get_recent_activities(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get recent activities. MVP: Returns empty."""
        # TODO: Implement when activity logging exists
        return {
            "message": "No activity history available yet. Tell me about your workout!",
            "activities": []
        }

    async def _get_body_measurements(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get body measurements. MVP: Returns empty."""
        # TODO: Implement when measurements exist
        return {
            "message": "No measurement data available yet.",
            "measurements": []
        }

    async def _calculate_progress_trend(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate progress trend. MVP: Returns empty."""
        # TODO: Implement when historical data exists
        return {
            "message": "Not enough data yet to calculate trends.",
            "trend": None
        }

    async def _analyze_training_volume(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze training volume. MVP: Returns empty."""
        # TODO: Implement when activity data exists
        return {
            "message": "No training data available yet.",
            "analysis": None
        }

    async def _semantic_search_user_data(self, user_id: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Semantic search. MVP: Returns empty."""
        # TODO: Implement when embeddings exist
        return []

    async def _calculate_meal_nutrition(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate nutrition for a meal."""
        try:
            foods = params["foods"]
            total_calories = 0
            total_protein = 0
            total_carbs = 0
            total_fats = 0

            for food_item in foods:
                food_name = food_item["name"]
                quantity = food_item["quantity"]
                unit = food_item.get("unit", "g")

                # Search for food in database
                result = self.supabase.table("foods")\
                    .select("calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g")\
                    .ilike("name", f"%{food_name}%")\
                    .eq("is_public", True)\
                    .limit(1)\
                    .execute()

                if not result.data:
                    continue

                food = result.data[0]

                # Convert to grams (simplified - assumes g)
                grams = quantity if unit == "g" else quantity * 100

                # Calculate nutrition
                multiplier = grams / 100
                total_calories += food["calories_per_100g"] * multiplier
                total_protein += food["protein_g_per_100g"] * multiplier
                total_carbs += food["carbs_g_per_100g"] * multiplier
                total_fats += food["fat_g_per_100g"] * multiplier

            return {
                "total_calories": round(total_calories),
                "total_protein_g": round(total_protein, 1),
                "total_carbs_g": round(total_carbs, 1),
                "total_fats_g": round(total_fats, 1)
            }
        except Exception as e:
            logger.error(f"[ToolService] calculate_meal_nutrition failed: {e}")
            return {"error": str(e)}

    async def _suggest_meal_adjustments(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest meal adjustments to hit targets."""
        try:
            current_meal = params["current_meal"]
            target_macros = params.get("target_macros")

            # Get user's targets if not provided
            if not target_macros:
                profile = await self._get_user_profile(user_id, {})
                target_macros = {
                    "protein": profile.get("daily_protein_goal"),
                    "carbs": profile.get("daily_carbs_goal"),
                    "fats": profile.get("daily_fat_goal")
                }

            # Calculate differences
            protein_diff = target_macros["protein"] - current_meal["protein"]
            carbs_diff = target_macros["carbs"] - current_meal["carbs"]
            fats_diff = target_macros["fats"] - current_meal["fats"]

            suggestions = []

            if protein_diff > 10:
                suggestions.append(f"Add {int(protein_diff)}g more protein (chicken, fish, or protein powder)")
            elif protein_diff < -10:
                suggestions.append(f"Reduce protein by {int(abs(protein_diff))}g")

            if carbs_diff > 20:
                suggestions.append(f"Add {int(carbs_diff)}g more carbs (rice, oats, or fruit)")
            elif carbs_diff < -20:
                suggestions.append(f"Reduce carbs by {int(abs(carbs_diff))}g")

            if fats_diff > 5:
                suggestions.append(f"Add {int(fats_diff)}g more fats (nuts, avocado, or olive oil)")
            elif fats_diff < -5:
                suggestions.append(f"Reduce fats by {int(abs(fats_diff))}g")

            return {
                "suggestions": suggestions if suggestions else ["Meal is well-balanced!"],
                "differences": {
                    "protein_diff": round(protein_diff, 1),
                    "carbs_diff": round(carbs_diff, 1),
                    "fats_diff": round(fats_diff, 1)
                }
            }
        except Exception as e:
            logger.error(f"[ToolService] suggest_meal_adjustments failed: {e}")
            return {"error": str(e)}

    async def _estimate_activity_calories(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate calories burned for activity."""
        try:
            activity_type = params["activity_type"]
            duration_minutes = params["duration_minutes"]
            intensity = params.get("intensity", "moderate")

            # MET values (Metabolic Equivalent of Task)
            MET_VALUES = {
                "running": {"low": 6.0, "moderate": 9.0, "high": 12.0},
                "cycling": {"low": 4.0, "moderate": 7.0, "high": 10.0},
                "swimming": {"low": 5.0, "moderate": 8.0, "high": 11.0},
                "strength_training": {"low": 3.0, "moderate": 5.0, "high": 6.0},
                "walking": {"low": 2.5, "moderate": 3.5, "high": 4.5},
                "yoga": {"low": 2.0, "moderate": 3.0, "high": 4.0}
            }

            # Get MET value
            activity_mets = MET_VALUES.get(activity_type.lower(), {"moderate": 5.0})
            met = activity_mets.get(intensity, 5.0)

            # Get user weight (need for calorie calculation)
            # Simplified: Assume 70kg if not available
            weight_kg = 70  # TODO: Get from user profile/measurements

            # Calculate calories: MET × weight (kg) × duration (hours)
            calories = met * weight_kg * (duration_minutes / 60)

            return {
                "estimated_calories": round(calories),
                "met_value": met,
                "activity_type": activity_type,
                "duration_minutes": duration_minutes,
                "intensity": intensity
            }
        except Exception as e:
            logger.error(f"[ToolService] estimate_activity_calories failed: {e}")
            return {"error": str(e)}


# Singleton
_tool_service: Optional[ToolService] = None

def get_tool_service(supabase_client=None) -> ToolService:
    """Get singleton ToolService instance."""
    global _tool_service
    if _tool_service is None:
        if supabase_client is None:
            from app.services.supabase_service import get_service_client
            supabase_client = get_service_client()
        _tool_service = ToolService(supabase_client)
    return _tool_service
