"""
Meal Matching Service

Matches logged meals to planned meal_instances and calculates nutrition adherence.
This service bridges the gap between:
- User's actual logged meals (meal_logs table)
- User's planned meals (meal_instances table)

Matching Algorithm:
1. Find planned meals for the same day and meal type (breakfast, lunch, dinner, snack)
2. Calculate similarity score based on:
   - Meal type match (breakfast vs breakfast)
   - Macro adherence (actual vs target calories, protein, carbs, fat)
   - Food overlap (did they eat planned foods?)
   - Timing match (did they eat at typical time for meal type?)
3. Link meal to best matching meal_instance
4. Create adherence_record with macro variance details
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
from uuid import UUID
import structlog

from app.services.supabase_service import SupabaseService

logger = structlog.get_logger()


class MealMatchingService:
    """Matches logged meals to planned meals and calculates nutrition adherence"""

    def __init__(self, db: Optional[SupabaseService] = None):
        self.db = db or SupabaseService()

    async def match_meal_to_plan(
        self,
        meal_log_id: str,
        user_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Match a logged meal to a planned meal_instance.

        Args:
            meal_log_id: UUID of the logged meal
            user_id: User UUID

        Returns:
            Adherence record dict if matched, None if no match found

        Flow:
        1. Fetch logged meal details
        2. Find planned meals for that day and meal type
        3. Calculate similarity scores based on macros
        4. Link to best match (if score > threshold)
        5. Create adherence_record with macro variance
        """
        client = self.db.client

        logger.info(
            "matching_meal_to_plan",
            meal_log_id=meal_log_id,
            user_id=user_id,
        )

        # Step 1: Fetch logged meal
        meal_result = (
            client.table("meal_logs")
            .select("*")
            .eq("id", meal_log_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not meal_result.data:
            logger.warning("meal_not_found", meal_log_id=meal_log_id)
            return None

        meal = meal_result.data[0]
        meal_date = datetime.fromisoformat(
            meal["logged_at"].replace("Z", "+00:00")
        ).date()

        logger.info(
            "fetched_meal",
            meal_log_id=meal_log_id,
            meal_date=str(meal_date),
            meal_name=meal.get("meal_name"),
        )

        # Step 2: Find planned meals for that day
        # Get user's active program
        program_result = (
            client.table("programs")
            .select("id, program_start_date, program_duration_weeks")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        if not program_result.data:
            logger.warning("no_active_program", user_id=user_id)
            return None

        program = program_result.data[0]
        program_id = program["id"]
        program_start = date.fromisoformat(program["program_start_date"])

        # Calculate week_index and day_index
        days_since_start = (meal_date - program_start).days
        if days_since_start < 0:
            logger.warning(
                "meal_before_program_start",
                meal_date=str(meal_date),
                program_start=str(program_start),
            )
            return None

        week_index = days_since_start // 7
        day_index = days_since_start % 7

        logger.info(
            "calculated_program_day",
            week_index=week_index,
            day_index=day_index,
            program_id=program_id,
        )

        # Fetch planned meals for this day
        # (meal_instances repeat weekly, so we use modulo)
        # Fetch meals for week 0 or week_index % pattern_weeks
        meals_result = (
            client.table("meal_instances")
            .select("*, meal_item_plan(*)")
            .eq("program_id", program_id)
            .eq("week_index", week_index % 2)  # Meals may have 1-2 week rotation
            .eq("day_index", day_index)
            .execute()
        )

        if not meals_result.data:
            logger.info(
                "no_planned_meals_for_day",
                day_index=day_index,
                program_id=program_id,
            )
            return None

        # Step 3: Calculate similarity scores for each planned meal
        best_match = None
        best_score = 0.0
        similarity_threshold = 0.3  # Minimum 30% similarity

        for planned_meal in meals_result.data:
            score = self._calculate_similarity_score(meal, planned_meal)
            logger.info(
                "calculated_similarity",
                meal_instance_id=planned_meal["id"],
                meal_name=planned_meal.get("meal_name"),
                score=score,
            )

            if score > best_score:
                best_score = score
                best_match = planned_meal

        if best_score < similarity_threshold:
            logger.info(
                "no_match_above_threshold",
                best_score=best_score,
                threshold=similarity_threshold,
            )
            return None

        # Step 4: Link meal to meal_instance
        logger.info(
            "matched_meal_to_plan",
            meal_log_id=meal_log_id,
            meal_instance_id=best_match["id"],
            similarity_score=best_score,
        )

        # Update meal_log with planned_meal_instance_id
        client.table("meal_logs").update(
            {"planned_meal_instance_id": best_match["id"]}
        ).eq("id", meal_log_id).execute()

        # Step 5: Create adherence record
        adherence_status = self._determine_adherence_status(best_score)
        macro_variance = self._calculate_macro_variance(meal, best_match)

        adherence_data = {
            "user_id": user_id,
            "program_id": program_id,
            "date": meal_date.isoformat(),
            "category": "nutrition",
            "planned_ref_table": "meal_instances",
            "planned_ref_id": best_match["id"],
            "actual_ref_table": "meal_logs",
            "actual_ref_id": meal_log_id,
            "status": adherence_status,
            "similarity_score": best_score,
            "details": {
                "matched_meal": best_match.get("meal_name"),
                "meal_type": best_match.get("meal_type"),
                "macro_variance": macro_variance,
            },
        }

        adherence_result = (
            client.table("adherence_records").insert(adherence_data).execute()
        )

        if not adherence_result.data:
            logger.error("failed_to_create_adherence_record", meal_log_id=meal_log_id)
            return None

        logger.info(
            "adherence_record_created",
            adherence_id=adherence_result.data[0]["id"],
            status=adherence_status,
            similarity_score=best_score,
        )

        return adherence_result.data[0]

    def _calculate_similarity_score(
        self, logged_meal: Dict[str, Any], planned_meal: Dict[str, Any]
    ) -> float:
        """
        Calculate similarity between logged meal and planned meal.

        Scoring factors:
        - Meal type match (30%): Breakfast vs breakfast, lunch vs lunch, etc.
        - Calorie accuracy (25%): How close are actual calories to target?
        - Protein accuracy (20%): How close is protein to target?
        - Carbs accuracy (15%): How close are carbs to target?
        - Fat accuracy (10%): How close is fat to target?

        Args:
            logged_meal: Logged meal dict
            planned_meal: Planned meal_instance dict (with meal_item_plan)

        Returns:
            Similarity score (0.0 to 1.0)
        """
        score = 0.0

        # Factor 1: Meal type match (30%)
        # Infer meal type from logged_at time if not explicitly set
        logged_meal_type = self._infer_meal_type(logged_meal)
        planned_meal_type = planned_meal.get("meal_type", "")

        if logged_meal_type == planned_meal_type:
            score += 0.3

        # Get logged meal macros
        logged_calories = logged_meal.get("total_calories", 0)
        logged_protein = logged_meal.get("total_protein_g", 0)
        logged_carbs = logged_meal.get("total_carbs_g", 0)
        logged_fat = logged_meal.get("total_fat_g", 0)

        # Get planned meal macros
        planned_totals = planned_meal.get("totals_json", {})
        planned_calories = planned_totals.get("calories", 0)
        planned_protein = planned_totals.get("protein_g", 0)
        planned_carbs = planned_totals.get("carbs_g", 0)
        planned_fat = planned_totals.get("fat_g", 0)

        # Factor 2: Calorie accuracy (25%)
        if planned_calories > 0:
            calorie_ratio = self._calculate_accuracy_ratio(
                logged_calories, planned_calories
            )
            score += calorie_ratio * 0.25

        # Factor 3: Protein accuracy (20%)
        if planned_protein > 0:
            protein_ratio = self._calculate_accuracy_ratio(
                logged_protein, planned_protein
            )
            score += protein_ratio * 0.20

        # Factor 4: Carbs accuracy (15%)
        if planned_carbs > 0:
            carbs_ratio = self._calculate_accuracy_ratio(logged_carbs, planned_carbs)
            score += carbs_ratio * 0.15

        # Factor 5: Fat accuracy (10%)
        if planned_fat > 0:
            fat_ratio = self._calculate_accuracy_ratio(logged_fat, planned_fat)
            score += fat_ratio * 0.10

        return min(score, 1.0)  # Cap at 1.0

    def _infer_meal_type(self, meal: Dict[str, Any]) -> str:
        """
        Infer meal type from logged_at timestamp if not explicitly set.

        Time ranges:
        - Breakfast: 5am - 11am
        - Lunch: 11am - 3pm
        - Dinner: 5pm - 9pm
        - Snack: All other times
        """
        # Check if meal_type is explicitly set in meal_logs
        if "meal_type" in meal and meal["meal_type"]:
            return meal["meal_type"]

        # Infer from logged_at timestamp
        logged_at_str = meal.get("logged_at")
        if not logged_at_str:
            return "snack"

        try:
            logged_at = datetime.fromisoformat(logged_at_str.replace("Z", "+00:00"))
            hour = logged_at.hour

            if 5 <= hour < 11:
                return "breakfast"
            elif 11 <= hour < 15:
                return "lunch"
            elif 17 <= hour < 21:
                return "dinner"
            else:
                return "snack"
        except (ValueError, AttributeError):
            return "snack"

    def _calculate_accuracy_ratio(self, actual: float, target: float) -> float:
        """
        Calculate accuracy ratio between actual and target values.

        Returns:
            Accuracy score (0.0 to 1.0)
            - 1.0 = exact match
            - 0.9 = within 10%
            - 0.5 = within 50%
            - 0.0 = >100% difference
        """
        if target == 0:
            return 0.0

        # Calculate percentage difference
        diff_pct = abs(actual - target) / target

        # Convert to accuracy score
        # 0% diff → 1.0 score
        # 10% diff → 0.9 score
        # 50% diff → 0.5 score
        # 100% diff → 0.0 score
        accuracy = max(0.0, 1.0 - diff_pct)

        return accuracy

    def _calculate_macro_variance(
        self, logged_meal: Dict[str, Any], planned_meal: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate variance between logged and planned macros.

        Returns:
            Dict with actual, target, variance, and variance_pct for each macro
        """
        planned_totals = planned_meal.get("totals_json", {})

        macros = ["calories", "protein_g", "carbs_g", "fat_g"]
        variance = {}

        for macro in macros:
            # Get actual value
            if macro == "calories":
                actual = logged_meal.get("total_calories", 0)
                target = planned_totals.get("calories", 0)
            else:
                actual = logged_meal.get(f"total_{macro}", 0)
                target = planned_totals.get(macro, 0)

            diff = actual - target
            diff_pct = (diff / target * 100) if target > 0 else 0

            variance[macro] = {
                "actual": actual,
                "target": target,
                "variance": diff,
                "variance_pct": round(diff_pct, 1),
            }

        return variance

    def _determine_adherence_status(self, similarity_score: float) -> str:
        """
        Determine adherence status based on similarity score.

        Thresholds:
        - 0.9+ = completed (excellent adherence)
        - 0.7-0.9 = similar (good adherence)
        - 0.5-0.7 = partial (moderate adherence)
        - <0.5 = off_plan (poor adherence)

        Args:
            similarity_score: Score from 0.0 to 1.0

        Returns:
            Status string: "completed", "similar", "partial", or "off_plan"
        """
        if similarity_score >= 0.9:
            return "completed"
        elif similarity_score >= 0.7:
            return "similar"
        elif similarity_score >= 0.5:
            return "partial"
        else:
            return "off_plan"

    async def match_skipped_meals(
        self, user_id: str, target_date: date
    ) -> List[Dict[str, Any]]:
        """
        Find planned meals that were not logged on a given day.

        Args:
            user_id: User UUID
            target_date: Date to check

        Returns:
            List of adherence records for skipped meals
        """
        client = self.db.client

        logger.info(
            "checking_for_skipped_meals",
            user_id=user_id,
            date=str(target_date),
        )

        # Get user's active program
        program_result = (
            client.table("programs")
            .select("id, program_start_date")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        if not program_result.data:
            logger.warning("no_active_program", user_id=user_id)
            return []

        program = program_result.data[0]
        program_id = program["id"]
        program_start = date.fromisoformat(program["program_start_date"])

        # Calculate day_index
        days_since_start = (target_date - program_start).days
        if days_since_start < 0:
            return []

        week_index = days_since_start // 7
        day_index = days_since_start % 7

        # Fetch planned meals for this day
        meals_result = (
            client.table("meal_instances")
            .select("id, meal_name, meal_type, totals_json")
            .eq("program_id", program_id)
            .eq("week_index", week_index % 2)
            .eq("day_index", day_index)
            .execute()
        )

        if not meals_result.data:
            logger.info("no_planned_meals_for_day", day_index=day_index)
            return []

        # Check which meals have adherence records
        skipped_records = []

        for meal in meals_result.data:
            # Check if adherence record exists
            adherence_result = (
                client.table("adherence_records")
                .select("id")
                .eq("user_id", user_id)
                .eq("date", target_date.isoformat())
                .eq("planned_ref_id", meal["id"])
                .execute()
            )

            if not adherence_result.data:
                # No adherence record = meal was skipped
                logger.info(
                    "meal_skipped",
                    meal_id=meal["id"],
                    meal_name=meal.get("meal_name"),
                )

                # Create adherence record for skipped meal
                adherence_data = {
                    "user_id": user_id,
                    "program_id": program_id,
                    "date": target_date.isoformat(),
                    "category": "nutrition",
                    "planned_ref_table": "meal_instances",
                    "planned_ref_id": meal["id"],
                    "actual_ref_table": None,
                    "actual_ref_id": None,
                    "status": "skipped",
                    "similarity_score": 0.0,
                    "details": {
                        "reason": "no_meal_logged",
                        "planned_meal": meal.get("meal_name"),
                        "meal_type": meal.get("meal_type"),
                    },
                }

                adherence_record = (
                    client.table("adherence_records").insert(adherence_data).execute()
                )

                if adherence_record.data:
                    skipped_records.append(adherence_record.data[0])

        logger.info(
            "skipped_meals_processed",
            user_id=user_id,
            date=str(target_date),
            skipped_count=len(skipped_records),
        )

        return skipped_records

    async def calculate_daily_macro_adherence(
        self, user_id: str, target_date: date
    ) -> Dict[str, Any]:
        """
        Calculate daily macro adherence summary.

        Compares total logged macros vs total planned macros for the day.

        Args:
            user_id: User UUID
            target_date: Date to calculate

        Returns:
            Dict with total_actual, total_target, variance, and adherence_pct for each macro
        """
        client = self.db.client

        logger.info(
            "calculating_daily_macro_adherence",
            user_id=user_id,
            date=str(target_date),
        )

        # Get all logged meals for the day
        meals_result = (
            client.table("meal_logs")
            .select("total_calories, total_protein_g, total_carbs_g, total_fat_g")
            .eq("user_id", user_id)
            .gte("logged_at", target_date.isoformat())
            .lt("logged_at", (target_date + timedelta(days=1)).isoformat())
            .execute()
        )

        # Sum up logged macros
        logged_totals = {
            "calories": sum(m.get("total_calories", 0) for m in meals_result.data),
            "protein_g": sum(m.get("total_protein_g", 0) for m in meals_result.data),
            "carbs_g": sum(m.get("total_carbs_g", 0) for m in meals_result.data),
            "fat_g": sum(m.get("total_fat_g", 0) for m in meals_result.data),
        }

        # Get daily targets from user's program
        program_result = (
            client.table("programs")
            .select("macros")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        if not program_result.data:
            logger.warning("no_active_program", user_id=user_id)
            return {}

        macros = program_result.data[0].get("macros", {})
        target_totals = {
            "calories": macros.get("calories_kcal", 0),
            "protein_g": macros.get("protein_g", 0),
            "carbs_g": macros.get("carbs_g", 0),
            "fat_g": macros.get("fat_g", 0),
        }

        # Calculate variance and adherence percentage
        adherence = {}

        for macro in ["calories", "protein_g", "carbs_g", "fat_g"]:
            actual = logged_totals[macro]
            target = target_totals[macro]
            variance = actual - target
            variance_pct = (variance / target * 100) if target > 0 else 0
            adherence_pct = (
                (1 - abs(variance) / target) * 100 if target > 0 else 0
            )

            adherence[macro] = {
                "actual": round(actual, 1),
                "target": round(target, 1),
                "variance": round(variance, 1),
                "variance_pct": round(variance_pct, 1),
                "adherence_pct": round(max(0, adherence_pct), 1),
            }

        logger.info(
            "daily_macro_adherence_calculated",
            user_id=user_id,
            date=str(target_date),
            overall_adherence=round(
                sum(a["adherence_pct"] for a in adherence.values()) / 4, 1
            ),
        )

        return adherence


# Import timedelta
from datetime import timedelta

# Global singleton instance
meal_matching_service = MealMatchingService()
