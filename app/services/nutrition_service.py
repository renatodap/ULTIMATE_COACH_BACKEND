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
        Search foods by name using Supabase text search.

        Returns public foods + user's custom foods.
        Minimum 2 characters required.

        Raises:
            SearchQueryTooShortError: If query < 2 characters
            SearchFailedError: If database query fails
        """
        if len(query) < 2:
            raise SearchQueryTooShortError(query)

        try:
            # Search public foods
            public_query = (
                supabase_service.client.table("foods")
                .select("*, food_servings(*)")
                .eq("is_public", True)
                .text_search("name", query, config="english")
                .order("usage_count", desc=True)
                .order("verified", desc=True)
                .limit(limit)
            )

            public_response = public_query.execute()
            foods = []

            # Add public foods
            for row in public_response.data:
                servings_data = row.pop("food_servings", [])
                food = Food(**row)
                food.servings = [FoodServing(**s) for s in servings_data]
                foods.append(food)

            # Search user's custom foods if user_id provided
            if user_id:
                custom_query = (
                    supabase_service.client.table("foods")
                    .select("*, food_servings(*)")
                    .eq("created_by", str(user_id))
                    .ilike("name", f"%{query}%")
                    .limit(limit)
                )

                custom_response = custom_query.execute()

                for row in custom_response.data:
                    servings_data = row.pop("food_servings", [])
                    food = Food(**row)
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

        Calculates nutrition totals from items.
        VALIDATES: serving_id belongs to food_id.

        PERFORMANCE: Batches all food fetches in a single query (fixes N+1 issue).

        Raises:
            MealEmptyError: If items list is empty
            FoodNotFoundError: If any food_id is not found or inaccessible
            InvalidServingError: If any serving_id is not found
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

                foods_map[UUID(food.id)] = food
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

                # Find serving
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

                # Calculate nutrition
                grams = item.quantity * serving.grams_per_serving
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
                        "serving": serving,
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
                meal_items_data.append(
                    {
                        "meal_id": meal_id,
                        "food_id": str(validated["food"].id),
                        "quantity": float(validated["quantity"]),
                        "serving_id": str(validated["serving"].id),
                        "grams": float(validated["grams"]),
                        "calories": float(validated["calories"]),
                        "protein_g": float(validated["protein_g"]),
                        "carbs_g": float(validated["carbs_g"]),
                        "fat_g": float(validated["fat_g"]),
                        "display_unit": validated["serving"].serving_unit,
                        "display_label": validated["serving"].serving_label,
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
            query = (
                supabase_service.client.table("meals")
                .select("*, meal_items(*)")
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

            meals = []
            for row in response.data:
                items_data = row.pop("meal_items", [])
                meal = Meal(**row)
                meal.items = [MealItem(**item) for item in items_data]
                meals.append(meal)

            return meals

        except Exception as e:
            logger.error("get_user_meals_error", user_id=str(user_id), error=str(e))
            return []

    async def get_meal(self, meal_id: UUID, user_id: UUID) -> Optional[Meal]:
        """Get a single meal by ID."""
        try:
            response = (
                supabase_service.client.table("meals")
                .select("*, meal_items(*)")
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
