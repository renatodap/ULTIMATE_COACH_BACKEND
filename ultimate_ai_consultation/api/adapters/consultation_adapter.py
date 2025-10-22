"""
Consultation to UserProfile Adapter

Transforms consultation data into the UserProfile domain model used by Phase 1 generator.
This is the critical bridge between external consultation data and internal program generation.

Architecture:
- Validates consultation completeness
- Intelligently maps goals, training preferences, and availability
- Resolves ambiguity in consultation responses
- Provides sensible defaults based on user profile
"""

from typing import List, Optional, Tuple, Dict
import logging
from datetime import datetime

from ultimate_ai_consultation.api.schemas.inputs import (
    ConsultationTranscript,
    GenerationOptions,
    TrainingModalityInput,
    ImprovementGoalInput,
    TrainingAvailabilityInput,
    DifficultyInput,
    DietaryMode,
)
from ultimate_ai_consultation.services.program_generator.plan_generator import UserProfile
from ultimate_ai_consultation.libs.calculators.macros import Goal
from ultimate_ai_consultation.libs.calculators.tdee import ActivityFactor
from ultimate_ai_consultation.services.program_generator.training_generator import ExperienceLevel, IntensityZone
from ultimate_ai_consultation.services.program_generator.meal_assembler import DietaryPreference
from ultimate_ai_consultation.services.program_generator.modality_planner import (
    ModalityPreference as PlannerModalityPreference,
    FacilityAccess as PlannerFacilityAccess,
    TimeWindow as PlannerTimeWindow,
)
from ultimate_ai_consultation.services.ai.personalization import maybe_infer_primary_goal
from ultimate_ai_consultation.config import get_settings

logger = logging.getLogger(__name__)


class ConsultationValidationError(Exception):
    """Raised when consultation data is incomplete or invalid."""
    pass


