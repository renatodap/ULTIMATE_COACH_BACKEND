"""
Profile Service

Business logic for user profile operations including macro recalculation.
Separates business logic from route handlers for better testability.
"""

import structlog
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any

from app.services.macro_calculator import calculate_targets

logger = structlog.get_logger()


class ProfileService:
    """Service for user profile business logic"""

    # Fields that trigger macro recalculation when changed
    MACRO_AFFECTING_FIELDS = {
        'age', 'height_cm', 'current_weight_kg', 'goal_weight_kg',
        'primary_goal', 'activity_level', 'experience_level'
    }

    def should_recalculate_macros(self, update_data: Dict[str, Any]) -> bool:
        """
        Check if update contains fields that require macro recalculation.

        Args:
            update_data: Dictionary of profile fields being updated

        Returns:
            True if macro recalculation is needed
        """
        return any(field in update_data for field in self.MACRO_AFFECTING_FIELDS)

    def recalculate_macros(
        self,
        current_profile: Dict[str, Any],
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Recalculate user macros based on profile changes.

        Uses updated values when provided, falls back to current profile values.
        Adds macro targets and calculation metadata to update_data.

        Args:
            current_profile: Current profile data from database
            update_data: Dictionary of fields being updated

        Returns:
            Updated update_data with macro calculations added

        Raises:
            ValueError: If required fields for macro calculation are missing
        """
        # Get values (updated or current)
        calc_age = update_data.get('age', current_profile.get('age'))
        calc_sex = current_profile.get('biological_sex')
        calc_height = update_data.get('height_cm', current_profile.get('height_cm'))
        calc_current_weight = update_data.get('current_weight_kg', current_profile.get('current_weight_kg'))
        calc_goal_weight = update_data.get('goal_weight_kg', current_profile.get('goal_weight_kg'))
        calc_activity = update_data.get('activity_level', current_profile.get('activity_level'))
        calc_goal = update_data.get('primary_goal', current_profile.get('primary_goal'))
        calc_experience = update_data.get('experience_level', current_profile.get('experience_level'))

        # Validate required fields
        if not all([calc_age, calc_sex, calc_height, calc_current_weight,
                   calc_goal_weight, calc_activity, calc_goal]):
            missing_fields = []
            if not calc_age:
                missing_fields.append('age')
            if not calc_sex:
                missing_fields.append('biological_sex')
            if not calc_height:
                missing_fields.append('height_cm')
            if not calc_current_weight:
                missing_fields.append('current_weight_kg')
            if not calc_goal_weight:
                missing_fields.append('goal_weight_kg')
            if not calc_activity:
                missing_fields.append('activity_level')
            if not calc_goal:
                missing_fields.append('primary_goal')

            logger.warning(
                "missing_fields_for_macro_calculation",
                missing_fields=missing_fields,
                profile_id=current_profile.get('id')
            )

            raise ValueError(
                f"Missing required fields for macro calculation: {', '.join(missing_fields)}"
            )

        # Recalculate macros
        logger.info(
            "recalculating_macros",
            age=calc_age,
            sex=calc_sex,
            height=calc_height,
            current_weight=calc_current_weight,
            goal_weight=calc_goal_weight,
            activity=calc_activity,
            goal=calc_goal,
            experience=calc_experience
        )

        targets = calculate_targets(
            age=calc_age,
            sex=calc_sex,
            height_cm=calc_height,
            current_weight_kg=calc_current_weight,
            goal_weight_kg=calc_goal_weight,
            activity_level=calc_activity,
            primary_goal=calc_goal,
            experience_level=calc_experience
        )

        # Add macro targets to update
        macro_updates = {
            "estimated_tdee": targets.tdee,
            "daily_calorie_goal": targets.daily_calories,
            "daily_protein_goal": targets.daily_protein_g,
            "daily_carbs_goal": targets.daily_carbs_g,
            "daily_fat_goal": targets.daily_fat_g,
            "macros_last_calculated_at": datetime.utcnow().isoformat(),
            "macros_calculation_reason": "profile_update"
        }

        logger.info(
            "macros_recalculated",
            calories=targets.daily_calories,
            protein=targets.daily_protein_g,
            carbs=targets.daily_carbs_g,
            fat=targets.daily_fat_g,
            tdee=targets.tdee
        )

        # Merge macro updates into update_data
        update_data.update(macro_updates)

        return update_data


# Singleton instance
profile_service = ProfileService()
