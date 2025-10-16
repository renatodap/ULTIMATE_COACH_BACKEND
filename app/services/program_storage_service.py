"""
Program Storage Service

Stores generated programs (ProgramBundle) into the database plan instance tables:
- programs (immutable program snapshot)
- session_instances (planned workout sessions)
- exercise_plan_items (exercises within sessions)
- meal_instances (planned meals)
- meal_item_plan (food items within meals)
- calendar_events (unified calendar view)

This bridges the gap between program generation (ultimate_ai_consultation)
and the adaptive system (daily adjustments, reassessments).
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date
from uuid import UUID
import structlog

from app.services.supabase_service import SupabaseService

logger = structlog.get_logger()


class ProgramStorageService:
    """Stores generated programs into database plan instances"""

    def __init__(self, db: Optional[SupabaseService] = None):
        self.db = db or SupabaseService()

    async def store_program_bundle(
        self,
        program_bundle: Dict[str, Any],
        user_id: str,
    ) -> str:
        """
        Store a complete ProgramBundle into the database.

        Args:
            program_bundle: ProgramBundle dict from generate_program_from_consultation()
            user_id: User UUID

        Returns:
            program_id: UUID of the stored program

        Creates:
            - 1 programs row (immutable snapshot)
            - N session_instances rows (one per weekly session)
            - M exercise_plan_items rows (exercises within sessions)
            - P meal_instances rows (one per meal per day)
            - Q meal_item_plan rows (food items within meals)
            - R calendar_events rows (denormalized view)
        """
        client = self.db.client

        logger.info(
            "storing_program_bundle",
            user_id=user_id,
            program_id=program_bundle.get("program_id"),
        )

        # Step 1: Store program snapshot
        program_id = await self._store_program(client, program_bundle, user_id)

        # Step 2: Store training sessions
        await self._store_training_sessions(
            client, program_id, program_bundle.get("training_plan", {})
        )

        # Step 3: Store meal plan
        await self._store_meal_plan(
            client, program_id, program_bundle.get("nutrition_plan", {})
        )

        # Step 4: Create calendar events (denormalized)
        await self._create_calendar_events(
            client, program_id, user_id, program_bundle
        )

        logger.info("program_bundle_stored", program_id=program_id, user_id=user_id)

        return program_id

    async def _store_program(
        self, client, program_bundle: Dict[str, Any], user_id: str
    ) -> str:
        """Store immutable program snapshot in programs table"""

        program_data = {
            "id": program_bundle.get("program_id"),
            "user_id": user_id,
            "primary_goal": program_bundle.get("primary_goal"),
            "program_start_date": date.today().isoformat(),
            "program_duration_weeks": program_bundle.get("timeline_weeks", 12),
            "version": program_bundle.get("version", {}).get("schema_version", "1.0.0"),
            "created_at": program_bundle.get("created_at"),
            "valid_until": program_bundle.get("valid_until"),
            "next_reassessment_date": (date.today() + timedelta(days=14)).isoformat(),
            "tdee": {
                "tdee_kcal": program_bundle.get("tdee_kcal"),
                "bmr_kcal": program_bundle.get("bmr_kcal"),
                "activity_multiplier": program_bundle.get("activity_multiplier"),
            },
            "macros": program_bundle.get("macro_targets", {}),
            "safety": program_bundle.get("safety_report", {}),
            "feasibility": program_bundle.get("feasibility_report", {}),
            "provenance": program_bundle.get("provenance", {}),
            "full_bundle": program_bundle,  # Store complete bundle for reference
        }

        result = client.table("programs").insert(program_data).execute()

        if not result.data:
            raise ValueError("Failed to store program")

        return result.data[0]["id"]

    async def _store_training_sessions(
        self, client, program_id: str, training_plan: Dict[str, Any]
    ):
        """Store training sessions and exercises"""

        weekly_sessions = training_plan.get("weekly_sessions", [])
        if not weekly_sessions:
            logger.warning("no_training_sessions_to_store", program_id=program_id)
            return

        # Map day names to indices (for week_index, day_index)
        day_to_index = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }

        session_instances = []
        exercise_items = []

        for session_idx, session in enumerate(weekly_sessions):
            day_of_week = session.get("day_of_week", "monday").lower()
            day_index = day_to_index.get(day_of_week, session_idx % 7)

            # Create session instance
            session_instance = {
                "program_id": program_id,
                "week_index": 0,  # Will repeat weekly
                "day_index": day_index,
                "day_of_week": day_of_week,
                "time_of_day": session.get("time_of_day", "evening"),
                "session_kind": "resistance",  # TODO: Infer from exercises
                "session_name": session.get("session_name"),
                "estimated_duration_minutes": session.get(
                    "estimated_duration_minutes", 60
                ),
                "notes": session.get("notes"),
                "state": "planned",
            }

            # Insert session and get ID
            result = client.table("session_instances").insert(session_instance).execute()
            if not result.data:
                logger.error(
                    "failed_to_store_session", session_name=session.get("session_name")
                )
                continue

            session_instance_id = result.data[0]["id"]

            # Create exercise plan items for this session
            exercises = session.get("exercises", [])
            for ex_idx, exercise in enumerate(exercises):
                exercise_item = {
                    "session_instance_id": session_instance_id,
                    "order_index": ex_idx,
                    "name": exercise.get("exercise_name"),
                    "muscle_groups": exercise.get("muscle_groups_primary", []),
                    "sets": exercise.get("sets"),
                    "rep_range": exercise.get("rep_range"),
                    "rest_seconds": exercise.get("rest_seconds", 120),
                    "rir": exercise.get("rir"),
                    "notes": exercise.get("instructions"),
                }
                exercise_items.append(exercise_item)

        # Bulk insert exercises
        if exercise_items:
            client.table("exercise_plan_items").insert(exercise_items).execute()

        logger.info(
            "training_sessions_stored",
            program_id=program_id,
            sessions=len(weekly_sessions),
            exercises=len(exercise_items),
        )

    async def _store_meal_plan(
        self, client, program_id: str, nutrition_plan: Dict[str, Any]
    ):
        """Store meal plan instances and food items"""

        daily_meal_plans = nutrition_plan.get("daily_meal_plans", [])
        if not daily_meal_plans:
            logger.warning("no_meal_plans_to_store", program_id=program_id)
            return

        meal_instances = []
        meal_items = []

        for daily_plan in daily_meal_plans:
            day_number = daily_plan.get("day_number", 1)
            week_index = (day_number - 1) // 7
            day_index = (day_number - 1) % 7

            meals = daily_plan.get("meals", [])
            for meal_idx, meal in enumerate(meals):
                # Create meal instance
                meal_instance = {
                    "program_id": program_id,
                    "week_index": week_index,
                    "day_index": day_index,
                    "order_index": meal_idx,
                    "meal_type": meal.get("meal_time"),
                    "meal_name": meal.get("meal_name"),
                    "totals_json": {
                        "calories": meal.get("total_calories"),
                        "protein_g": meal.get("total_protein_g"),
                        "carbs_g": meal.get("total_carbs_g"),
                        "fat_g": meal.get("total_fat_g"),
                    },
                    "notes": meal.get("notes"),
                }

                # Insert meal and get ID
                result = client.table("meal_instances").insert(meal_instance).execute()
                if not result.data:
                    logger.error("failed_to_store_meal", meal_name=meal.get("meal_name"))
                    continue

                meal_instance_id = result.data[0]["id"]

                # Create meal item plan for this meal
                foods = meal.get("foods", [])
                for food_idx, food in enumerate(foods):
                    meal_item = {
                        "meal_instance_id": meal_instance_id,
                        "order_index": food_idx,
                        "food_name": food.get("food_name"),
                        "serving_size": food.get("serving_size"),
                        "serving_unit": food.get("serving_unit", "g"),
                        "targets_json": {
                            "calories": food.get("calories"),
                            "protein_g": food.get("protein_g"),
                            "carbs_g": food.get("carbs_g"),
                            "fat_g": food.get("fat_g"),
                        },
                    }
                    meal_items.append(meal_item)

        # Bulk insert meal items
        if meal_items:
            client.table("meal_item_plan").insert(meal_items).execute()

        logger.info(
            "meal_plan_stored",
            program_id=program_id,
            daily_plans=len(daily_meal_plans),
            meal_items=len(meal_items),
        )

    async def _create_calendar_events(
        self, client, program_id: str, user_id: str, program_bundle: Dict[str, Any]
    ):
        """Create denormalized calendar events for unified view"""

        calendar_events = []
        start_date = date.today()

        # Training sessions (repeat weekly for 12 weeks)
        training_plan = program_bundle.get("training_plan", {})
        weekly_sessions = training_plan.get("weekly_sessions", [])

        day_to_index = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }

        for week in range(12):  # 12-week program
            for session in weekly_sessions:
                day_of_week = session.get("day_of_week", "monday").lower()
                day_index = day_to_index.get(day_of_week, 0)
                event_date = start_date + timedelta(days=week * 7 + day_index)

                # Fetch session_instance_id (we need to query it)
                # For now, we'll create events without ref_id and link later
                calendar_events.append(
                    {
                        "user_id": user_id,
                        "program_id": program_id,
                        "date": event_date.isoformat(),
                        "event_type": "training",
                        "ref_table": "session_instances",
                        "ref_id": "00000000-0000-0000-0000-000000000000",  # Placeholder
                        "title": session.get("session_name"),
                        "details": {
                            "duration_minutes": session.get(
                                "estimated_duration_minutes", 60
                            ),
                            "time_of_day": session.get("time_of_day"),
                        },
                        "status": "planned",
                    }
                )

        # Meals (repeat weekly for 12 weeks)
        nutrition_plan = program_bundle.get("nutrition_plan", {})
        daily_meal_plans = nutrition_plan.get("daily_meal_plans", [])

        for week in range(12):
            for daily_plan in daily_meal_plans[:7]:  # First 7 days (1 week)
                day_number = daily_plan.get("day_number", 1)
                day_index = (day_number - 1) % 7
                event_date = start_date + timedelta(days=week * 7 + day_index)

                meals = daily_plan.get("meals", [])
                for meal in meals:
                    calendar_events.append(
                        {
                            "user_id": user_id,
                            "program_id": program_id,
                            "date": event_date.isoformat(),
                            "event_type": "meal",
                            "ref_table": "meal_instances",
                            "ref_id": "00000000-0000-0000-0000-000000000000",  # Placeholder
                            "title": meal.get("meal_name"),
                            "details": {
                                "meal_type": meal.get("meal_time"),
                                "calories": meal.get("total_calories"),
                            },
                            "status": "planned",
                        }
                    )

        # Bulk insert calendar events (in batches to avoid hitting limits)
        batch_size = 100
        for i in range(0, len(calendar_events), batch_size):
            batch = calendar_events[i : i + batch_size]
            client.table("calendar_events").insert(batch).execute()

        logger.info(
            "calendar_events_created",
            program_id=program_id,
            events=len(calendar_events),
        )