class ConsultationAdapter:
    """
    Adapter between consultation data and UserProfile.
    
    Responsibilities:
    1. Validate consultation data completeness
    2. Map consultation responses to domain enums
    3. Derive missing fields from available data
    4. Apply sensible defaults based on user context
    """
    
    def __init__(self):
        """Initialize adapter with default mappings."""
        self._goal_mappings = self._build_goal_mappings()
        self._experience_mappings = self._build_experience_mappings()
        self._intensity_mappings = self._build_intensity_mappings()
        self._activity_mappings = self._build_activity_mappings()
        self._dietary_mappings = self._build_dietary_mappings()
    
    def consultation_to_user_profile(
        self,
        consultation: ConsultationTranscript,
        options: Optional[GenerationOptions] = None
    ) -> Tuple[UserProfile, List[str]]:
        """
        Transform consultation data into UserProfile.
        
        Args:
            consultation: Complete consultation transcript
            options: Generation options (optional overrides)
        
        Returns:
            (UserProfile, warnings) - Domain model and any mapping warnings
        
        Raises:
            ConsultationValidationError: If consultation data is incomplete/invalid
        """
        warnings: List[str] = []
        
        # Step 1: Validate consultation completeness
        validation_warnings = self._validate_consultation(consultation)
        warnings.extend(validation_warnings)
        
        # Step 2: Extract and map demographics (straightforward)
        demographics = consultation.demographics
        
        # Step 3: Determine primary goal from improvement goals
        primary_goal, goal_warnings = self._determine_primary_goal(
            consultation.improvement_goals,
            consultation.training_modalities
        )
        warnings.extend(goal_warnings)
        
        # Step 4: Determine training experience level
        experience_level, exp_warnings = self._determine_experience_level(
            consultation.training_modalities
        )
        warnings.extend(exp_warnings)
        
        # Step 5: Determine training focus (intensity zone)
        training_focus, focus_warnings = self._determine_training_focus(
            consultation.improvement_goals,
            consultation.training_modalities,
            primary_goal
        )
        warnings.extend(focus_warnings)
        
        # Step 6: Determine sessions per week and available days
        sessions_per_week, available_days, sched_warnings = self._determine_schedule(
            consultation.training_availability,
            consultation.difficulties,
            consultation.non_negotiables
        )
        warnings.extend(sched_warnings)
        
        # Step 7: Determine activity factor
        activity_factor, activity_warnings = self._determine_activity_factor(
            sessions_per_week,
            consultation.training_modalities,
            consultation.improvement_goals
        )
        warnings.extend(activity_warnings)
        
        # Step 8: Determine dietary preference
        dietary_pref, diet_warnings = self._determine_dietary_preference(
            consultation.typical_foods,
            options.dietary_mode if options else None
        )
        warnings.extend(diet_warnings)
        
        # Step 9: Extract food allergies from difficulties/non-negotiables
        food_allergies = self._extract_food_allergies(
            consultation.difficulties,
            consultation.non_negotiables
        )
        
        # Step 10: Determine target weight and timeline
        target_weight, timeline_weeks, goal_warnings = self._determine_goal_targets(
            consultation.improvement_goals,
            consultation.upcoming_events,
            demographics.weight_kg,
            primary_goal,
            options.program_duration_weeks if options else 12
        )
        warnings.extend(goal_warnings)
        
        # Step 11: Extract medical information
        medical_conditions, medications, injuries = self._extract_medical_info(
            consultation.difficulties,
            consultation.non_negotiables
        )
        
        # Step 12: Determine doctor clearance (conservative)
        doctor_clearance = self._determine_doctor_clearance(
            demographics.age,
            medical_conditions,
            medications
        )

        # Step 13: Map optional modality preferences and facilities
        facility_access_list = [
            PlannerFacilityAccess(
                facility_type=f.facility_type,
                days_available=f.days_available,
                notes=f.notes,
            )
            for f in (consultation.facility_access or [])
        ]
        modality_prefs_list = [
            PlannerModalityPreference(
                modality=m.modality,
                priority=m.priority,
                target_sessions_per_week=m.target_sessions_per_week,
                min_duration_minutes=m.min_duration_minutes,
                max_duration_minutes=m.max_duration_minutes,
                facility_needed=m.facility_needed,
                intensity_preference=m.intensity_preference,
                seriousness=m.seriousness,
                seriousness_score=m.seriousness_score,
                preferred_time_of_day=m.preferred_time_of_day,
            )
            for m in (consultation.modality_preferences or [])
        ]
        # Attach fixed time windows to corresponding preferences (by order)
        idx = 0
        for m in (consultation.modality_preferences or []):
            if m.fixed_time_windows:
                tws = [
                    PlannerTimeWindow(
                        day_of_week=tw.day_of_week,
                        start_hour=tw.start_hour,
                        end_hour=tw.end_hour,
                    )
                    for tw in m.fixed_time_windows
                ]
                modality_prefs_list[idx].fixed_time_windows = tws  # type: ignore[attr-defined]
            idx += 1
        
        # Build UserProfile
        profile = UserProfile(
            # Demographics
            user_id=consultation.user_id,
            age=demographics.age,
            sex_at_birth=demographics.sex_at_birth,
            weight_kg=demographics.weight_kg,
            height_cm=demographics.height_cm,
            body_fat_percentage=demographics.body_fat_percentage,
            
            # Goals
            primary_goal=primary_goal,
            target_weight_kg=target_weight,
            timeline_weeks=timeline_weeks,
            
            # Training
            sessions_per_week=sessions_per_week,
            experience_level=experience_level,
            training_focus=training_focus,
            available_days=available_days,
            
            # Nutrition
            dietary_preference=dietary_pref,
            food_allergies=food_allergies,
            
            # Activity
            activity_factor=activity_factor,
            
            # Medical/Safety
            medical_conditions=medical_conditions,
            medications=medications,
            injuries=injuries,
            doctor_clearance=doctor_clearance,
            # Multimodal
            modality_preferences=modality_prefs_list or None,
            facility_access=facility_access_list or None,
            cardio_preference=(consultation.cardio_preference or None),
            upcoming_events=[
                {
                    "event_type": e.event_type,
                    "weeks_until": e.weeks_until,
                    "event_name": e.event_name,
                }
                for e in (consultation.upcoming_events or [])
            ] or None,
        )
        
        logger.info(
            f"Consultation adapted to UserProfile: "
            f"goal={primary_goal.value}, experience={experience_level.value}, "
            f"sessions={sessions_per_week}/week, warnings={len(warnings)}"
        )
        
        return profile, warnings
    
    # ============================================================================
    # VALIDATION
    # ============================================================================
    
    def _validate_consultation(self, consultation: ConsultationTranscript) -> List[str]:
        """
        Validate consultation data completeness.
        
        Returns warnings for missing or incomplete data.
        """
        warnings = []
        
        # Demographics must be complete
        if not consultation.demographics:
            raise ConsultationValidationError("Missing demographics data")
        
        # At least one improvement goal should be present
        if not consultation.improvement_goals:
            warnings.append(
                "No improvement goals specified - defaulting to maintenance"
            )
        
        # Training modality or goal helps determine experience
        if not consultation.training_modalities and not consultation.improvement_goals:
            warnings.append(
                "No training history or goals - defaulting to beginner/intermediate"
            )
        
        # Availability is critical for scheduling
        if not consultation.training_availability:
            warnings.append(
                "No training availability specified - defaulting to 4 sessions/week"
            )
        
        return warnings
    
    # ============================================================================
    # GOAL MAPPING
    # ============================================================================
    
    def _determine_primary_goal(
        self,
        improvement_goals: List[ImprovementGoalInput],
        training_modalities: List[TrainingModalityInput]
    ) -> Tuple[Goal, List[str]]:
        """
        Determine primary fitness goal from consultation data.
        
        Priority:
        1. Highest priority improvement goal
        2. Primary training modality inference
        3. Default to maintenance
        """
        warnings = []
        
        if not improvement_goals:
            warnings.append("No goals specified - defaulting to MAINTENANCE")
            # Try AI inference if enabled
            inferred, reason = maybe_infer_primary_goal({
                "improvement_goals": [],
                "training_modalities": [m.model_dump() for m in training_modalities],
            })
            if inferred is not None:
                if reason:
                    warnings.append(f"AI inferred primary goal: {inferred.value} ({reason})")
                return inferred, warnings
            return Goal.MAINTENANCE, warnings
        
        # Find highest priority goal
        sorted_goals = sorted(improvement_goals, key=lambda g: g.priority, reverse=True)
        top_goal = sorted_goals[0]
        
        # Map goal type to Goal enum
        goal_type_lower = top_goal.goal_type.lower()
        
        if goal_type_lower in self._goal_mappings:
            mapped_goal = self._goal_mappings[goal_type_lower]
            logger.info(
                f"Mapped goal '{top_goal.goal_type}' (priority {top_goal.priority}) "
                f"to {mapped_goal.value}"
            )
            return mapped_goal, warnings
        
        # Fallback: check if goal description contains keywords
        description_lower = top_goal.description.lower()
        
        if any(kw in description_lower for kw in ["lose", "cut", "lean", "shred", "fat"]):
            warnings.append(f"Inferred FAT_LOSS from goal description")
            return Goal.FAT_LOSS, warnings
        
        if any(kw in description_lower for kw in ["gain", "muscle", "bulk", "mass", "grow"]):
            warnings.append(f"Inferred MUSCLE_GAIN from goal description")
            return Goal.MUSCLE_GAIN, warnings
        
        if any(kw in description_lower for kw in ["recomp", "body recomp", "tone"]):
            warnings.append(f"Inferred RECOMP from goal description")
            return Goal.RECOMP, warnings
        
        # If unclear, optionally query AI
        settings = get_settings()
        if settings.ENABLE_LLM_PERSONALIZATION:
            inferred, reason = maybe_infer_primary_goal({
                "top_goal": top_goal.model_dump(),
                "all_goals": [g.model_dump() for g in improvement_goals],
                "training_modalities": [m.model_dump() for m in training_modalities],
            })
            if inferred is not None:
                if reason:
                    warnings.append(f"AI inferred primary goal: {inferred.value} ({reason})")
                return inferred, warnings

        # Default to maintenance if still unclear
        warnings.append(
            f"Could not map goal type '{top_goal.goal_type}' - defaulting to MAINTENANCE"
        )
        return Goal.MAINTENANCE, warnings
    
    def _build_goal_mappings(self) -> Dict[str, Goal]:
        """Build goal type string to Goal enum mappings."""
        return {
            "fat_loss": Goal.FAT_LOSS,
            "weight_loss": Goal.FAT_LOSS,
            "cutting": Goal.FAT_LOSS,
            "shredding": Goal.FAT_LOSS,
            "muscle_gain": Goal.MUSCLE_GAIN,
            "muscle_building": Goal.MUSCLE_GAIN,
            "bulking": Goal.MUSCLE_GAIN,
            "mass_gain": Goal.MUSCLE_GAIN,
            "hypertrophy": Goal.MUSCLE_GAIN,
            "recomp": Goal.RECOMP,
            "body_recomposition": Goal.RECOMP,
            "toning": Goal.RECOMP,
            "maintenance": Goal.MAINTENANCE,
            "maintain": Goal.MAINTENANCE,
            "health": Goal.MAINTENANCE,
            "strength": Goal.MUSCLE_GAIN,  # Strength usually comes with some muscle
            "performance": Goal.MUSCLE_GAIN,
            "endurance": Goal.MAINTENANCE,  # Endurance without weight goals
        }
    
    # ============================================================================
    # EXPERIENCE LEVEL MAPPING
    # ============================================================================
    
    def _determine_experience_level(
        self,
        training_modalities: List[TrainingModalityInput]
    ) -> Tuple[ExperienceLevel, List[str]]:
        """
        Determine training experience level.
        
        Logic:
        - Use primary modality proficiency if available
        - Average years of experience across modalities
        - Default to intermediate if no data
        """
        warnings = []
        
        if not training_modalities:
            warnings.append("No training modalities - defaulting to INTERMEDIATE")
            return ExperienceLevel.INTERMEDIATE, warnings
        
        # Check for primary modality first
        primary_modalities = [m for m in training_modalities if m.is_primary]
        
        if primary_modalities:
            modality = primary_modalities[0]
            proficiency_lower = modality.proficiency.lower()
            
            if proficiency_lower in self._experience_mappings:
                level = self._experience_mappings[proficiency_lower]
                logger.info(
                    f"Mapped proficiency '{modality.proficiency}' "
                    f"({modality.years_experience} years) to {level.value}"
                )
                return level, warnings
        
        # Fallback: use max years of experience across all modalities
        max_years = max(m.years_experience for m in training_modalities)
        
        if max_years < 1:
            return ExperienceLevel.BEGINNER, warnings
        elif max_years < 3:
            return ExperienceLevel.INTERMEDIATE, warnings
        else:
            return ExperienceLevel.ADVANCED, warnings
    
    def _build_experience_mappings(self) -> Dict[str, ExperienceLevel]:
        """Build proficiency string to ExperienceLevel enum mappings."""
        return {
            "beginner": ExperienceLevel.BEGINNER,
            "novice": ExperienceLevel.BEGINNER,
            "new": ExperienceLevel.BEGINNER,
            "starting": ExperienceLevel.BEGINNER,
            "intermediate": ExperienceLevel.INTERMEDIATE,
            "moderate": ExperienceLevel.INTERMEDIATE,
            "experienced": ExperienceLevel.INTERMEDIATE,
            "advanced": ExperienceLevel.ADVANCED,
            "expert": ExperienceLevel.ADVANCED,
            "elite": ExperienceLevel.ADVANCED,
            "professional": ExperienceLevel.ADVANCED,
        }
    
    # ============================================================================
    # TRAINING FOCUS MAPPING
    # ============================================================================
    
    def _determine_training_focus(
        self,
        improvement_goals: List[ImprovementGoalInput],
        training_modalities: List[TrainingModalityInput],
        primary_goal: Goal
    ) -> Tuple[IntensityZone, List[str]]:
        """
        Determine training intensity zone (strength, hypertrophy, endurance).
        
        Logic:
        1. Check goal descriptions for explicit intensity keywords
        2. Map primary goal to typical intensity
        3. Default to hypertrophy (most versatile)
        """
        warnings = []
        
        # Check improvement goals for explicit intensity keywords
        for goal in improvement_goals:
            desc_lower = goal.description.lower()
            goal_type_lower = goal.goal_type.lower()
            
            # Check both description and goal type
            combined = f"{desc_lower} {goal_type_lower}"
            
            if any(kw in combined for kw in ["strength", "1rm", "powerlifting", "strongman"]):
                logger.info("Detected STRENGTH focus from goal keywords")
                return IntensityZone.STRENGTH, warnings
            
            if any(kw in combined for kw in ["endurance", "marathon", "cardio", "conditioning"]):
                logger.info("Detected ENDURANCE focus from goal keywords")
                return IntensityZone.ENDURANCE, warnings
        
        # Check training modalities
        for modality in training_modalities:
            mod_lower = modality.modality.lower()
            
            if mod_lower in self._intensity_mappings:
                zone = self._intensity_mappings[mod_lower]
                logger.info(f"Mapped modality '{modality.modality}' to {zone.value}")
                return zone, warnings
        
        # Map primary goal to intensity zone
        goal_to_intensity = {
            Goal.MUSCLE_GAIN: IntensityZone.HYPERTROPHY,
            Goal.FAT_LOSS: IntensityZone.HYPERTROPHY,
            Goal.RECOMP: IntensityZone.HYPERTROPHY,
            Goal.MAINTENANCE: IntensityZone.HYPERTROPHY,
        }
        
        if primary_goal in goal_to_intensity:
            zone = goal_to_intensity[primary_goal]
            warnings.append(f"Defaulted to {zone.value} based on {primary_goal.value} goal")
            return zone, warnings
        
        # Final fallback
        warnings.append("No intensity indicators - defaulting to HYPERTROPHY")
        return IntensityZone.HYPERTROPHY, warnings
    
    def _build_intensity_mappings(self) -> Dict[str, IntensityZone]:
        """Build modality string to IntensityZone enum mappings."""
        return {
            "powerlifting": IntensityZone.STRENGTH,
            "strongman": IntensityZone.STRENGTH,
            "olympic_weightlifting": IntensityZone.STRENGTH,
            "bodybuilding": IntensityZone.HYPERTROPHY,
            "physique": IntensityZone.HYPERTROPHY,
            "hypertrophy": IntensityZone.HYPERTROPHY,
            "general_fitness": IntensityZone.HYPERTROPHY,
            "crossfit": IntensityZone.HYPERTROPHY,  # Mix, but hypertrophy works
            "endurance": IntensityZone.ENDURANCE,
            "marathon": IntensityZone.ENDURANCE,
            "cycling": IntensityZone.ENDURANCE,
            "triathlon": IntensityZone.ENDURANCE,
        }
    
    # ============================================================================
    # SCHEDULE MAPPING
    # ============================================================================
    
    def _determine_schedule(
        self,
        availability: List[TrainingAvailabilityInput],
        difficulties: List[DifficultyInput],
        non_negotiables: List
    ) -> Tuple[int, List[str], List[str]]:
        """
        Determine training schedule: sessions per week and available days.
        
        Logic:
        1. Count available days from availability list
        2. Check for time constraints in difficulties
        3. Apply constraints from non-negotiables
        4. Default to 4 sessions if no data
        """
        warnings = []
        
        if not availability:
            warnings.append("No availability data - defaulting to 4 sessions/week, Mon-Fri")
            return 4, ["monday", "tuesday", "wednesday", "thursday", "friday"], warnings
        
        # Extract unique days
        available_days = sorted(list(set(
            a.day_of_week.lower() for a in availability
        )))
        
        # Check for time difficulties
        time_difficulties = [
            d for d in difficulties 
            if d.category.lower() in ["time", "schedule", "availability"]
        ]
        
        # Start with available days count
        sessions_per_week = len(available_days)
        
        # Adjust for severe time constraints
        for diff in time_difficulties:
            if diff.severity >= 7:  # Severe time constraint
                sessions_per_week = max(2, sessions_per_week - 1)
                warnings.append(
                    f"Reduced sessions due to time constraint (severity {diff.severity})"
                )
        
        # Validate sessions per week (2-6 range)
        if sessions_per_week < 2:
            warnings.append("Less than 2 days available - setting to minimum of 2")
            sessions_per_week = 2
        elif sessions_per_week > 6:
            warnings.append("More than 6 days available - capping at 6 for recovery")
            sessions_per_week = 6
        
        # Ensure available_days list has correct day names
        normalized_days = self._normalize_day_names(available_days)
        
        logger.info(
            f"Schedule determined: {sessions_per_week} sessions/week "
            f"on {', '.join(normalized_days)}"
        )
        
        return sessions_per_week, normalized_days, warnings
    
    def _normalize_day_names(self, days: List[str]) -> List[str]:
        """Normalize day names to lowercase full names."""
        day_map = {
            "mon": "monday", "monday": "monday",
            "tue": "tuesday", "tuesday": "tuesday", "tues": "tuesday",
            "wed": "wednesday", "wednesday": "wednesday",
            "thu": "thursday", "thursday": "thursday", "thur": "thursday", "thurs": "thursday",
            "fri": "friday", "friday": "friday",
            "sat": "saturday", "saturday": "saturday",
            "sun": "sunday", "sunday": "sunday",
        }
        
        normalized = []
        for day in days:
            day_lower = day.lower().strip()
            if day_lower in day_map:
                normalized.append(day_map[day_lower])
        
        return normalized if normalized else ["monday", "tuesday", "wednesday", "thursday"]
    
    # ============================================================================
    # ACTIVITY FACTOR MAPPING
    # ============================================================================
    
    def _determine_activity_factor(
        self,
        sessions_per_week: int,
        training_modalities: List[TrainingModalityInput],
        improvement_goals: List[ImprovementGoalInput]
    ) -> Tuple[ActivityFactor, List[str]]:
        """
        Determine overall physical activity level.
        
        Logic:
        1. Base activity from training sessions per week
        2. Adjust for activity-heavy modalities (e.g., crossfit, sports)
        3. Check goals for endurance/performance indicators
        """
        warnings = []
        
        # Base mapping from training sessions
        if sessions_per_week <= 2:
            base_factor = ActivityFactor.LIGHTLY_ACTIVE
        elif sessions_per_week <= 4:
            base_factor = ActivityFactor.MODERATELY_ACTIVE
        elif sessions_per_week <= 5:
            base_factor = ActivityFactor.VERY_ACTIVE
        else:
            base_factor = ActivityFactor.EXTRA_ACTIVE
        
        # Check for high-activity modalities
        high_activity_modalities = [
            "crossfit", "martial_arts", "sports", "athlete", 
            "endurance", "marathon", "cycling", "triathlon"
        ]
        
        for modality in training_modalities:
            if any(ham in modality.modality.lower() for ham in high_activity_modalities):
                # Bump up one level
                current_value = base_factor.value
                if current_value < ActivityFactor.EXTRA_ACTIVE.value:
                    upgraded = [f for f in ActivityFactor if f.value > current_value][0]
                    warnings.append(
                        f"Increased activity factor due to {modality.modality}"
                    )
                    base_factor = upgraded
                    break
        
        logger.info(
            f"Activity factor: {base_factor.name} ({base_factor.value}x) "
            f"for {sessions_per_week} sessions/week"
        )
        
        return base_factor, warnings
    
    def _build_activity_mappings(self) -> Dict[int, ActivityFactor]:
        """Build session count to ActivityFactor mappings."""
        return {
            0: ActivityFactor.SEDENTARY,
            1: ActivityFactor.LIGHTLY_ACTIVE,
            2: ActivityFactor.LIGHTLY_ACTIVE,
            3: ActivityFactor.MODERATELY_ACTIVE,
            4: ActivityFactor.MODERATELY_ACTIVE,
            5: ActivityFactor.VERY_ACTIVE,
            6: ActivityFactor.EXTRA_ACTIVE,
        }
    
    # ============================================================================
    # DIETARY PREFERENCE MAPPING
    # ============================================================================
    
    def _determine_dietary_preference(
        self,
        typical_foods: List,
        dietary_mode_override: Optional[DietaryMode]
    ) -> Tuple[DietaryPreference, List[str]]:
        """
        Determine dietary preference.
        
        Priority:
        1. Explicit dietary_mode override from options
        2. Infer from typical foods
        3. Default to NONE (flexible)
        """
        warnings = []
        
        # Check for override
        if dietary_mode_override:
            if dietary_mode_override in self._dietary_mappings:
                pref = self._dietary_mappings[dietary_mode_override]
                logger.info(f"Using dietary override: {pref.value}")
                return pref, warnings
        
        # Infer from typical foods (simple keyword check)
        if typical_foods:
            food_names = " ".join([f.food_name.lower() for f in typical_foods])
            
            has_meat = any(kw in food_names for kw in [
                "chicken", "beef", "pork", "meat", "steak", "bacon"
            ])
            has_fish = any(kw in food_names for kw in [
                "fish", "salmon", "tuna", "seafood", "shrimp"
            ])
            has_dairy = any(kw in food_names for kw in [
                "milk", "cheese", "yogurt", "whey"
            ])
            
            if not has_meat and not has_fish and not has_dairy:
                warnings.append("No animal products detected - inferring VEGAN")
                return DietaryPreference.VEGAN, warnings
            
            if not has_meat and not has_fish and has_dairy:
                warnings.append("No meat/fish but dairy detected - inferring VEGETARIAN")
                return DietaryPreference.VEGETARIAN, warnings
            
            if not has_meat and has_fish:
                warnings.append("No meat but fish detected - inferring PESCATARIAN")
                return DietaryPreference.PESCATARIAN, warnings
        
        # Default to flexible
        return DietaryPreference.NONE, warnings
    
    def _build_dietary_mappings(self) -> Dict[DietaryMode, DietaryPreference]:
        """Map DietaryMode to DietaryPreference."""
        return {
            DietaryMode.OMNIVORE: DietaryPreference.NONE,
            DietaryMode.VEGETARIAN: DietaryPreference.VEGETARIAN,
            DietaryMode.VEGAN: DietaryPreference.VEGAN,
            DietaryMode.PESCATARIAN: DietaryPreference.PESCATARIAN,
            DietaryMode.FLEXIBLE: DietaryPreference.NONE,
        }
    
    # ============================================================================
    # FOOD ALLERGIES & MEDICAL
    # ============================================================================
    
    def _extract_food_allergies(
        self,
        difficulties: List[DifficultyInput],
        non_negotiables: List
    ) -> List[str]:
        """Extract food allergies from difficulties and non-negotiables."""
        allergies = []
        
        # Check difficulties
        for diff in difficulties:
            if "allergy" in diff.description.lower() or "allergic" in diff.description.lower():
                # Try to extract allergen from description
                # Simple keyword extraction
                desc_lower = diff.description.lower()
                common_allergens = [
                    "dairy", "lactose", "milk", "nuts", "peanuts", "tree nuts",
                    "shellfish", "fish", "eggs", "soy", "wheat", "gluten"
                ]
                for allergen in common_allergens:
                    if allergen in desc_lower:
                        allergies.append(allergen)
        
        # Check non-negotiables
        for nn in non_negotiables:
            if "allergy" in nn.constraint.lower() or "cannot eat" in nn.constraint.lower():
                desc_lower = nn.constraint.lower()
                common_allergens = [
                    "dairy", "lactose", "milk", "nuts", "peanuts", "tree nuts",
                    "shellfish", "fish", "eggs", "soy", "wheat", "gluten"
                ]
                for allergen in common_allergens:
                    if allergen in desc_lower:
                        allergies.append(allergen)
        
        return list(set(allergies))  # Remove duplicates
    
    def _extract_medical_info(
        self,
        difficulties: List[DifficultyInput],
        non_negotiables: List
    ) -> Tuple[List[str], List[str], List[str]]:
        """
        Extract medical conditions, medications, and injuries.
        
        Returns:
            (medical_conditions, medications, injuries)
        """
        medical_conditions = []
        medications = []
        injuries = []
        
        # Check difficulties
        for diff in difficulties:
            category_lower = diff.category.lower()
            desc_lower = diff.description.lower()
            
            if category_lower == "injury" or "injury" in desc_lower:
                injuries.append(diff.description)
            elif "medication" in desc_lower or "prescription" in desc_lower:
                medications.append(diff.description)
            elif any(kw in desc_lower for kw in [
                "diabetes", "hypertension", "heart", "asthma", "condition"
            ]):
                medical_conditions.append(diff.description)
        
        # Check non-negotiables
        for nn in non_negotiables:
            constraint_lower = nn.constraint.lower()
            
            if "injury" in constraint_lower:
                injuries.append(nn.constraint)
            elif "medication" in constraint_lower or "doctor" in constraint_lower:
                medications.append(nn.constraint)
            elif any(kw in constraint_lower for kw in [
                "diabetes", "hypertension", "heart", "asthma", "condition"
            ]):
                medical_conditions.append(nn.constraint)
        
        return (
            list(set(medical_conditions)),
            list(set(medications)),
            list(set(injuries))
        )
    
    def _determine_doctor_clearance(
        self,
        age: int,
        medical_conditions: List[str],
        medications: List[str]
    ) -> bool:
        """
        Determine if we should assume doctor clearance.
        
        Conservative: return False if any red flags present.
        """
        # High-risk age groups
        if age < 16 or age > 65:
            return False
        
        # Any medical conditions or medications = require clearance
        if medical_conditions or medications:
            return False
        
        # Otherwise assume clearance (consultation should have screened this)
        return True
    
    # ============================================================================
    # GOAL TARGETS
    # ============================================================================
    
    def _determine_goal_targets(
        self,
        improvement_goals: List[ImprovementGoalInput],
        upcoming_events: List,
        current_weight_kg: float,
        primary_goal: Goal,
        default_timeline_weeks: int
    ) -> Tuple[Optional[float], int, List[str]]:
        """
        Determine target weight and timeline.
        
        Returns:
            (target_weight_kg, timeline_weeks, warnings)
        """
        warnings = []
        
        # Find the primary goal
        if improvement_goals:
            sorted_goals = sorted(improvement_goals, key=lambda g: g.priority, reverse=True)
            top_goal = sorted_goals[0]
            
            # Extract target weight from target_metric if present
            target_weight = None
            if top_goal.target_metric:
                # Try to parse weight from target metric
                import re
                metric_lower = top_goal.target_metric.lower()
                
                # Pattern: "75kg", "75 kg", "165 lbs", etc.
                weight_match = re.search(r'(\d+(?:\.\d+)?)\s*(kg|kgs|lbs|pounds)', metric_lower)
                if weight_match:
                    value = float(weight_match.group(1))
                    unit = weight_match.group(2)
                    
                    if unit in ["lbs", "pounds"]:
                        value = value * 0.453592  # Convert to kg
                    
                    target_weight = value
                    logger.info(f"Extracted target weight: {target_weight:.1f} kg")
            
            # Use timeline from goal if present
            timeline_weeks = top_goal.timeline_weeks or default_timeline_weeks
            
            # If no explicit target weight, infer from goal type
            if target_weight is None:
                if primary_goal == Goal.FAT_LOSS:
                    # Assume 0.5-1% bodyweight loss per week, use mid-range
                    weekly_loss = current_weight_kg * 0.0075  # 0.75% per week
                    total_loss = weekly_loss * timeline_weeks
                    target_weight = current_weight_kg - total_loss
                    warnings.append(
                        f"No target weight specified - estimated {target_weight:.1f}kg "
                        f"based on safe loss rate"
                    )
                
                elif primary_goal == Goal.MUSCLE_GAIN:
                    # Assume 0.25-0.5% bodyweight gain per week
                    weekly_gain = current_weight_kg * 0.00375  # 0.375% per week
                    total_gain = weekly_gain * timeline_weeks
                    target_weight = current_weight_kg + total_gain
                    warnings.append(
                        f"No target weight specified - estimated {target_weight:.1f}kg "
                        f"based on lean gain rate"
                    )
                
                else:
                    # Maintenance or recomp - no target weight change
                    target_weight = None
            
            return target_weight, timeline_weeks, warnings
        
        # No goals - use default timeline and no target weight
        return None, default_timeline_weeks, warnings


