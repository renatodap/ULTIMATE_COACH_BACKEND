"""
Nutrition Service (Refactored v2.1)

Handles business logic for foods, food servings, meals, and meal items.
Uses Supabase client consistently for all database operations.

Changes in v2.1:
- Added structured error codes for i18n support
- Fixed N+1 query issue in create_meal (now batches food fetching)
- Improved error messages with detailed context
"""

import structlog
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict
from uuid import UUID

from app.services.supabase_service import supabase_service
from app.models.nutrition import (
    Food,
    FoodServing,
    Meal,
    MealItem,
    MealItemBase,
    NutritionStats,
)
from app.models.errors import (
    SearchQueryTooShortError,
    SearchFailedError,
    FoodNotFoundError,
    InvalidServingError,
    ServingMismatchError,
    MealEmptyError,
    MealCreationFailedError,
    InvalidGramsPerServingError,
    CustomFoodCreationFailedError,
)

logger = structlog.get_logger()


class NutritionService:
    """Service for nutrition-related operations."""

    # =====================================================
    # Foods
    # =====================================================

    async def search_foods(
        self,
        query: str,
        limit: int = 20,
        user_id: Optional[UUID] = None,
    ) -> List[Food]:
        """
        Search foods by name using Supabase RPC function.

        Returns public foods + user's custom foods.
        Minimum 2 characters required.

        Uses PostgreSQL RPC function to bypass PostgREST worker crashes.
        Falls back to direct table query if RPC is unavailable.

        Raises:
            SearchQueryTooShortError: If query < 2 characters
            SearchFailedError: If database query fails
        """
        if len(query) < 2:
            raise SearchQueryTooShortError(query)

        try:
            # ===================================================================
            # PRIMARY METHOD: Use RPC function (bypasses PostgREST crashes)
            # ===================================================================
            try:
                logger.info(
                    "search_foods_rpc_starting",
                    query=query,
                    limit=limit,
                    user_id=str(user_id) if user_id else None,
                    method="rpc_search_foods_safe"
                )

                # Call PostgreSQL RPC function
                rpc_response = supabase_service.client.rpc(
                    "search_foods_safe",
                    {
                        "search_query": query,
                        "result_limit": limit,
                        "user_id_filter": str(user_id) if user_id else None
                    }
                ).execute()

                # Handle different RPC response formats
                # Supabase can return: {"foods": [...]} or [{"foods": [...]}]
                response_data = rpc_response.data

                # If response is a list, unwrap first element
                if isinstance(response_data, list) and len(response_data) > 0:
                    response_data = response_data[0]

                logger.info(
                    "search_foods_rpc_response",
                    query=query,
                    response_type=type(response_data).__name__,
                    is_dict=isinstance(response_data, dict),
                    has_foods_key="foods" in response_data if isinstance(response_data, dict) else False,
                    method="rpc_search_foods_safe"
                )

                # Check if RPC returned an error
                if response_data and isinstance(response_data, dict):
                    if "error" in response_data:
                        logger.warning(
                            "search_foods_rpc_error",
                            query=query,
                            error=response_data.get("error"),
                            fallback="using_table_query"
                        )
                        # Fall through to fallback method
                        raise Exception(f"RPC error: {response_data.get('error')}")

                    # Success! Parse RPC response
                    foods_data = response_data.get("foods", [])

                    logger.info(
                        "search_foods_rpc_success",
                        query=query,
                        results_count=len(foods_data),
                        servings_sample=len(foods_data[0].get("servings", [])) if foods_data else 0,
                        method="rpc_search_foods_safe"
                    )

                    # Convert RPC response to Food objects
                    foods = []
                    for food_dict in foods_data:
                        servings_data = food_dict.pop("servings", [])
                        food = Food(**food_dict)
                        food.servings = [FoodServing(**s) for s in servings_data]
                        foods.append(food)

                    logger.info(
                        "search_foods_rpc_parsed",
                        query=query,
                        foods_count=len(foods),
                        first_food_servings=len(foods[0].servings) if foods else 0
                    )

                    return foods[:limit]

            except Exception as rpc_error:
                # RPC failed, fall back to direct table query
                logger.warning(
                    "search_foods_rpc_failed",
                    query=query,
                    error=str(rpc_error),
                    fallback="using_table_query"
                )

            # ===================================================================
            # FALLBACK METHOD: Direct table query (original method)
            # ===================================================================
            # Search public foods
            try:
                # Enhanced logging for diagnostics
                logger.info(
                    "search_foods_query_starting",
                    query=query,
                    limit=limit,
                    user_id=str(user_id) if user_id else None,
                    has_user_id=user_id is not None,
                    method="table_query_fallback"
                )

                public_query = (
                    supabase_service.client.table("foods")
                    .select("*, food_servings(*)")
                    .eq("is_public", True)
                    .ilike("name", f"%{query}%")
                    .order("usage_count", desc=True)
                    .order("verified", desc=True)
                    .limit(limit)
                )

                public_response = public_query.execute()

                # Enhanced logging for diagnostics
                logger.info(
                    "search_foods_query_completed",
                    query=query,
                    results_count=len(public_response.data),
                    has_servings=any(row.get("food_servings") for row in public_response.data) if public_response.data else False,
                    sample_results=[{
                        "id": row.get("id"),
                        "name": row.get("name"),
                        "is_public": row.get("is_public"),
                        "verified": row.get("verified"),
                        "servings_count": len(row.get("food_servings", []))
                    } for row in public_response.data[:3]] if public_response.data else []
                )
            except Exception as nested_error:
                # Fallback: PostgREST "JSON could not be generated" error (code 5)
                # This happens when there's corrupted JSONB data in foods table
                logger.warning(
                    "search_foods_nested_query_failed",
                    query=query,
                    error=str(nested_error),
                    fallback="fetching_foods_without_jsonb"
                )

                # Even more aggressive fallback - exclude JSONB columns that might be corrupted
                # Only select non-JSONB columns to avoid serialization errors
                try:
                    public_query = (
                        supabase_service.client.table("foods")
                        .select("id, name, brand_name, food_type, composition_type, "
                               "calories_per_100g, protein_g_per_100g, carbs_g_per_100g, "
                               "fat_g_per_100g, fiber_g_per_100g, "
                               "is_public, verified, usage_count, created_by, created_at, updated_at")
                        .eq("is_public", True)
                        .ilike("name", f"%{query}%")
                        .order("usage_count", desc=True)
                        .order("verified", desc=True)
                        .limit(limit)
                    )

                    public_response = public_query.execute()
                except Exception as final_error:
                    # If even this fails, return empty list
                    logger.error(
                        "search_foods_all_fallbacks_failed",
                        query=query,
                        error=str(final_error)
                    )
                    return []

            foods = []

            # Add public foods
            for row in public_response.data:
                servings_data = row.pop("food_servings", [])
                food = Food(**row)

                # If we didn't get servings in the query, fetch them separately
                if not servings_data and food.id:
                    try:
                        servings_response = (
                            supabase_service.client.table("food_servings")
                            .select("*")
                            .eq("food_id", str(food.id))
                            .execute()
                        )
                        servings_data = servings_response.data
                    except Exception:
                        # Skip servings if fetch fails
                        pass

                food.servings = [FoodServing(**s) for s in servings_data]
                foods.append(food)

            # Search user's custom foods if user_id provided
            if user_id:
                try:
                    custom_query = (
                        supabase_service.client.table("foods")
                        .select("*, food_servings(*)")
                        .eq("created_by", str(user_id))
                        .ilike("name", f"%{query}%")
                        .limit(limit)
                    )

                    custom_response = custom_query.execute()
                except Exception as nested_error:
                    # Fallback: Same as above for custom foods
                    logger.warning(
                        "search_custom_foods_nested_query_failed",
                        query=query,
                        user_id=str(user_id),
                        error=str(nested_error),
                        fallback="fetching_foods_without_jsonb"
                    )

                    try:
                        custom_query = (
                            supabase_service.client.table("foods")
                            .select("id, name, brand_name, food_type, composition_type, "
                                   "calories_per_100g, protein_g_per_100g, carbs_g_per_100g, "
                                   "fat_g_per_100g, fiber_g_per_100g, "
                                   "is_public, verified, usage_count, created_by, created_at, updated_at")
                            .eq("created_by", str(user_id))
                            .ilike("name", f"%{query}%")
                            .limit(limit)
                        )

                        custom_response = custom_query.execute()
                    except Exception as final_error:
                        # If even this fails, skip custom foods
                        logger.error(
                            "search_custom_foods_all_fallbacks_failed",
                            query=query,
                            user_id=str(user_id),
                            error=str(final_error)
                        )
                        custom_response = type('obj', (object,), {'data': []})()  # Empty response

                for row in custom_response.data:
                    servings_data = row.pop("food_servings", [])
                    food = Food(**row)

                    # If we didn't get servings in the query, fetch them separately
                    if not servings_data and food.id:
                        try:
                            servings_response = (
                                supabase_service.client.table("food_servings")
                                .select("*")
                                .eq("food_id", str(food.id))
                                .execute()
                            )
                            servings_data = servings_response.data
                        except Exception:
                            # Skip servings if fetch fails
                            pass

                    food.servings = [FoodServing(**s) for s in servings_data]
                    foods.append(food)

            return foods[:limit]  # Limit total results

        except SearchQueryTooShortError:
            raise
        except Exception as e:
            logger.error("search_foods_error", query=query, error=str(e))
            raise SearchFailedError(query, original_error=str(e))

    async def get_food(
        self,
        food_id: UUID,
        user_id: Optional[UUID] = None,
    ) -> Optional[Food]:
        """
        Get a single food by ID with servings.

        Returns None if not found or user doesn't have access.
        """
        try:
            # Get food
            query = (
                supabase_service.client.table("foods")
                .select("*, food_servings(*)")
                .eq("id", str(food_id))
                .single()
            )

            response = query.execute()

            if not response.data:
                return None

            # Check access
            food_data = response.data
            if not food_data["is_public"] and food_data.get("created_by") != str(user_id):
                return None

            # Build food object
            servings_data = food_data.pop("food_servings", [])
            food = Food(**food_data)
            food.servings = [FoodServing(**s) for s in servings_data]

            return food

        except Exception as e:
            logger.error("get_food_error", food_id=str(food_id), error=str(e))
            return None

    async def get_food_servings(
        self,
        food_id: UUID,
        user_id: Optional[UUID] = None,
    ) -> List[FoodServing]:
        """Get all serving sizes for a food."""
        try:
            # Verify food access first
            food = await self.get_food(food_id, user_id)
            if not food:
                return []

            return food.servings

        except Exception as e:
            logger.error("get_food_servings_error", food_id=str(food_id), error=str(e))
            return []

    async def get_recent_foods(
        self,
        user_id: UUID,
        limit: int = 10,
    ) -> List[Food]:
        """
        Get recently logged foods for a user.

        Returns foods the user has logged in meals, ordered by most recent.
        Deduplicates by food_id.

        Uses safe two-query approach to avoid complex join syntax.
        """
        try:
            # Step 1: Get user's recent meal IDs
            meals_response = (
                supabase_service.client.table("meals")
                .select("id")
                .eq("user_id", str(user_id))
                .order("logged_at", desc=True)
                .limit(50)  # Get last 50 meals
                .execute()
            )

            if not meals_response.data:
                return []

            meal_ids = [meal["id"] for meal in meals_response.data]

            # Step 2: Get meal items for those meals, ordered by recency
            meal_items_response = (
                supabase_service.client.table("meal_items")
                .select("food_id")
                .in_("meal_id", meal_ids)
                .order("created_at", desc=True)
                .limit(limit * 3)  # Get more to account for duplicates
                .execute()
            )

            if not meal_items_response.data:
                return []

            # Step 3: Extract unique food IDs (preserving order)
            seen_food_ids = set()
            unique_food_ids = []
            for item in meal_items_response.data:
                food_id = item["food_id"]
                if food_id not in seen_food_ids:
                    seen_food_ids.add(food_id)
                    unique_food_ids.append(food_id)
                    if len(unique_food_ids) >= limit:
                        break

            if not unique_food_ids:
                return []

            # Step 4: Fetch full food data with servings
            foods_response = (
                supabase_service.client.table("foods")
                .select("*, food_servings(*)")
                .in_("id", unique_food_ids)
                .execute()
            )

            # Step 5: Build foods map
            foods_map = {}
            for row in foods_response.data:
                servings_data = row.pop("food_servings", [])
                food = Food(**row)
                food.servings = [FoodServing(**s) for s in servings_data]
                foods_map[row["id"]] = food

            # Step 6: Return in order of recency (preserving unique_food_ids order)
            recent_foods = []
            for food_id in unique_food_ids:
                if food_id in foods_map:
                    recent_foods.append(foods_map[food_id])

            logger.info(
                "recent_foods_retrieved",
                user_id=str(user_id),
                count=len(recent_foods),
            )

            return recent_foods

        except Exception as e:
            logger.error("get_recent_foods_error", user_id=str(user_id), error=str(e))
            return []

    async def create_custom_food(
        self,
        user_id: UUID,
        name: str,
        brand_name: Optional[str],
        serving_size: Decimal,
        serving_unit: str,
        grams_per_serving: Decimal,  # ← NOW REQUIRED!
        calories: Decimal,
        protein_g: Decimal,
        carbs_g: Decimal,
        fat_g: Decimal,
        fiber_g: Optional[Decimal] = None,
    ) -> Food:
        """
        Create a custom food with a single serving size.

        Takes nutrition for the user's serving and converts to per-100g.
        FIXED: Now requires grams_per_serving (no more bad estimation).
        """
        # Validate grams_per_serving
        if grams_per_serving <= 0:
            raise InvalidGramsPerServingError(float(grams_per_serving))

        # Convert nutrition to per-100g (CORRECT formula)
        calories_per_100g = (calories / grams_per_serving) * Decimal("100")
        protein_per_100g = (protein_g / grams_per_serving) * Decimal("100")
        carbs_per_100g = (carbs_g / grams_per_serving) * Decimal("100")
        fat_per_100g = (fat_g / grams_per_serving) * Decimal("100")
        fiber_per_100g = (
            (fiber_g / grams_per_serving) * Decimal("100") if fiber_g else None
        )

        try:
            # Insert food
            food_data = {
                "name": name,
                "brand_name": brand_name,
                "calories_per_100g": float(calories_per_100g),
                "protein_g_per_100g": float(protein_per_100g),
                "carbs_g_per_100g": float(carbs_per_100g),
                "fat_g_per_100g": float(fat_per_100g),
                "fiber_g_per_100g": float(fiber_per_100g) if fiber_per_100g else None,
                "food_type": "dish",
                "is_public": False,
                "created_by": str(user_id),
            }

            food_response = (
                supabase_service.client.table("foods")
                .insert(food_data)
                .execute()
            )

            if not food_response.data:
                raise CustomFoodCreationFailedError(name, "Database insert returned no data")

            food_row = food_response.data[0]
            food_id = food_row["id"]

            # Insert serving
            serving_data = {
                "food_id": food_id,
                "serving_size": float(serving_size),
                "serving_unit": serving_unit,
                "grams_per_serving": float(grams_per_serving),
                "is_default": True,
                "display_order": 0,
            }

            serving_response = (
                supabase_service.client.table("food_servings")
                .insert(serving_data)
                .execute()
            )

            if not serving_response.data:
                raise CustomFoodCreationFailedError(name, "Failed to create serving size")

            # Build food object
            food = Food(**food_row)
            food.servings = [FoodServing(**serving_response.data[0])]

            logger.info(
                "custom_food_created",
                food_id=food_id,
                name=name,
                user_id=str(user_id),
            )

            return food

        except (InvalidGramsPerServingError, CustomFoodCreationFailedError):
            raise
        except Exception as e:
            logger.error("create_custom_food_error", name=name, error=str(e))
            raise CustomFoodCreationFailedError(name, str(e))

    # =====================================================
    # Meals
    # =====================================================

    async def create_meal(
        self,
        user_id: UUID,
        name: Optional[str],
        meal_type: str,
        logged_at: Optional[datetime],
        notes: Optional[str],
        items: List[MealItemBase],
        source: str = "manual",
        ai_confidence: Optional[Decimal] = None,
    ) -> Meal:
        """
        Create a meal with items.

        Supports two logging methods:
        - GRAM-BASED: serving_id = None, quantity = grams (e.g., 100 = 100g)
        - SERVING-BASED: serving_id = UUID, quantity = serving count (e.g., 2 = 2 scoops)

        CRITICAL: Backend ALWAYS recalculates grams and nutrition from quantity + serving/food.
        Does NOT trust frontend's pre-calculated values (single source of truth).

        QUANTITY SEMANTIC OVERLOAD:
        - If serving_id is None → quantity = grams directly
        - If serving_id present → quantity = serving count (multiplied by grams_per_serving)

        VALIDATION LAYERS:
        - Serving count: max 50 (hard reject), warn if >10
        - Gram amount: max 10,000g (10kg) per item
        - Serving ownership: serving_id must belong to food_id

        PERFORMANCE: Batches all food fetches in a single query (fixes N+1 issue).

        See: NUTRITION_LOGGING_ARCHITECTURE.md for complete documentation

        Raises:
            MealEmptyError: If items list is empty
            FoodNotFoundError: If any food_id is not found or inaccessible
            InvalidServingError: If serving_id is provided but not found
            ServingMismatchError: If serving doesn't belong to food
            MealCreationFailedError: If database operations fail
        """
        if not items:
            raise MealEmptyError()

        if not logged_at:
            logged_at = datetime.utcnow()

        try:
            # === FIX N+1 QUERY: Batch fetch all foods at once ===
            food_ids = list(set(item.food_id for item in items))  # Deduplicate

            # Single query for all foods
            foods_query = (
                supabase_service.client.table("foods")
                .select("*, food_servings(*)")
                .in_("id", [str(fid) for fid in food_ids])
                .execute()
            )

            # Build foods map for O(1) lookup
            foods_map: Dict[UUID, Food] = {}
            for row in foods_query.data:
                servings_data = row.pop("food_servings", [])
                food = Food(**row)
                food.servings = [FoodServing(**s) for s in servings_data]

                # Check user access
                if not food.is_public and food.created_by != user_id:
                    continue  # Skip inaccessible foods

                foods_map[food.id] = food  # food.id is already UUID
            # === End N+1 fix ===

            # Validate and calculate totals
            total_calories = Decimal("0")
            total_protein = Decimal("0")
            total_carbs = Decimal("0")
            total_fat = Decimal("0")

            validated_items = []

            for idx, item in enumerate(items):
                # Get food from map (O(1) lookup, not O(n) query!)
                food = foods_map.get(item.food_id)
                if not food:
                    raise FoodNotFoundError(str(item.food_id))

                # Determine if gram-based or serving-based logging
                if item.serving_id is None:
                    # ======================================================
                    # GRAM-BASED LOGGING
                    # ======================================================
                    # quantity represents grams directly (e.g., 100 = 100g)
                    # Frontend sends: quantity=150, serving_id=null
                    # We interpret: user logged 150 grams
                    # ======================================================
                    grams = item.quantity
                    serving = None

                    # Validate reasonable gram amounts (max 10kg = 10,000g per item)
                    if grams > 10000:
                        raise ValueError(
                            f"Unreasonable quantity: {grams}g for {food.name}. "
                            f"Maximum allowed is 10,000g (10kg) per item."
                        )
                else:
                    # ======================================================
                    # SERVING-BASED LOGGING
                    # ======================================================
                    # quantity represents serving count (e.g., 2 = 2 servings)
                    # Frontend sends: quantity=2, serving_id="uuid"
                    # We interpret: user logged 2 servings
                    # We calculate: grams = 2 × serving.grams_per_serving
                    # ======================================================
                    serving = next(
                        (s for s in food.servings if s.id == item.serving_id), None
                    )
                    if not serving:
                        raise InvalidServingError(str(item.serving_id), str(item.food_id))

                    # Validate serving belongs to food
                    if serving.food_id != item.food_id:
                        raise ServingMismatchError(
                            str(item.serving_id),
                            str(item.food_id),
                            str(serving.food_id),
                        )

                    # ======================================================
                    # VALIDATION LAYER 4: Backend Hard Limit (50 servings)
                    # ======================================================
                    # CRITICAL: Prevents "100 banana" bug from reaching database
                    # Frontend has 3 layers (HTML max=20, warning >10, visual warning)
                    # This is the final safety net
                    # See: NUTRITION_LOGGING_ARCHITECTURE.md - Validation Requirements
                    # ======================================================
                    if item.quantity > 50:
                        raise ValueError(
                            f"Unreasonable quantity: {item.quantity} servings of {food.name}. "
                            f"Maximum allowed is 50 servings per item. "
                            f"Did you mean to log in grams instead?"
                        )

                    # ======================================================
                    # MONITORING: Log suspicious quantities (>10 servings)
                    # ======================================================
                    # This doesn't block the request, but alerts monitoring
                    # Helps detect patterns (e.g., consistent >10 serving logs)
                    # ======================================================
                    if item.quantity > 10:
                        logger.warning(
                            "suspicious_serving_quantity",
                            food_name=food.name,
                            quantity=float(item.quantity),
                            serving_unit=serving.serving_unit,
                            total_grams=float(item.quantity * serving.grams_per_serving),
                            user_id=str(user_id)
                        )

                    # Calculate grams from serving count
                    # Example: 2 servings × 118g/serving = 236g
                    grams = item.quantity * serving.grams_per_serving

                # ======================================================
                # AUTHORITATIVE CALCULATION (Single Source of Truth)
                # ======================================================
                # ALWAYS calculate nutrition from grams - DON'T TRUST FRONTEND
                # Frontend values are for preview only, backend recalculates everything
                #
                # All foods store nutrition as per_100g in database
                # Formula: (grams / 100) × per_100g_value
                #
                # Example: 236g banana with 89 cal/100g
                #   multiplier = 236 / 100 = 2.36
                #   calories = 89 × 2.36 = 210
                #
                # See: NUTRITION_LOGGING_ARCHITECTURE.md - Frontend/Backend Contract
                # ======================================================
                multiplier = grams / Decimal("100")
                item_calories = food.calories_per_100g * multiplier
                item_protein = food.protein_g_per_100g * multiplier
                item_carbs = food.carbs_g_per_100g * multiplier
                item_fat = food.fat_g_per_100g * multiplier

                total_calories += item_calories
                total_protein += item_protein
                total_carbs += item_carbs
                total_fat += item_fat

                validated_items.append(
                    {
                        "food": food,
                        "serving": serving,  # Can be None for gram-based logging
                        "quantity": item.quantity,
                        "grams": grams,
                        "calories": item_calories,
                        "protein_g": item_protein,
                        "carbs_g": item_carbs,
                        "fat_g": item_fat,
                        "display_order": idx,
                    }
                )

            # Create meal
            meal_data = {
                "user_id": str(user_id),
                "name": name,
                "meal_type": meal_type,
                "logged_at": logged_at.isoformat(),
                "notes": notes,
                "total_calories": float(total_calories),
                "total_protein_g": float(total_protein),
                "total_carbs_g": float(total_carbs),
                "total_fat_g": float(total_fat),
                "source": source,
                "ai_confidence": float(ai_confidence) if ai_confidence else None,
            }

            meal_response = (
                supabase_service.client.table("meals").insert(meal_data).execute()
            )

            if not meal_response.data:
                raise MealCreationFailedError("Database insert returned no data")

            meal_row = meal_response.data[0]
            meal_id = meal_row["id"]

            # Create meal items
            meal_items_data = []
            for validated in validated_items:
                # Handle gram-based logging (serving can be None)
                serving = validated["serving"]

                meal_items_data.append(
                    {
                        "meal_id": meal_id,
                        "food_id": str(validated["food"].id),
                        "quantity": float(validated["quantity"]),
                        "serving_id": str(serving.id) if serving else None,
                        "grams": float(validated["grams"]),
                        "calories": float(validated["calories"]),
                        "protein_g": float(validated["protein_g"]),
                        "carbs_g": float(validated["carbs_g"]),
                        "fat_g": float(validated["fat_g"]),
                        "display_unit": serving.serving_unit if serving else "g",
                        "display_label": serving.serving_label if serving else None,
                        "display_order": validated["display_order"],
                    }
                )

            items_response = (
                supabase_service.client.table("meal_items")
                .insert(meal_items_data)
                .execute()
            )

            if not items_response.data:
                raise MealCreationFailedError("Failed to create meal items")

            # Build meal object
            meal = Meal(**meal_row)
            meal.items = [MealItem(**item) for item in items_response.data]

            logger.info(
                "meal_created",
                meal_id=meal_id,
                meal_type=meal_type,
                items_count=len(meal.items),
                calories=float(total_calories),
                user_id=str(user_id),
            )

            return meal

        except (MealEmptyError, FoodNotFoundError, InvalidServingError, ServingMismatchError, MealCreationFailedError):
            raise
        except Exception as e:
            logger.error("create_meal_error", user_id=str(user_id), error=str(e))
            raise MealCreationFailedError(str(e))

    async def get_user_meals(
        self,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Meal]:
        """Get user's meals with optional date filtering."""
        try:
            # DEBUG: Log query construction
            logger.info(
                "get_user_meals_query_building",
                user_id=str(user_id),
                start_date=start_date.isoformat() if start_date else None,
                end_date=end_date.isoformat() if end_date else None,
                limit=limit,
                offset=offset
            )

            query = (
                supabase_service.client.table("meals")
                .select("*, meal_items(*, foods(name, brand_name))")
                .eq("user_id", str(user_id))
                .order("logged_at", desc=True)
                .limit(limit)
                .offset(offset)
            )

            if start_date:
                query = query.gte("logged_at", start_date.isoformat())
            if end_date:
                query = query.lt("logged_at", end_date.isoformat())

            response = query.execute()

            # DEBUG: Log raw response
            logger.info(
                "get_user_meals_raw_response",
                user_id=str(user_id),
                rows_returned=len(response.data),
                sample_row=response.data[0] if response.data else None
            )

            meals = []
            for row in response.data:
                items_data = row.pop("meal_items", [])
                meal = Meal(**row)
                meal.items = [MealItem(**item) for item in items_data]
                meals.append(meal)

            # DEBUG: Log processed meals
            logger.info(
                "get_user_meals_processed",
                user_id=str(user_id),
                meals_count=len(meals),
                meals_sample=[{
                    "id": str(m.id),
                    "logged_at": m.logged_at.isoformat() if m.logged_at else None,
                    "meal_type": m.meal_type
                } for m in meals[:3]]
            )

            return meals

        except Exception as e:
            logger.error("get_user_meals_error", user_id=str(user_id), error=str(e), exc_info=True)
            return []

    async def get_meal(self, meal_id: UUID, user_id: UUID) -> Optional[Meal]:
        """Get a single meal by ID."""
        try:
            response = (
                supabase_service.client.table("meals")
                .select("*, meal_items(*, foods(name, brand_name))")
                .eq("id", str(meal_id))
                .eq("user_id", str(user_id))
                .single()
                .execute()
            )

            if not response.data:
                return None

            row = response.data
            items_data = row.pop("meal_items", [])
            meal = Meal(**row)
            meal.items = [MealItem(**item) for item in items_data]

            return meal

        except Exception as e:
            logger.error("get_meal_error", meal_id=str(meal_id), error=str(e))
            return None

    async def delete_meal(self, meal_id: UUID, user_id: UUID) -> bool:
        """Delete a meal. Returns True if deleted, False if not found."""
        try:
            response = (
                supabase_service.client.table("meals")
                .delete()
                .eq("id", str(meal_id))
                .eq("user_id", str(user_id))
                .execute()
            )

            return len(response.data) > 0

        except Exception as e:
            logger.error("delete_meal_error", meal_id=str(meal_id), error=str(e))
            return False

    async def delete_meal_item(
        self, meal_id: UUID, item_id: UUID, user_id: UUID
    ) -> Optional[Meal]:
        """
        Delete a single food item from a meal.

        If this is the last item in the meal, deletes the entire meal.

        Returns:
            Updated meal if items remain, None if meal was deleted (last item removed)

        Raises:
            HTTPException 404: Meal not found or not owned by user
            HTTPException 404: Item not found in meal
        """
        from fastapi import HTTPException, status

        try:
            # Get the meal first to verify ownership
            meal = await self.get_meal(meal_id, user_id)
            if not meal:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Meal not found"
                )

            # Check if item exists in meal
            item_exists = any(item.id == item_id for item in meal.items)
            if not item_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Food item not found in meal"
                )

            # If this is the last item, delete the entire meal
            if len(meal.items) == 1:
                await self.delete_meal(meal_id, user_id)
                logger.info(
                    "meal_deleted_last_item_removed",
                    meal_id=str(meal_id),
                    item_id=str(item_id),
                    user_id=str(user_id)
                )
                return None

            # Delete the specific item
            delete_response = (
                supabase_service.client.table("meal_items")
                .delete()
                .eq("id", str(item_id))
                .eq("meal_id", str(meal_id))
                .execute()
            )

            if not delete_response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Failed to delete item"
                )

            # Recalculate meal totals
            remaining_items = [item for item in meal.items if item.id != item_id]
            new_total_calories = sum(item.calories for item in remaining_items)
            new_total_protein = sum(item.protein_g for item in remaining_items)
            new_total_carbs = sum(item.carbs_g for item in remaining_items)
            new_total_fat = sum(item.fat_g for item in remaining_items)

            # Update meal totals
            update_response = (
                supabase_service.client.table("meals")
                .update({
                    "total_calories": float(new_total_calories),
                    "total_protein_g": float(new_total_protein),
                    "total_carbs_g": float(new_total_carbs),
                    "total_fat_g": float(new_total_fat),
                    "updated_at": datetime.utcnow().isoformat()
                })
                .eq("id", str(meal_id))
                .eq("user_id", str(user_id))
                .execute()
            )

            logger.info(
                "meal_item_deleted",
                meal_id=str(meal_id),
                item_id=str(item_id),
                remaining_items=len(remaining_items),
                user_id=str(user_id)
            )

            # Return updated meal
            return await self.get_meal(meal_id, user_id)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "delete_meal_item_error",
                meal_id=str(meal_id),
                item_id=str(item_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete meal item"
            )

    async def update_meal_item(
        self,
        meal_id: UUID,
        item_id: UUID,
        updates: "UpdateMealItemRequest",
        user_id: UUID
    ) -> Meal:
        """
        Update a single meal item (quantity, serving, etc).

        Backend recalculates nutrition values from food data.
        Does NOT trust frontend-provided nutrition values.

        Raises:
            HTTPException 404: Meal or item not found
            HTTPException 400: Invalid serving or food data
        """
        from fastapi import HTTPException, status

        try:
            # Get meal to verify ownership and get current item
            meal = await self.get_meal(meal_id, user_id)
            if not meal:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Meal not found"
                )

            # Find the item
            current_item = None
            for item in meal.items:
                if item.id == item_id:
                    current_item = item
                    break

            if not current_item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Food item not found in meal"
                )

            # Get food data
            food_response = (
                supabase_service.client.table("foods")
                .select("*, food_servings(*)")
                .eq("id", str(current_item.food_id))
                .execute()
            )

            if not food_response.data:
                raise FoodNotFoundError(str(current_item.food_id))

            food_data = food_response.data[0]
            servings_data = food_data.pop("food_servings", [])
            food = Food(**food_data)
            food.servings = [FoodServing(**s) for s in servings_data]

            # Determine new values
            # Frontend always sends quantity + serving_id together, so if quantity is updated,
            # we must use BOTH new values (serving_id can be None for grams mode)
            if updates.quantity is not None:
                new_quantity = updates.quantity
                new_serving_id = updates.serving_id  # Can be None (grams) or UUID (serving)
            else:
                # No update - keep current values
                new_quantity = current_item.quantity
                new_serving_id = current_item.serving_id

            # Recalculate nutrition based on new quantity/serving
            if new_serving_id is None:
                # Gram-based
                grams = new_quantity
                serving = None

                # Validate
                if grams > 10000:
                    raise ValueError(f"Maximum 10,000g per item")
            else:
                # Serving-based
                serving = None
                for s in food.servings:
                    if s.id == new_serving_id:
                        serving = s
                        break

                if not serving:
                    raise InvalidServingError(str(new_serving_id))

                # Validate serving quantity
                if new_quantity > 50:
                    raise ValueError("Maximum 50 servings per item")

                if new_quantity > 10:
                    logger.warning(
                        "high_serving_quantity",
                        meal_id=str(meal_id),
                        item_id=str(item_id),
                        quantity=float(new_quantity)
                    )

                grams = new_quantity * serving.grams_per_serving

            # Calculate nutrition
            factor = grams / Decimal("100")
            new_calories = food.calories_per_100g * factor
            new_protein = food.protein_g_per_100g * factor
            new_carbs = food.carbs_g_per_100g * factor
            new_fat = food.fat_g_per_100g * factor

            # Update display fields
            new_display_unit = updates.display_unit if updates.display_unit else (
                "g" if new_serving_id is None else serving.serving_unit if serving else current_item.display_unit
            )
            new_display_label = updates.display_label if updates.display_label is not None else (
                None if new_serving_id is None else serving.serving_label if serving else current_item.display_label
            )

            # Update the item in database
            update_data = {
                "quantity": float(new_quantity),
                "serving_id": str(new_serving_id) if new_serving_id else None,
                "grams": float(grams),
                "calories": float(new_calories),
                "protein_g": float(new_protein),
                "carbs_g": float(new_carbs),
                "fat_g": float(new_fat),
                "display_unit": new_display_unit,
                "display_label": new_display_label
            }

            update_response = (
                supabase_service.client.table("meal_items")
                .update(update_data)
                .eq("id", str(item_id))
                .eq("meal_id", str(meal_id))
                .execute()
            )

            if not update_response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update item"
                )

            # Recalculate meal totals
            updated_meal_items = []
            for item in meal.items:
                if item.id == item_id:
                    # Use new values
                    updated_meal_items.append({
                        "calories": new_calories,
                        "protein_g": new_protein,
                        "carbs_g": new_carbs,
                        "fat_g": new_fat
                    })
                else:
                    # Keep existing values
                    updated_meal_items.append({
                        "calories": item.calories,
                        "protein_g": item.protein_g,
                        "carbs_g": item.carbs_g,
                        "fat_g": item.fat_g
                    })

            new_total_calories = sum(Decimal(str(i["calories"])) for i in updated_meal_items)
            new_total_protein = sum(Decimal(str(i["protein_g"])) for i in updated_meal_items)
            new_total_carbs = sum(Decimal(str(i["carbs_g"])) for i in updated_meal_items)
            new_total_fat = sum(Decimal(str(i["fat_g"])) for i in updated_meal_items)

            # Update meal totals
            meal_update_response = (
                supabase_service.client.table("meals")
                .update({
                    "total_calories": float(new_total_calories),
                    "total_protein_g": float(new_total_protein),
                    "total_carbs_g": float(new_total_carbs),
                    "total_fat_g": float(new_total_fat),
                    "updated_at": datetime.utcnow().isoformat()
                })
                .eq("id", str(meal_id))
                .eq("user_id", str(user_id))
                .execute()
            )

            logger.info(
                "meal_item_updated",
                meal_id=str(meal_id),
                item_id=str(item_id),
                old_quantity=float(current_item.quantity),
                new_quantity=float(new_quantity),
                user_id=str(user_id)
            )

            # Return updated meal
            return await self.get_meal(meal_id, user_id)

        except HTTPException:
            raise
        except (FoodNotFoundError, InvalidServingError, ServingMismatchError):
            raise
        except Exception as e:
            logger.error(
                "update_meal_item_error",
                meal_id=str(meal_id),
                item_id=str(item_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update meal item"
            )

    async def add_meal_item(
        self, meal_id: UUID, item: MealItemBase, user_id: UUID
    ) -> Meal:
        """
        Add a new food item to an existing meal.

        Recalculates meal nutrition totals after adding.

        Raises:
            HTTPException 404: Meal not found
            HTTPException 400: Invalid food or serving data
        """
        from fastapi import HTTPException, status

        try:
            # Verify meal exists and user owns it
            meal = await self.get_meal(meal_id, user_id)
            if not meal:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Meal not found"
                )

            # Get food data
            food_response = (
                supabase_service.client.table("foods")
                .select("*, food_servings(*)")
                .eq("id", str(item.food_id))
                .execute()
            )

            if not food_response.data:
                raise FoodNotFoundError(str(item.food_id))

            food_data = food_response.data[0]
            servings_data = food_data.pop("food_servings", [])
            food = Food(**food_data)
            food.servings = [FoodServing(**s) for s in servings_data]

            # Validate and calculate (same logic as create_meal)
            if item.serving_id is None:
                # Gram-based
                grams = item.quantity
                serving = None

                if grams > 10000:
                    raise ValueError("Maximum 10,000g per item")
            else:
                # Serving-based
                serving = None
                for s in food.servings:
                    if s.id == item.serving_id:
                        serving = s
                        break

                if not serving:
                    raise InvalidServingError(str(item.serving_id))

                if item.quantity > 50:
                    raise ValueError("Maximum 50 servings per item")

                if item.quantity > 10:
                    logger.warning(
                        "high_serving_quantity_add",
                        meal_id=str(meal_id),
                        quantity=float(item.quantity)
                    )

                grams = item.quantity * serving.grams_per_serving

            # Calculate nutrition
            factor = grams / Decimal("100")
            calories = food.calories_per_100g * factor
            protein = food.protein_g_per_100g * factor
            carbs = food.carbs_g_per_100g * factor
            fat = food.fat_g_per_100g * factor

            # Determine display order (append to end)
            display_order = item.display_order if item.display_order is not None else len(meal.items)

            # Insert new meal item
            new_item_data = {
                "meal_id": str(meal_id),
                "food_id": str(item.food_id),
                "quantity": float(item.quantity),
                "serving_id": str(item.serving_id) if item.serving_id else None,
                "grams": float(grams),
                "calories": float(calories),
                "protein_g": float(protein),
                "carbs_g": float(carbs),
                "fat_g": float(fat),
                "display_unit": item.display_unit,
                "display_label": item.display_label,
                "display_order": display_order
            }

            insert_response = (
                supabase_service.client.table("meal_items")
                .insert(new_item_data)
                .execute()
            )

            if not insert_response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to add item to meal"
                )

            # Recalculate meal totals
            new_total_calories = meal.total_calories + calories
            new_total_protein = meal.total_protein_g + protein
            new_total_carbs = meal.total_carbs_g + carbs
            new_total_fat = meal.total_fat_g + fat

            # Update meal totals
            update_response = (
                supabase_service.client.table("meals")
                .update({
                    "total_calories": float(new_total_calories),
                    "total_protein_g": float(new_total_protein),
                    "total_carbs_g": float(new_total_carbs),
                    "total_fat_g": float(new_total_fat),
                    "updated_at": datetime.utcnow().isoformat()
                })
                .eq("id", str(meal_id))
                .eq("user_id", str(user_id))
                .execute()
            )

            logger.info(
                "meal_item_added",
                meal_id=str(meal_id),
                food_id=str(item.food_id),
                calories=float(calories),
                user_id=str(user_id)
            )

            # Return updated meal
            return await self.get_meal(meal_id, user_id)

        except HTTPException:
            raise
        except (FoodNotFoundError, InvalidServingError):
            raise
        except Exception as e:
            logger.error(
                "add_meal_item_error",
                meal_id=str(meal_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add item to meal"
            )

    # =====================================================
    # Nutrition Stats
    # =====================================================

    async def get_nutrition_stats(
        self,
        user_id: UUID,
        date: str,
    ) -> NutritionStats:
        """
        Get daily nutrition stats for a specific date.

        Returns consumed totals vs goals.
        """
        try:
            # Parse date
            target_date = datetime.fromisoformat(date).date()
            start_datetime = datetime.combine(target_date, datetime.min.time())
            end_datetime = datetime.combine(
                target_date, datetime.max.time().replace(microsecond=0)
            )

            # Get meals for the day
            response = (
                supabase_service.client.table("meals")
                .select("total_calories, total_protein_g, total_carbs_g, total_fat_g, meal_type")
                .eq("user_id", str(user_id))
                .gte("logged_at", start_datetime.isoformat())
                .lte("logged_at", end_datetime.isoformat())
                .execute()
            )

            # Calculate totals
            total_calories = Decimal("0")
            total_protein = Decimal("0")
            total_carbs = Decimal("0")
            total_fat = Decimal("0")
            meals_by_type = {}

            for meal in response.data:
                total_calories += Decimal(str(meal["total_calories"]))
                total_protein += Decimal(str(meal["total_protein_g"]))
                total_carbs += Decimal(str(meal["total_carbs_g"]))
                total_fat += Decimal(str(meal["total_fat_g"]))

                meal_type = meal["meal_type"]
                meals_by_type[meal_type] = meals_by_type.get(meal_type, 0) + 1

            # Get user goals
            profile = await supabase_service.get_profile(user_id)

            return NutritionStats(
                date=date,
                calories_consumed=total_calories,
                protein_consumed=total_protein,
                carbs_consumed=total_carbs,
                fat_consumed=total_fat,
                calories_goal=profile.get("daily_calorie_goal") if profile else None,
                protein_goal=profile.get("daily_protein_goal") if profile else None,
                carbs_goal=profile.get("daily_carbs_goal") if profile else None,
                fat_goal=profile.get("daily_fat_goal") if profile else None,
                meals_count=len(response.data),
                meals_by_type=meals_by_type,
            )

        except Exception as e:
            logger.error("get_nutrition_stats_error", date=date, error=str(e))
            raise


# Singleton instance
nutrition_service = NutritionService()
