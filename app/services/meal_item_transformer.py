"""
Meal Item Transformer Service (Enhanced v2.0)

Transforms LLM-extracted food data into proper meal items for database insertion.

Flow:
1. LLM extracts: [{name: "banana", quantity: 2, unit: "pieces", estimated_grams: 240}]
2. This service:
   - Searches for food with user history priority
   - Matches common units to food_servings
   - Handles cooking methods/preparation
   - Returns proper serving-based OR gram-based logging format
3. nutrition_service.create_meal() receives proper format

NEW in v2.0:
- Common units support (pieces, cups, scoops, etc.)
- User history weighting (frequently logged foods ranked higher)
- Cooking method matching (grilled vs fried chicken)
- Smart serving_id matching based on unit type
"""

import structlog
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta

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
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Transform extracted food data to meal items with SMART MATCHING.

        NEW v2.0: Supports common units (pieces, cups, scoops) and user history priority.

        Args:
            foods: List of extracted food data:
            OLD FORMAT: {name: str, quantity_g: float}
            NEW FORMAT: {
                name: str,
                quantity: float,  # Number of units
                unit: str,  # "pieces", "cups", "grams", "scoops", etc.
                estimated_grams: float,
                cooking_method: str (optional)
            }

        Returns:
            Tuple of (meal_items, missing_foods):
            - meal_items: List ready for nutrition_service.create_meal()
            - missing_foods: List of foods not found (for custom food creation)

        The service automatically determines serving-based vs gram-based logging:
        - If unit matches a food_serving → serving-based logging
        - Otherwise → gram-based logging with quantity = grams
        """
        logger.info(f"[MealTransformer] 🔄 Transforming {len(foods)} foods to items (v2.0)")

        items = []
        missing_foods = []

        for idx, food_data in enumerate(foods):
            food_name = food_data.get("name")

            # Support both old and new formats
            quantity = food_data.get("quantity")
            unit = food_data.get("unit", "grams")
            estimated_grams = food_data.get("estimated_grams") or food_data.get("quantity_g", 100)
            cooking_method = food_data.get("cooking_method")

            logger.info(
                f"[MealTransformer] 🔍 Processing: '{food_name}' "
                f"({quantity} {unit}, ~{estimated_grams}g)"
            )

            # STEP 1: Smart search with user history priority
            search_result = await self._smart_search_food(
                food_name=food_name,
                user_id=user_id,
                cooking_method=cooking_method,
                unit=unit
            )

            if not search_result:
                logger.warning(f"[MealTransformer] ❌ Food not found: '{food_name}'")
                missing_foods.append({
                    "name": food_name,
                    "quantity": quantity,
                    "unit": unit,
                    "estimated_grams": estimated_grams,
                    "cooking_method": cooking_method
                })
                continue

            food, match_score, match_reason = search_result
            logger.info(
                f"[MealTransformer] ✅ Found: {food['name']} "
                f"(score: {match_score:.0f}%, reason: {match_reason})"
            )

            # STEP 2: Try to match unit to serving
            serving = None
            if unit and unit not in ["grams", "g"]:
                serving = self._find_matching_serving(food, unit, quantity)

            # STEP 3: Calculate nutrition (serving-based or gram-based)
            if serving:
                # SERVING-BASED LOGGING
                logger.info(
                    f"[MealTransformer] 📦 Using serving: "
                    f"{serving['serving_size']} {serving['serving_unit']}"
                )
                item = self._calculate_serving_based_item(food, serving, quantity)
            else:
                # GRAM-BASED LOGGING (fallback)
                grams = estimated_grams if estimated_grams else 100
                logger.info(f"[MealTransformer] ⚖️ Using gram-based: {grams}g")
                item = self._calculate_gram_based_item(food, grams)

            logger.info(
                f"[MealTransformer] 📊 Calculated: "
                f"{item['calories']}cal, {item['protein_g']}g protein"
            )

            items.append(item)

        logger.info(
            f"[MealTransformer] ✅ Transformed {len(items)} items successfully, "
            f"{len(missing_foods)} not found"
        )
        return items, missing_foods

    async def _smart_search_food(
        self,
        food_name: str,
        user_id: str,
        cooking_method: Optional[str] = None,
        unit: Optional[str] = None
    ) -> Optional[Tuple[Dict[str, Any], float, str]]:
        """
        Smart search with user history priority and cooking method matching.

        Search priority:
        1. User's frequently logged foods (weighted by frequency × recency)
        2. Cooking method match (grilled chicken vs fried chicken)
        3. Exact name match in public foods
        4. Fuzzy match in public foods

        Args:
            food_name: Food name to search for
            user_id: User UUID
            cooking_method: Optional cooking method (e.g., "grilled", "fried")
            unit: Optional unit (helps with scoring)

        Returns:
            Tuple of (food_dict, match_score, match_reason) or None if not found
        """
        logger.info(f"[MealTransformer] 🔍 Smart searching: '{food_name}' (method: {cooking_method})")

        # PRIORITY 1: Check user's frequent foods
        user_history = await self._get_user_food_history(user_id, food_name, limit=5)

        if user_history:
            # Found in user's history - HIGH CONFIDENCE!
            best_match = user_history[0]
            food_id = best_match['food_id']

            # Fetch full food data with servings
            food = await self._get_food_by_id(food_id, user_id)
            if food:
                frequency = best_match.get('log_count', 1)
                logger.info(
                    f"[MealTransformer] 🎯 USER HISTORY MATCH: {food['name']} "
                    f"(logged {frequency}x)"
                )
                return (food, 95.0, f"user_history_{frequency}x")

        # PRIORITY 2 & 3: Search database with cooking method
        search_query = food_name
        if cooking_method:
            search_query = f"{cooking_method} {food_name}"

        try:
            result = self.supabase.rpc(
                'search_foods_safe',
                {
                    'search_query': search_query,
                    'user_id_param': user_id,
                    'result_limit': 5  # Get top 5 matches for scoring
                }
            ).execute()

            if not result.data or len(result.data) == 0:
                # Try without cooking method
                if cooking_method:
                    logger.info(
                        f"[MealTransformer] ⚠️ No match with cooking method, "
                        f"retrying without..."
                    )
                    result = self.supabase.rpc(
                        'search_foods_safe',
                        {
                            'search_query': food_name,
                            'user_id_param': user_id,
                            'result_limit': 5
                        }
                    ).execute()

            if result.data and len(result.data) > 0:
                # Score and rank results
                scored_foods = []

                for food in result.data:
                    # Validate required fields
                    required = ['id', 'name', 'calories_per_100g', 'protein_g_per_100g',
                               'carbs_g_per_100g', 'fat_g_per_100g']
                    if not all(field in food for field in required):
                        continue

                    score, reason = self._score_food_match(
                        food=food,
                        search_name=food_name,
                        cooking_method=cooking_method,
                        unit=unit
                    )

                    scored_foods.append((food, score, reason))

                # Sort by score descending
                scored_foods.sort(key=lambda x: x[1], reverse=True)

                if scored_foods:
                    best = scored_foods[0]
                    # Fetch full data with servings
                    full_food = await self._get_food_by_id(best[0]['id'], user_id)
                    if full_food:
                        return (full_food, best[1], best[2])

            return None

        except Exception as e:
            logger.error(f"[MealTransformer] ❌ Search failed: {e}", exc_info=True)
            return None

    async def _get_user_food_history(
        self,
        user_id: str,
        food_name: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get user's frequently logged foods matching the search term.

        Returns foods ordered by: frequency × recency score

        Args:
            user_id: User UUID
            food_name: Food to search for
            limit: Max results

        Returns:
            List of {food_id, food_name, log_count, last_logged_at, score}
        """
        try:
            # Get user's meal items from last 90 days
            cutoff_date = (datetime.utcnow() - timedelta(days=90)).isoformat()

            query = f"""
                SELECT
                    mi.food_id,
                    f.name as food_name,
                    COUNT(*) as log_count,
                    MAX(m.logged_at) as last_logged_at
                FROM meal_items mi
                JOIN meals m ON mi.meal_id = m.id
                JOIN foods f ON mi.food_id = f.id
                WHERE m.user_id = '{user_id}'
                AND m.logged_at > '{cutoff_date}'
                AND f.name ILIKE '%{food_name}%'
                GROUP BY mi.food_id, f.name
                ORDER BY log_count DESC, last_logged_at DESC
                LIMIT {limit}
            """

            # Note: Using RPC or direct query depending on what's available
            # For now, use a simpler approach with meal_items table
            result = self.supabase.table("meal_items")\
                .select("food_id, foods(name)")\
                .limit(100)\
                .execute()

            if not result.data:
                return []

            # Group by food_id and count
            food_counts = {}
            for item in result.data:
                food_id = item['food_id']
                food_name_db = item.get('foods', {}).get('name', '')

                # Check if food name matches search
                if food_name.lower() in food_name_db.lower():
                    if food_id not in food_counts:
                        food_counts[food_id] = {
                            'food_id': food_id,
                            'food_name': food_name_db,
                            'log_count': 0
                        }
                    food_counts[food_id]['log_count'] += 1

            # Convert to list and sort
            history = sorted(
                food_counts.values(),
                key=lambda x: x['log_count'],
                reverse=True
            )

            return history[:limit]

        except Exception as e:
            logger.error(f"[MealTransformer] ❌ History fetch failed: {e}", exc_info=True)
            return []

    async def _get_food_by_id(
        self,
        food_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get full food data with servings by ID.

        Args:
            food_id: Food UUID
            user_id: User UUID (for access check)

        Returns:
            Food dict with servings, or None if not found
        """
        try:
            result = self.supabase.table("foods")\
                .select("*, food_servings(*)")\
                .eq("id", food_id)\
                .single()\
                .execute()

            if result.data:
                food = result.data
                # Extract servings from nested response
                servings_data = food.pop("food_servings", [])
                food['servings'] = servings_data if servings_data else []
                return food

            return None

        except Exception as e:
            logger.error(f"[MealTransformer] ❌ Food fetch failed: {e}", exc_info=True)
            return None

    def _score_food_match(
        self,
        food: Dict[str, Any],
        search_name: str,
        cooking_method: Optional[str],
        unit: Optional[str]
    ) -> Tuple[float, str]:
        """
        Score how well a food matches the search criteria.

        Scoring factors:
        - Name match quality (exact > contains > fuzzy)
        - Cooking method match (+20 points)
        - Has matching serving unit (+10 points)
        - Verified food (+5 points)
        - Food type (simple > composed for basic ingredients)

        Args:
            food: Food dict from database
            search_name: What user searched for
            cooking_method: Cooking method if specified
            unit: Unit type if specified

        Returns:
            Tuple of (score, reason)
        """
        score = 50.0  # Base score
        reasons = []

        food_name = food.get('name', '').lower()
        search_lower = search_name.lower()

        # Name matching (0-40 points)
        if food_name == search_lower:
            score += 40
            reasons.append("exact_match")
        elif search_lower in food_name:
            score += 30
            reasons.append("name_contains")
        elif any(word in food_name for word in search_lower.split()):
            score += 20
            reasons.append("word_match")
        else:
            score += 10
            reasons.append("fuzzy")

        # Cooking method matching (+20 points)
        if cooking_method:
            if cooking_method.lower() in food_name:
                score += 20
                reasons.append(f"method_{cooking_method}")

        # Has matching serving unit (+10 points)
        if unit and unit not in ["grams", "g"]:
            servings = food.get('servings', [])
            unit_variants = self._get_unit_variants(unit)

            for serving in servings:
                serving_unit = serving.get('serving_unit', '').lower()
                if serving_unit in unit_variants:
                    score += 10
                    reasons.append(f"has_{unit}")
                    break

        # Verified food (+5 points)
        if food.get('verified'):
            score += 5
            reasons.append("verified")

        # Food type preference
        food_type = food.get('food_type', '')
        if food_type == 'simple':
            score += 5
            reasons.append("simple_food")

        reason_str = ",".join(reasons)
        return (score, reason_str)

    def _get_unit_variants(self, unit: str) -> List[str]:
        """
        Get all possible variants of a unit name.

        Args:
            unit: Unit name (e.g., "pieces", "cups")

        Returns:
            List of variants to check
        """
        unit_lower = unit.lower()

        variants_map = {
            "pieces": ["piece", "pieces", "pc", "pcs", "unit", "units"],
            "piece": ["piece", "pieces", "pc", "pcs", "unit", "units"],
            "cups": ["cup", "cups", "c"],
            "cup": ["cup", "cups", "c"],
            "scoops": ["scoop", "scoops", "serving", "servings"],
            "scoop": ["scoop", "scoops", "serving", "servings"],
            "tablespoons": ["tablespoon", "tablespoons", "tbsp", "T"],
            "tbsp": ["tablespoon", "tablespoons", "tbsp", "T"],
            "teaspoons": ["teaspoon", "teaspoons", "tsp", "t"],
            "tsp": ["teaspoon", "teaspoons", "tsp", "t"],
            "slices": ["slice", "slices"],
            "slice": ["slice", "slices"],
            "servings": ["serving", "servings", "portion", "portions"],
            "serving": ["serving", "servings", "portion", "portions"],
        }

        # Try exact match first
        if unit_lower in variants_map:
            return variants_map[unit_lower]

        # Try to find in values
        for key, variants in variants_map.items():
            if unit_lower in variants:
                return variants

        # Default: return as-is
        return [unit_lower]

    def _find_matching_serving(
        self,
        food: Dict[str, Any],
        unit: str,
        quantity: float
    ) -> Optional[Dict[str, Any]]:
        """
        Find a food serving that matches the requested unit.

        Args:
            food: Food dict with servings
            unit: Unit type (e.g., "pieces", "cups", "scoops")
            quantity: Quantity (for validation)

        Returns:
            Matching serving dict or None if not found
        """
        servings = food.get('servings', [])

        if not servings:
            return None

        unit_variants = self._get_unit_variants(unit)

        # Try to find exact match
        for serving in servings:
            serving_unit = serving.get('serving_unit', '').lower()

            if serving_unit in unit_variants:
                logger.info(
                    f"[MealTransformer] ✅ Matched serving: "
                    f"{serving['serving_size']} {serving['serving_unit']} = "
                    f"{serving['grams_per_serving']}g"
                )
                return serving

        # No match found
        logger.info(f"[MealTransformer] ⚠️ No serving found for unit '{unit}'")
        return None

    def _calculate_serving_based_item(
        self,
        food: Dict[str, Any],
        serving: Dict[str, Any],
        quantity: float
    ) -> Dict[str, Any]:
        """
        Calculate nutrition for serving-based logging.

        CRITICAL: This creates serving-based format where:
        - quantity = number of servings (e.g., 2 for "2 bananas")
        - serving_id = UUID of the serving
        - grams = quantity × serving.grams_per_serving

        Backend will recalculate nutrition from grams.

        Args:
            food: Food dict from database
            serving: Matched serving dict
            quantity: Number of servings

        Returns:
            Meal item dict for serving-based logging
        """
        # Calculate grams from serving size
        grams = float(quantity) * float(serving['grams_per_serving'])

        # Calculate nutrition from per_100g values
        multiplier = Decimal(str(grams)) / Decimal("100")

        calories = float(Decimal(str(food['calories_per_100g'])) * multiplier)
        protein_g = float(Decimal(str(food['protein_g_per_100g'])) * multiplier)
        carbs_g = float(Decimal(str(food['carbs_g_per_100g'])) * multiplier)
        fat_g = float(Decimal(str(food['fat_g_per_100g'])) * multiplier)

        # Round for display
        calories_rounded = round(calories)
        protein_g_rounded = round(protein_g, 1)
        carbs_g_rounded = round(carbs_g, 1)
        fat_g_rounded = round(fat_g, 1)

        # Build display label
        display_label = None
        if serving.get('serving_label'):
            display_label = f"{quantity:.0f} {serving['serving_label']}"
        else:
            unit_name = serving.get('serving_unit', 'serving')
            display_label = f"{quantity:.0f} {unit_name}{'s' if quantity != 1 else ''}"

        return {
            "food_id": food['id'],
            "quantity": float(quantity),  # Number of servings
            "serving_id": serving['id'],  # Serving UUID
            "grams": grams,
            "calories": calories_rounded,
            "protein_g": protein_g_rounded,
            "carbs_g": carbs_g_rounded,
            "fat_g": fat_g_rounded,
            "display_unit": serving.get('serving_unit', 'serving'),
            "display_label": display_label
        }

    def _calculate_gram_based_item(
        self,
        food: Dict[str, Any],
        grams: float
    ) -> Dict[str, Any]:
        """
        Calculate nutrition for gram-based logging.

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
