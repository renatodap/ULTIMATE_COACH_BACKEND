"""
Onboarding Service

Business logic for onboarding flow including age derivation, macro calculation,
profile updates, and initial body metrics seeding.
"""

import structlog
from uuid import UUID
from datetime import datetime, date
from typing import Optional, Dict, Any

from app.services.macro_calculator import calculate_targets, MacroTargets
from app.services.supabase_service import supabase_service
from app.utils.logger import log_event

logger = structlog.get_logger()


class OnboardingService:
    """Service for onboarding business logic"""

    def __init__(self):
        self.supabase_service = supabase_service

    def derive_age(
        self,
        birth_date: Optional[date],
        age: Optional[int]
    ) -> int:
        """
        Derive age from birth_date or use provided age.

        Args:
            birth_date: User's birth date (optional)
            age: User's age (optional)

        Returns:
            Derived or provided age as integer

        Raises:
            ValueError: If both birth_date and age are None
        """
        if birth_date:
            today = date.today()
            derived_age = int((today - birth_date).days // 365.25)
            logger.info(
                "age_derived_from_birth_date",
                birth_date=str(birth_date),
                derived_age=derived_age
            )
            return derived_age
        elif age is not None:
            logger.info("age_provided_directly", age=age)
            return int(age)
        else:
            raise ValueError("Either birth_date or age is required")

    def calculate_macro_targets(
        self,
        age: int,
        biological_sex: str,
        height_cm: float,
        current_weight_kg: float,
        goal_weight_kg: float,
        activity_level: str,
        primary_goal: str,
        experience_level: str,
        user_id: Optional[UUID] = None
    ) -> MacroTargets:
        """
        Calculate macro targets for user.

        Args:
            age: User's age
            biological_sex: 'male' or 'female'
            height_cm: Height in centimeters
            current_weight_kg: Current weight in kg
            goal_weight_kg: Goal weight in kg
            activity_level: Activity level string
            primary_goal: Primary fitness goal
            experience_level: Training experience level
            user_id: Optional user ID for logging

        Returns:
            MacroTargets object with calculations
        """
        log_event(
            "onboarding_macro_calculation_started",
            user_id=str(user_id) if user_id else None,
            primary_goal=primary_goal,
            activity_level=activity_level
        )

        targets = calculate_targets(
            age=age,
            sex=biological_sex,
            height_cm=height_cm,
            current_weight_kg=current_weight_kg,
            goal_weight_kg=goal_weight_kg,
            activity_level=activity_level,
            primary_goal=primary_goal,
            experience_level=experience_level
        )

        log_event(
            "onboarding_macro_calculation_completed",
            user_id=str(user_id) if user_id else None,
            bmr=targets.bmr,
            tdee=targets.tdee,
            calories=targets.daily_calories,
            protein=targets.daily_protein_g,
            carbs=targets.daily_carbs_g,
            fat=targets.daily_fat_g
        )

        return targets

    def prepare_profile_update(
        self,
        onboarding_data: Dict[str, Any],
        targets: MacroTargets
    ) -> Dict[str, Any]:
        """
        Prepare profile update dictionary from onboarding data and calculated targets.

        Args:
            onboarding_data: Raw onboarding data dictionary
            targets: Calculated macro targets

        Returns:
            Dictionary ready for profile update
        """
        profile_update = {
            # Physical stats
            'biological_sex': onboarding_data['biological_sex'],
            'height_cm': onboarding_data['height_cm'],
            'current_weight_kg': onboarding_data['current_weight_kg'],
            'goal_weight_kg': onboarding_data['goal_weight_kg'],

            # Goals
            'primary_goal': onboarding_data['primary_goal'],
            'secondary_goal': onboarding_data.get('secondary_goal'),  # Optional secondary goal
            'experience_level': onboarding_data['experience_level'],
            'fitness_notes': onboarding_data.get('fitness_notes'),  # Optional fitness notes

            # Activity & Lifestyle
            'activity_level': onboarding_data['activity_level'],
            'workout_frequency': onboarding_data['workout_frequency'],
            'sleep_hours': onboarding_data['sleep_hours'],
            'stress_level': onboarding_data['stress_level'],

            # Dietary
            'dietary_preference': onboarding_data['dietary_preference'],
            'food_allergies': onboarding_data.get('food_allergies', []),
            'foods_to_avoid': onboarding_data.get('foods_to_avoid', []),
            'meals_per_day': onboarding_data.get('meals_per_day', 3),
            'cooks_regularly': onboarding_data.get('cooks_regularly', True),

            # Calculated targets
            'estimated_tdee': targets.tdee,
            'daily_calorie_goal': targets.daily_calories,
            'daily_protein_goal': targets.daily_protein_g,
            'daily_carbs_goal': targets.daily_carbs_g,
            'daily_fat_goal': targets.daily_fat_g,

            # Preferences
            'unit_system': onboarding_data.get('unit_system', 'imperial'),
            'timezone': onboarding_data.get('timezone', 'America/New_York'),

            # Onboarding status
            'onboarding_completed': True,
            'onboarding_completed_at': datetime.utcnow().isoformat(),

            # Macro metadata
            'macros_last_calculated_at': datetime.utcnow().isoformat(),
            'macros_calculation_reason': 'initial_onboarding',
        }

        # Add optional fields if present
        if 'birth_date' in onboarding_data and onboarding_data['birth_date']:
            if isinstance(onboarding_data['birth_date'], date):
                profile_update['birth_date'] = onboarding_data['birth_date'].isoformat()
            else:
                profile_update['birth_date'] = onboarding_data['birth_date']

        if 'age' in onboarding_data and onboarding_data['age'] is not None:
            profile_update['age'] = onboarding_data['age']

        logger.info(
            "profile_update_prepared",
            field_count=len(profile_update),
            has_birth_date='birth_date' in profile_update,
            has_age='age' in profile_update
        )

        return profile_update

    async def save_training_modalities(
        self,
        user_id: UUID,
        training_modalities: list[Dict[str, Any]],
        user_token: Optional[str] = None
    ) -> bool:
        """
        Save user's selected training modalities to user_training_modalities table.

        Args:
            user_id: User UUID
            training_modalities: List of training modality selections
                                Each item should have: modality_id, proficiency_level, is_primary
            user_token: Optional JWT token for RLS

        Returns:
            True if successful, False if failed (non-critical)
        """
        if not training_modalities:
            logger.info(
                "no_training_modalities_to_save",
                user_id=str(user_id)
            )
            return True

        try:
            # Prepare records for bulk insert
            records = []
            for modality in training_modalities:
                records.append({
                    'user_id': str(user_id),
                    'modality_id': modality['modality_id'],
                    'proficiency_level': modality['proficiency_level'],
                    'is_primary': modality.get('is_primary', False),
                    'willing_to_continue': True,
                })

            # Bulk insert training modalities
            result = self.supabase_service.client.table('user_training_modalities').insert(records).execute()

            if result.data:
                log_event(
                    "onboarding_training_modalities_saved",
                    user_id=str(user_id),
                    modality_count=len(records)
                )
                return True
            else:
                log_event(
                    "onboarding_training_modalities_save_failed",
                    level="warn",
                    user_id=str(user_id),
                    error="No data returned from insert"
                )
                return False

        except Exception as e:
            log_event(
                "onboarding_training_modalities_save_error",
                level="warn",
                user_id=str(user_id),
                error=str(e),
                modality_count=len(training_modalities)
            )
            return False

    async def seed_initial_body_metrics(
        self,
        user_id: UUID,
        weight_kg: float,
        height_cm: float,
        user_token: Optional[str] = None
    ) -> bool:
        """
        Create initial body metrics record from onboarding data.

        Args:
            user_id: User UUID
            weight_kg: Initial weight
            height_cm: Initial height
            user_token: Optional JWT token for RLS

        Returns:
            True if successful, False if failed (non-critical)
        """
        try:
            await self.supabase_service.create_body_metric({
                'user_id': str(user_id),
                'recorded_at': datetime.utcnow().isoformat(),
                'weight_kg': weight_kg,
                'height_cm': height_cm,
                'notes': 'Initial metrics from onboarding'
            }, user_token=user_token)

            log_event(
                "onboarding_body_metrics_seeded",
                user_id=str(user_id),
                weight_kg=weight_kg,
                height_cm=height_cm
            )
            return True

        except Exception as e:
            log_event(
                "onboarding_body_metrics_seed_failed",
                level="warn",
                user_id=str(user_id),
                error=str(e)
            )
            return False

    async def complete_onboarding(
        self,
        user_id: UUID,
        onboarding_data: Dict[str, Any],
        user_token: Optional[str] = None
    ) -> tuple[Dict[str, Any], MacroTargets]:
        """
        Complete full onboarding flow.

        Process:
        1. Derive age from birth_date or use provided age
        2. Calculate macro targets
        3. Prepare profile update
        4. Update user profile
        5. Seed initial body metrics

        Args:
            user_id: User UUID
            onboarding_data: Complete onboarding data dictionary
            user_token: Optional JWT token for RLS

        Returns:
            Tuple of (updated_profile, macro_targets)

        Raises:
            ValueError: If validation fails
            HTTPException: If profile update fails
        """
        log_event(
            "onboarding_request_received",
            user_id=str(user_id),
            primary_goal=onboarding_data.get('primary_goal'),
            experience_level=onboarding_data.get('experience_level'),
            activity_level=onboarding_data.get('activity_level')
        )

        # Step 1: Derive age
        age = self.derive_age(
            onboarding_data.get('birth_date'),
            onboarding_data.get('age')
        )

        # Step 2: Calculate macro targets
        targets = self.calculate_macro_targets(
            age=age,
            biological_sex=onboarding_data['biological_sex'],
            height_cm=onboarding_data['height_cm'],
            current_weight_kg=onboarding_data['current_weight_kg'],
            goal_weight_kg=onboarding_data['goal_weight_kg'],
            activity_level=onboarding_data['activity_level'],
            primary_goal=onboarding_data['primary_goal'],
            experience_level=onboarding_data['experience_level'],
            user_id=user_id
        )

        # Step 3: Prepare profile update
        profile_update = self.prepare_profile_update(onboarding_data, targets)

        # Step 4: Update profile
        updated_profile = await self.supabase_service.update_profile(
            user_id,
            profile_update,
            user_token=user_token
        )

        if not updated_profile:
            log_event("onboarding_profile_update_failed", user_id=str(user_id))
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update profile"
            )

        log_event(
            "onboarding_profile_updated",
            user_id=str(user_id),
            updated_fields=list(profile_update.keys()),
            onboarding_completed=True
        )

        # Step 5: Save training modalities (non-critical)
        training_modalities = onboarding_data.get('training_modalities', [])
        if training_modalities:
            await self.save_training_modalities(
                user_id,
                training_modalities,
                user_token=user_token
            )

        # Step 6: Seed initial body metrics (non-critical)
        await self.seed_initial_body_metrics(
            user_id,
            onboarding_data['current_weight_kg'],
            onboarding_data['height_cm'],
            user_token=user_token
        )

        log_event(
            "onboarding_completed",
            user_id=str(user_id),
            primary_goal=onboarding_data['primary_goal'],
            secondary_goal=onboarding_data.get('secondary_goal'),
            daily_calories=targets.daily_calories,
            has_fitness_notes=bool(onboarding_data.get('fitness_notes')),
            training_modalities_count=len(training_modalities)
        )

        return updated_profile, targets


# Singleton instance
onboarding_service = OnboardingService()