# ============================================================================
# PUBLIC API FUNCTIONS
# ============================================================================

def consultation_to_user_profile(
    consultation: ConsultationTranscript,
    options: Optional[GenerationOptions] = None
) -> Tuple[UserProfile, List[str]]:
    """
    Transform consultation transcript into UserProfile.
    
    This is the primary entry point for the consultation adapter.
    
    Args:
        consultation: Complete consultation transcript
        options: Optional generation options for overrides
    
    Returns:
        (UserProfile, warnings) - Domain model and any warnings
    
    Raises:
        ConsultationValidationError: If consultation data is invalid
    
    Example:
        >>> profile, warnings = consultation_to_user_profile(transcript)
        >>> if warnings:
        ...     for warning in warnings:
        ...         print(f"Warning: {warning}")
        >>> plan, plan_warnings = generator.generate_complete_plan(profile)
    """
    adapter = ConsultationAdapter()
    return adapter.consultation_to_user_profile(consultation, options)


def validate_consultation_data(consultation: ConsultationTranscript) -> List[str]:
    """
    Validate consultation data without performing full transformation.
    
    Use this for pre-validation before calling consultation_to_user_profile.
    
    Args:
        consultation: Consultation transcript to validate
    
    Returns:
        List of validation warnings (empty if fully valid)
    
    Example:
        >>> warnings = validate_consultation_data(transcript)
        >>> if warnings:
        ...     print("Consultation has issues:")
        ...     for w in warnings:
        ...         print(f"  - {w}")
    """
    adapter = ConsultationAdapter()
    return adapter._validate_consultation(consultation)
