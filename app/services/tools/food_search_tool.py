"""
Food Search Tool

Smart food database search with ranking and personalization.

Search Strategy:
1. User's quick_meals (personalized shortcuts) - HIGHEST PRIORITY
2. Exact matches in foods table
3. Partial matches with relevance scoring
4. Prioritize by composition_type (simple > composed > branded)

Responsibilities:
- Search both quick_meals and foods tables
- Calculate relevance scores for ranking
- Deduplicate results
- Cache results for 30 minutes

Usage:
    tool = FoodSearchTool(supabase, cache)
    results = await tool.execute(user_id, {
        "query": "chicken",
        "limit": 5
    })
"""

from typing import Dict, Any, List, Optional
from app.services.tools.base_tool import BaseTool
import structlog

logger = structlog.get_logger()


class FoodSearchTool(BaseTool):
    """Smart food database search with relevance ranking."""

    def get_definition(self) -> Dict[str, Any]:
        """
        Get tool definition for LLM.

        Returns:
            Tool definition dict
        """
        return {
            "name": "search_food_database",
            "description": (
                "Search the food database for foods by name or brand. "
                "Returns ranked results with nutrition per 100g. "
                "Prioritizes user's saved quick meals, then exact matches, then partial matches. "
                "Simple ingredients (chicken, rice) are ranked higher than branded products."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (food name or brand)"
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of results (default: 5, max: 10)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }

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
        - Brand match: +15
        - composition_type='simple': +10
        - composition_type='composed': +5
        - composition_type='branded': +0

        Args:
            query: Search query
            food_name: Food name
            brand_name: Brand name (optional)
            composition_type: Food type (simple/composed/branded)

        Returns:
            Relevance score (higher is better)
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
        # Simple ingredients (chicken, rice) prioritized for basic searches
        if composition_type == "simple":
            score += 10
        elif composition_type == "composed":
            score += 5
        # branded gets +0 (lowest priority unless exact match)

        return score

    async def execute(self, user_id: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search food database with smart ranking.

        Args:
            user_id: User UUID
            params: {
                "query": "chicken breast",
                "limit": 5
            }

        Returns:
            [
                {
                    "source": "foods_database",
                    "name": "Chicken breast, grilled",
                    "brand": "Generic",
                    "composition_type": "simple",
                    "per_100g": {
                        "calories": 165,
                        "protein": 31.0,
                        "carbs": 0.0,
                        "fats": 3.6
                    },
                    "serving_size": {
                        "grams": 100,
                        "description": "1 breast"
                    }
                }
            ]
        """
        try:
            query = params.get("query", "").lower().strip()
            limit = min(params.get("limit", 5), 10)  # Max 10 results

            if not query:
                return []

            # Check cache first (30min TTL)
            cache_key = f"food_search:{user_id or 'public'}:{query}:{limit}"
            cached_result = await self.get_from_cache(cache_key)
            if cached_result:
                logger.debug(
                    "food_search_cache_hit",
                    user_id=user_id,
                    query=query
                )
                return cached_result

            results = []
            seen_names = set()  # Deduplicate

            # STEP 1: Search user's quick_meals (HIGHEST PRIORITY)
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
                            await self.cache_result(cache_key, results, ttl=1800)
                            return results

                except Exception as e:
                    logger.warning(
                        "quick_meals_search_failed",
                        user_id=user_id,
                        error=str(e)
                    )

            # STEP 2: Search public foods table
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
                return results  # Return quick meals only (if any)

            # STEP 3: Rank and sort results
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

            # STEP 4: Format and return results
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

            # Cache results for 30 minutes
            await self.cache_result(cache_key, results, ttl=1800)

            logger.info(
                "food_search_completed",
                user_id=user_id,
                query=query,
                results_count=len(results)
            )

            return results

        except Exception as e:
            logger.error(
                "food_search_failed",
                user_id=user_id,
                query=params.get("query"),
                error=str(e),
                exc_info=True
            )
            return []
