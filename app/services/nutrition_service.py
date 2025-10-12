"""
Nutrition Service

Handles business logic for foods, food servings, meals, and meal items.
Interfaces with database and performs nutrition calculations.
"""

import structlog
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from app.db import get_db
from app.models.nutrition import (
    Food,
    FoodServing,
    Meal,
    MealItem,
    MealItemBase,
    NutritionStats,
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
        Search foods by name using full-text search.

        Returns public foods + user's custom foods.
        """
        async with get_db() as conn:
            # Search foods with text search
            foods_query = """
                SELECT
                    f.id, f.name, f.brand_name,
                    f.calories_per_100g, f.protein_g_per_100g,
                    f.carbs_g_per_100g, f.fat_g_per_100g,
                    f.fiber_g_per_100g, f.sugar_g_per_100g, f.sodium_mg_per_100g,
                    f.food_type, f.dietary_flags, f.is_public, f.verified, f.usage_count,
                    f.created_by, f.created_at, f.updated_at
                FROM foods f
                WHERE (
                    f.is_public = TRUE
                    OR ($2::uuid IS NOT NULL AND f.created_by = $2)
                )
                AND to_tsvector('english', f.name || ' ' || COALESCE(f.brand_name, '')) @@ plainto_tsquery('english', $1)
                ORDER BY
                    f.usage_count DESC,
                    f.verified DESC,
                    f.name ASC
                LIMIT $3
            """

            foods_rows = await conn.fetch(foods_query, query, user_id, limit)

            if not foods_rows:
                return []

            # Get food IDs
            food_ids = [row['id'] for row in foods_rows]

            # Get servings for these foods
            servings_query = """
                SELECT
                    id, food_id, serving_size, serving_unit, serving_label,
                    grams_per_serving, is_default, display_order, created_at
                FROM food_servings
                WHERE food_id = ANY($1::uuid[])
                ORDER BY food_id, display_order, serving_size
            """

            servings_rows = await conn.fetch(servings_query, food_ids)

            # Build servings map
            servings_by_food = {}
            for row in servings_rows:
                food_id = row['food_id']
                if food_id not in servings_by_food:
                    servings_by_food[food_id] = []
                servings_by_food[food_id].append(FoodServing(**dict(row)))

            # Build food objects
            foods = []
            for row in foods_rows:
                food_dict = dict(row)
                food_dict['servings'] = servings_by_food.get(row['id'], [])
                foods.append(Food(**food_dict))

            return foods

    async def get_food(
        self,
        food_id: UUID,
        user_id: Optional[UUID] = None,
    ) -> Optional[Food]:
        """
        Get a single food by ID with servings.

        Returns None if not found or user doesn't have access.
        """
        async with get_db() as conn:
            # Get food
            food_query = """
                SELECT
                    id, name, brand_name,
                    calories_per_100g, protein_g_per_100g,
                    carbs_g_per_100g, fat_g_per_100g,
                    fiber_g_per_100g, sugar_g_per_100g, sodium_mg_per_100g,
                    food_type, dietary_flags, is_public, verified, usage_count,
                    created_by, created_at, updated_at
                FROM foods
                WHERE id = $1
                AND (is_public = TRUE OR ($2::uuid IS NOT NULL AND created_by = $2))
            """

            food_row = await conn.fetchrow(food_query, food_id, user_id)

            if not food_row:
                return None

            # Get servings
            servings_query = """
                SELECT
                    id, food_id, serving_size, serving_unit, serving_label,
                    grams_per_serving, is_default, display_order, created_at
                FROM food_servings
                WHERE food_id = $1
                ORDER BY display_order, serving_size
            """

            servings_rows = await conn.fetch(servings_query, food_id)
            servings = [FoodServing(**dict(row)) for row in servings_rows]

            # Build food
            food_dict = dict(food_row)
            food_dict['servings'] = servings
            return Food(**food_dict)

    async def get_food_servings(
        self,
        food_id: UUID,
        user_id: Optional[UUID] = None,
    ) -> List[FoodServing]:
        """Get all serving sizes for a food."""
        async with get_db() as conn:
            # Verify food access first
            access_query = """
                SELECT 1 FROM foods
                WHERE id = $1
                AND (is_public = TRUE OR ($2::uuid IS NOT NULL AND created_by = $2))
            """
            has_access = await conn.fetchval(access_query, food_id, user_id)

            if not has_access:
                return []

            # Get servings
            servings_query = """
                SELECT
                    id, food_id, serving_size, serving_unit, serving_label,
                    grams_per_serving, is_default, display_order, created_at
                FROM food_servings
                WHERE food_id = $1
                ORDER BY display_order, serving_size
            """

            rows = await conn.fetch(servings_query, food_id)
            return [FoodServing(**dict(row)) for row in rows]

    async def create_custom_food(
        self,
        user_id: UUID,
        name: str,
        brand_name: Optional[str],
        serving_size: Decimal,
        serving_unit: str,
        calories: Decimal,
        protein_g: Decimal,
        carbs_g: Decimal,
        fat_g: Decimal,
        fiber_g: Optional[Decimal] = None,
    ) -> Food:
        """
        Create a custom food with a single serving size.

        Takes nutrition for the user's serving and converts to per-100g.
        """
        # Estimate grams for this serving (rough estimate based on typical densities)
        # For custom foods, we'll use a default conversion
        # User can provide grams explicitly if needed (future enhancement)
        estimated_grams = serving_size * Decimal("100")  # Default: 1 serving = 100g

        # Convert nutrition to per-100g
        calories_per_100g = calories * Decimal("100") / estimated_grams
        protein_per_100g = protein_g * Decimal("100") / estimated_grams
        carbs_per_100g = carbs_g * Decimal("100") / estimated_grams
        fat_per_100g = fat_g * Decimal("100") / estimated_grams
        fiber_per_100g = (
            fiber_g * Decimal("100") / estimated_grams if fiber_g else None
        )

        async with get_db() as conn:
            # Insert food
            food_query = """
                INSERT INTO foods (
                    name, brand_name,
                    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
                    fiber_g_per_100g,
                    food_type, is_public, created_by
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, 'dish', FALSE, $8)
                RETURNING
                    id, name, brand_name,
                    calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g,
                    fiber_g_per_100g, sugar_g_per_100g, sodium_mg_per_100g,
                    food_type, dietary_flags, is_public, verified, usage_count,
                    created_by, created_at, updated_at
            """

            food_row = await conn.fetchrow(
                food_query,
                name,
                brand_name,
                calories_per_100g,
                protein_per_100g,
                carbs_per_100g,
                fat_per_100g,
                fiber_per_100g,
                user_id,
            )

            food_id = food_row['id']

            # Insert serving
            serving_query = """
                INSERT INTO food_servings (
                    food_id, serving_size, serving_unit, grams_per_serving, is_default
                )
                VALUES ($1, $2, $3, $4, TRUE)
                RETURNING
                    id, food_id, serving_size, serving_unit, serving_label,
                    grams_per_serving, is_default, display_order, created_at
            """

            serving_row = await conn.fetchrow(
                serving_query,
                food_id,
                serving_size,
                serving_unit,
                estimated_grams,
            )

            # Build food object
            food_dict = dict(food_row)
            food_dict['servings'] = [FoodServing(**dict(serving_row))]
            return Food(**food_dict)

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
        """
        if not logged_at:
            logged_at = datetime.utcnow()

        async with get_db() as conn:
            # Start transaction
            async with conn.transaction():
                # Create meal
                meal_query = """
                    INSERT INTO meals (
                        user_id, name, meal_type, logged_at, notes, source, ai_confidence
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING id, user_id, name, meal_type, logged_at, notes,
                              total_calories, total_protein_g, total_carbs_g, total_fat_g,
                              source, ai_confidence, ai_cost_usd,
                              created_at, updated_at
                """

                meal_row = await conn.fetchrow(
                    meal_query,
                    user_id,
                    name,
                    meal_type,
                    logged_at,
                    notes,
                    source,
                    ai_confidence,
                )

                meal_id = meal_row['id']

                # Add items and calculate totals
                total_calories = Decimal("0")
                total_protein = Decimal("0")
                total_carbs = Decimal("0")
                total_fat = Decimal("0")

                meal_items = []

                for idx, item in enumerate(items):
                    # Get food and serving
                    food_serving_query = """
                        SELECT
                            f.calories_per_100g, f.protein_g_per_100g,
                            f.carbs_g_per_100g, f.fat_g_per_100g,
                            fs.grams_per_serving, fs.serving_unit, fs.serving_label
                        FROM foods f
                        JOIN food_servings fs ON fs.food_id = f.id
                        WHERE f.id = $1 AND fs.id = $2
                    """

                    food_data = await conn.fetchrow(
                        food_serving_query, item.food_id, item.serving_id
                    )

                    if not food_data:
                        raise ValueError(
                            f"Food {item.food_id} or serving {item.serving_id} not found"
                        )

                    # Calculate grams and nutrition
                    grams = item.quantity * food_data['grams_per_serving']
                    multiplier = grams / Decimal("100")

                    item_calories = food_data['calories_per_100g'] * multiplier
                    item_protein = food_data['protein_g_per_100g'] * multiplier
                    item_carbs = food_data['carbs_g_per_100g'] * multiplier
                    item_fat = food_data['fat_g_per_100g'] * multiplier

                    # Insert meal item
                    item_query = """
                        INSERT INTO meal_items (
                            meal_id, food_id, quantity, serving_id, grams,
                            calories, protein_g, carbs_g, fat_g,
                            display_unit, display_label, display_order
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                        RETURNING id, meal_id, food_id, quantity, serving_id, grams,
                                  calories, protein_g, carbs_g, fat_g,
                                  display_unit, display_label, display_order, created_at
                    """

                    item_row = await conn.fetchrow(
                        item_query,
                        meal_id,
                        item.food_id,
                        item.quantity,
                        item.serving_id,
                        grams,
                        item_calories,
                        item_protein,
                        item_carbs,
                        item_fat,
                        food_data['serving_unit'],
                        food_data['serving_label'],
                        idx,
                    )

                    meal_items.append(MealItem(**dict(item_row)))

                    # Add to totals
                    total_calories += item_calories
                    total_protein += item_protein
                    total_carbs += item_carbs
                    total_fat += item_fat

                # Update meal totals
                update_query = """
                    UPDATE meals
                    SET total_calories = $1, total_protein_g = $2,
                        total_carbs_g = $3, total_fat_g = $4
                    WHERE id = $5
                """

                await conn.execute(
                    update_query,
                    total_calories,
                    total_protein,
                    total_carbs,
                    total_fat,
                    meal_id,
                )

                # Build meal object
                meal_dict = dict(meal_row)
                meal_dict['total_calories'] = total_calories
                meal_dict['total_protein_g'] = total_protein
                meal_dict['total_carbs_g'] = total_carbs
                meal_dict['total_fat_g'] = total_fat
                meal_dict['items'] = meal_items

                return Meal(**meal_dict)

    async def get_user_meals(
        self,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Meal]:
        """Get user's meals with optional date filtering."""
        async with get_db() as conn:
            # Build query
            conditions = ["user_id = $1"]
            params = [user_id]
            param_idx = 2

            if start_date:
                conditions.append(f"logged_at >= ${param_idx}")
                params.append(start_date)
                param_idx += 1

            if end_date:
                conditions.append(f"logged_at < ${param_idx}")
                params.append(end_date)
                param_idx += 1

            where_clause = " AND ".join(conditions)

            # Get meals
            meals_query = f"""
                SELECT
                    id, user_id, name, meal_type, logged_at, notes,
                    total_calories, total_protein_g, total_carbs_g, total_fat_g,
                    source, ai_confidence, ai_cost_usd,
                    created_at, updated_at
                FROM meals
                WHERE {where_clause}
                ORDER BY logged_at DESC
                LIMIT ${param_idx} OFFSET ${param_idx + 1}
            """

            params.extend([limit, offset])
            meals_rows = await conn.fetch(meals_query, *params)

            if not meals_rows:
                return []

            meal_ids = [row['id'] for row in meals_rows]

            # Get items for these meals
            items_query = """
                SELECT
                    id, meal_id, food_id, quantity, serving_id, grams,
                    calories, protein_g, carbs_g, fat_g,
                    display_unit, display_label, display_order, created_at
                FROM meal_items
                WHERE meal_id = ANY($1::uuid[])
                ORDER BY meal_id, display_order
            """

            items_rows = await conn.fetch(items_query, meal_ids)

            # Build items map
            items_by_meal = {}
            for row in items_rows:
                meal_id = row['meal_id']
                if meal_id not in items_by_meal:
                    items_by_meal[meal_id] = []
                items_by_meal[meal_id].append(MealItem(**dict(row)))

            # Build meal objects
            meals = []
            for row in meals_rows:
                meal_dict = dict(row)
                meal_dict['items'] = items_by_meal.get(row['id'], [])
                meals.append(Meal(**meal_dict))

            return meals

    async def get_meal(self, meal_id: UUID, user_id: UUID) -> Optional[Meal]:
        """Get a single meal by ID."""
        async with get_db() as conn:
            # Get meal
            meal_query = """
                SELECT
                    id, user_id, name, meal_type, logged_at, notes,
                    total_calories, total_protein_g, total_carbs_g, total_fat_g,
                    source, ai_confidence, ai_cost_usd,
                    created_at, updated_at
                FROM meals
                WHERE id = $1 AND user_id = $2
            """

            meal_row = await conn.fetchrow(meal_query, meal_id, user_id)

            if not meal_row:
                return None

            # Get items
            items_query = """
                SELECT
                    id, meal_id, food_id, quantity, serving_id, grams,
                    calories, protein_g, carbs_g, fat_g,
                    display_unit, display_label, display_order, created_at
                FROM meal_items
                WHERE meal_id = $1
                ORDER BY display_order
            """

            items_rows = await conn.fetch(items_query, meal_id)
            items = [MealItem(**dict(row)) for row in items_rows]

            # Build meal
            meal_dict = dict(meal_row)
            meal_dict['items'] = items
            return Meal(**meal_dict)

    async def delete_meal(self, meal_id: UUID, user_id: UUID) -> bool:
        """Delete a meal. Returns True if deleted, False if not found."""
        async with get_db() as conn:
            result = await conn.execute(
                "DELETE FROM meals WHERE id = $1 AND user_id = $2",
                meal_id,
                user_id,
            )
            return result == "DELETE 1"

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
        async with get_db() as conn:
            # Get date range (start and end of day)
            stats_query = """
                SELECT
                    COALESCE(SUM(total_calories), 0) as calories_consumed,
                    COALESCE(SUM(total_protein_g), 0) as protein_consumed,
                    COALESCE(SUM(total_carbs_g), 0) as carbs_consumed,
                    COALESCE(SUM(total_fat_g), 0) as fat_consumed,
                    COUNT(*) as meals_count
                FROM meals
                WHERE user_id = $1
                AND logged_at >= $2::date
                AND logged_at < ($2::date + INTERVAL '1 day')
            """

            stats_row = await conn.fetchrow(stats_query, user_id, date)

            # Get meals by type
            by_type_query = """
                SELECT meal_type, COUNT(*) as count
                FROM meals
                WHERE user_id = $1
                AND logged_at >= $2::date
                AND logged_at < ($2::date + INTERVAL '1 day')
                GROUP BY meal_type
            """

            by_type_rows = await conn.fetch(by_type_query, user_id, date)
            meals_by_type = {row['meal_type']: row['count'] for row in by_type_rows}

            # Get user goals
            goals_query = """
                SELECT
                    daily_calorie_goal, daily_protein_goal,
                    daily_carbs_goal, daily_fat_goal
                FROM profiles
                WHERE id = $1
            """

            goals_row = await conn.fetchrow(goals_query, user_id)

            return NutritionStats(
                date=date,
                calories_consumed=stats_row['calories_consumed'],
                protein_consumed=stats_row['protein_consumed'],
                carbs_consumed=stats_row['carbs_consumed'],
                fat_consumed=stats_row['fat_consumed'],
                calories_goal=goals_row['daily_calorie_goal'] if goals_row else None,
                protein_goal=goals_row['daily_protein_goal'] if goals_row else None,
                carbs_goal=goals_row['daily_carbs_goal'] if goals_row else None,
                fat_goal=goals_row['daily_fat_goal'] if goals_row else None,
                meals_count=stats_row['meals_count'],
                meals_by_type=meals_by_type,
            )


# Singleton instance
nutrition_service = NutritionService()
