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
        birth_date: Optional[date]
    ) -> int:
        """
        Derive age from birth_date ONLY.

        CRITICAL: Age must ALWAYS be calculated from birth_date, never accepted as input.
        This ensures age accuracy and automatic updates on birthdays.

        Args:
            birth_date: User's birth date (REQUIRED)

        Returns:
            Derived age as integer

        Raises:
            ValueError: If birth_date is None
        """
        if not birth_date:
            raise ValueError("birth_date is required to calculate age")

        today = date.today()
        derived_age = int((today - birth_date).days // 365.25)

        # Validate reasonable age range
        if derived_age < 13 or derived_age > 120:
            raise ValueError(f"Derived age ({derived_age}) must be between 13 and 120. Please check birth_date.")

        logger.info(
            "age_derived_from_birth_date",
            birth_date=str(birth_date),
            derived_age=derived_age
        )
        return derived_age

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

        # Add birth_date if present
        # CRITICAL: We store birth_date, NOT age. Age is calculated dynamically.
        if 'birth_date' in onboarding_data and onboarding_data['birth_date']:
            if isinstance(onboarding_data['birth_date'], date):
                profile_update['birth_date'] = onboarding_data['birth_date'].isoformat()
            else:
                profile_update['birth_date'] = onboarding_data['birth_date']

        # NOTE: We do NOT store 'age' in the database.
        # Age is derived from birth_date on every read to ensure accuracy.

        logger.info(
            "profile_update_prepared",
            field_count=len(profile_update),
            has_birth_date='birth_date' in profile_update
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

        IMPORTANT: This is now a CRITICAL operation. If user selects modalities,
        they MUST be saved for personalized recommendations.

        Args:
            user_id: User UUID
            training_modalities: List of training modality selections
                                Each item should have: modality_id, proficiency_level, is_primary
            user_token: Optional JWT token for RLS

        Returns:
            True if successful, raises exception if critical failure

        Raises:
            Exception: If modalities were selected but failed to save
        """
        if not training_modalities:
            log_event(
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
                # CRITICAL: User selected modalities but save failed
                log_event(
                    "onboarding_training_modalities_save_failed",
                    level="error",
                    user_id=str(user_id),
                    error="No data returned from insert",
                    modality_count=len(records)
                )
                raise Exception("Failed to save training modalities - no data returned")

        except Exception as e:
            log_event(
                "onboarding_training_modalities_save_error",
                level="error",
                user_id=str(user_id),
                error=str(e),
                modality_count=len(training_modalities)
            )
            # Re-raise to fail onboarding if modalities can't be saved
            raise Exception(f"Failed to save training modalities: {str(e)}")

    async def save_exercise_familiarity(
        self,
        user_id: UUID,
        exercise_familiarity: list[Dict[str, Any]],
        user_token: Optional[str] = None
    ) -> bool:
        """Save user's exercise familiarity to user_familiar_exercises table."""
        if not exercise_familiarity:
            return True

        try:
            records = []
            for entry in exercise_familiarity:
                records.append({
                    'user_id': str(user_id),
                    'exercise_id': entry['exercise_id'],
                    'comfort_level': entry['comfort_level'],
                    'typical_weight_kg': entry.get('typical_weight_kg'),
                    'typical_reps': entry.get('typical_reps'),
                    'typical_duration_minutes': entry.get('typical_duration_minutes'),
                    'frequency': entry.get('frequency'),
                    'enjoys_it': entry.get('enjoys_it'),
                    'source': 'onboarding'
                })

            result = self.supabase_service.client.table('user_familiar_exercises').insert(records).execute()
            if result.data:
                log_event("onboarding_exercise_familiarity_saved", user_id=str(user_id), count=len(records))
                return True
            raise Exception("No data returned from insert")

        except Exception as e:
            log_event("onboarding_exercise_familiarity_save_error", level="error", user_id=str(user_id), error=str(e))
            return False  # Non-critical

    async def save_training_availability(
        self,
        user_id: UUID,
        training_availability: list[Dict[str, Any]],
        user_token: Optional[str] = None
    ) -> bool:
        """Save user's training availability to user_training_availability table."""
        if not training_availability:
            return True

        try:
            records = []
            for entry in training_availability:
                records.append({
                    'user_id': str(user_id),
                    'day_of_week': entry['day_of_week'],
                    'time_of_day': entry['time_of_day'],
                    'typical_duration_minutes': entry['typical_duration_minutes'],
                    'location_type': entry['location_type'],
                    'is_preferred': entry.get('is_preferred', False)
                })

            result = self.supabase_service.client.table('user_training_availability').insert(records).execute()
            if result.data:
                log_event("onboarding_training_availability_saved", user_id=str(user_id), count=len(records))
                return True
            raise Exception("No data returned from insert")

        except Exception as e:
            log_event("onboarding_training_availability_save_error", level="error", user_id=str(user_id), error=str(e))
            return False  # Non-critical

    async def save_meal_timing_preferences(
        self,
        user_id: UUID,
        meal_timing_preferences: list[Dict[str, Any]],
        user_token: Optional[str] = None
    ) -> bool:
        """Save user's meal timing preferences to user_preferred_meal_times table."""
        if not meal_timing_preferences:
            return True

        try:
            records = []
            for entry in meal_timing_preferences:
                records.append({
                    'user_id': str(user_id),
                    'meal_time_id': entry['meal_time_id'],
                    'typical_portion_size': entry['typical_portion_size'],
                    'flexibility_minutes': entry.get('flexibility_minutes', 30),
                    'is_non_negotiable': entry.get('is_non_negotiable', False)
                })

            result = self.supabase_service.client.table('user_preferred_meal_times').insert(records).execute()
            if result.data:
                log_event("onboarding_meal_timing_saved", user_id=str(user_id), count=len(records))
                return True
            raise Exception("No data returned from insert")

        except Exception as e:
            log_event("onboarding_meal_timing_save_error", level="error", user_id=str(user_id), error=str(e))
            return False  # Non-critical

    async def save_typical_foods(
        self,
        user_id: UUID,
        typical_foods: list[Dict[str, Any]],
        user_token: Optional[str] = None
    ) -> bool:
        """Save user's typical foods to user_typical_meal_foods table."""
        if not typical_foods:
            return True

        try:
            records = []
            for entry in typical_foods:
                records.append({
                    'user_id': str(user_id),
                    'food_id': entry['food_id'],
                    'meal_time_id': entry.get('meal_time_id'),
                    'frequency': entry['frequency'],
                    'typical_quantity_grams': entry.get('typical_quantity_grams'),
                    'typical_serving_id': entry.get('typical_serving_id')
                })

            result = self.supabase_service.client.table('user_typical_meal_foods').insert(records).execute()
            if result.data:
                log_event("onboarding_typical_foods_saved", user_id=str(user_id), count=len(records))
                return True
            raise Exception("No data returned from insert")

        except Exception as e:
            log_event("onboarding_typical_foods_save_error", level="error", user_id=str(user_id), error=str(e))
            return False  # Non-critical

    async def save_upcoming_events(
        self,
        user_id: UUID,
        upcoming_events: list[Dict[str, Any]],
        user_token: Optional[str] = None
    ) -> bool:
        """Save user's upcoming events to user_upcoming_events table."""
        if not upcoming_events:
            return True

        try:
            records = []
            for entry in upcoming_events:
                record = {
                    'user_id': str(user_id),
                    'event_type_id': entry.get('event_type_id'),
                    'event_name': entry['event_name'],
                    'event_date': entry.get('event_date'),
                    'priority': entry.get('priority', 3),
                    'specific_goals': entry.get('specific_goals', [])
                }
                # Convert date to string if needed
                if record['event_date'] and isinstance(record['event_date'], date):
                    record['event_date'] = record['event_date'].isoformat()
                records.append(record)

            result = self.supabase_service.client.table('user_upcoming_events').insert(records).execute()
            if result.data:
                log_event("onboarding_upcoming_events_saved", user_id=str(user_id), count=len(records))
                return True
            raise Exception("No data returned from insert")

        except Exception as e:
            log_event("onboarding_upcoming_events_save_error", level="error", user_id=str(user_id), error=str(e))
            return False  # Non-critical

    async def save_improvement_goals(
        self,
        user_id: UUID,
        improvement_goals: list[Dict[str, Any]],
        user_token: Optional[str] = None
    ) -> bool:
        """Save user's improvement goals to user_improvement_goals table."""
        if not improvement_goals:
            return True

        try:
            records = []
            for entry in improvement_goals:
                record = {
                    'user_id': str(user_id),
                    'goal_type': entry['goal_type'],
                    'target_description': entry['target_description'],
                    'current_value': entry.get('current_value'),
                    'target_value': entry.get('target_value'),
                    'target_date': entry.get('target_date'),
                    'exercise_id': entry.get('exercise_id')
                }
                # Convert date to string if needed
                if record['target_date'] and isinstance(record['target_date'], date):
                    record['target_date'] = record['target_date'].isoformat()
                records.append(record)

            result = self.supabase_service.client.table('user_improvement_goals').insert(records).execute()
            if result.data:
                log_event("onboarding_improvement_goals_saved", user_id=str(user_id), count=len(records))
                return True
            raise Exception("No data returned from insert")

        except Exception as e:
            log_event("onboarding_improvement_goals_save_error", level="error", user_id=str(user_id), error=str(e))
            return False  # Non-critical

    async def save_difficulties(
        self,
        user_id: UUID,
        difficulties: list[Dict[str, Any]],
        user_token: Optional[str] = None
    ) -> bool:
        """Save user's difficulties to user_difficulties table."""
        if not difficulties:
            return True

        try:
            records = []
            for entry in difficulties:
                records.append({
                    'user_id': str(user_id),
                    'difficulty_category': entry['difficulty_category'],
                    'description': entry['description'],
                    'severity': entry.get('severity', 3),
                    'frequency': entry.get('frequency')
                })

            result = self.supabase_service.client.table('user_difficulties').insert(records).execute()
            if result.data:
                log_event("onboarding_difficulties_saved", user_id=str(user_id), count=len(records))
                return True
            raise Exception("No data returned from insert")

        except Exception as e:
            log_event("onboarding_difficulties_save_error", level="error", user_id=str(user_id), error=str(e))
            return False  # Non-critical

    async def save_non_negotiables(
        self,
        user_id: UUID,
        non_negotiables: list[Dict[str, Any]],
        user_token: Optional[str] = None
    ) -> bool:
        """Save user's non-negotiables to user_non_negotiables table."""
        if not non_negotiables:
            return True

        try:
            records = []
            for entry in non_negotiables:
                records.append({
                    'user_id': str(user_id),
                    'constraint_type': entry['constraint_type'],
                    'description': entry['description'],
                    'reason': entry.get('reason'),
                    'excluded_exercise_ids': entry.get('excluded_exercise_ids', []),
                    'excluded_food_ids': entry.get('excluded_food_ids', [])
                })

            result = self.supabase_service.client.table('user_non_negotiables').insert(records).execute()
            if result.data:
                log_event("onboarding_non_negotiables_saved", user_id=str(user_id), count=len(records))
                return True
            raise Exception("No data returned from insert")

        except Exception as e:
            log_event("onboarding_non_negotiables_save_error", level="error", user_id=str(user_id), error=str(e))
            return False  # Non-critical

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

        # Step 1: Derive age from birth_date ONLY
        # CRITICAL: We ignore any 'age' field sent by frontend
        age = self.derive_age(onboarding_data.get('birth_date'))

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

        # Step 5: Save training modalities (critical if provided)
        training_modalities = onboarding_data.get('training_modalities', [])
        if training_modalities:
            await self.save_training_modalities(
                user_id,
                training_modalities,
                user_token=user_token
            )

        # Step 6: Save consultation data (all non-critical, skippable)
        # Phase 2: Training Background
        await self.save_exercise_familiarity(
            user_id,
            onboarding_data.get('exercise_familiarity', []),
            user_token=user_token
        )
        await self.save_training_availability(
            user_id,
            onboarding_data.get('training_availability', []),
            user_token=user_token
        )

        # Phase 3: Nutrition Profile
        await self.save_meal_timing_preferences(
            user_id,
            onboarding_data.get('meal_timing_preferences', []),
            user_token=user_token
        )
        await self.save_typical_foods(
            user_id,
            onboarding_data.get('typical_foods', []),
            user_token=user_token
        )

        # Phase 4: Goals & Context
        await self.save_upcoming_events(
            user_id,
            onboarding_data.get('upcoming_events', []),
            user_token=user_token
        )
        await self.save_improvement_goals(
            user_id,
            onboarding_data.get('improvement_goals', []),
            user_token=user_token
        )
        await self.save_difficulties(
            user_id,
            onboarding_data.get('difficulties', []),
            user_token=user_token
        )
        await self.save_non_negotiables(
            user_id,
            onboarding_data.get('non_negotiables', []),
            user_token=user_token
        )

        # Step 7: Seed initial body metrics (non-critical)
        await self.seed_initial_body_metrics(
            user_id,
            onboarding_data['current_weight_kg'],
            onboarding_data['height_cm'],
            user_token=user_token
        )

        # Count consultation data entries for logging
        consultation_counts = {
            'exercise_familiarity': len(onboarding_data.get('exercise_familiarity', [])),
            'training_availability': len(onboarding_data.get('training_availability', [])),
            'meal_timing_preferences': len(onboarding_data.get('meal_timing_preferences', [])),
            'typical_foods': len(onboarding_data.get('typical_foods', [])),
            'upcoming_events': len(onboarding_data.get('upcoming_events', [])),
            'improvement_goals': len(onboarding_data.get('improvement_goals', [])),
            'difficulties': len(onboarding_data.get('difficulties', [])),
            'non_negotiables': len(onboarding_data.get('non_negotiables', []))
        }

        log_event(
            "onboarding_completed",
            user_id=str(user_id),
            primary_goal=onboarding_data['primary_goal'],
            secondary_goal=onboarding_data.get('secondary_goal'),
            daily_calories=targets.daily_calories,
            has_fitness_notes=bool(onboarding_data.get('fitness_notes')),
            training_modalities_count=len(training_modalities),
            consultation_data_counts=consultation_counts
        )

        return updated_profile, targets


# Singleton instance
onboarding_service = OnboardingService()
