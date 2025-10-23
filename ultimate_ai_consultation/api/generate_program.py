"""
Main Program Generation API

This is the primary entry point for generating complete training and nutrition programs
from consultation data. It orchestrates the entire pipeline:

1. Validate consultation data
2. Transform to UserProfile (via adapter)
3. Generate complete program (via Phase 1 generator)
4. Transform to output schema
5. Add metadata and versioning

This function is designed to be called by external systems (FastAPI endpoints,
background workers, etc.) and provides a clean, type-safe interface.
"""

from typing import Tuple, List, Optional
from datetime import datetime
import logging

from ultimate_ai_consultation.api.schemas.inputs import ConsultationTranscript, GenerationOptions
from ultimate_ai_consultation.api.schemas.outputs import (
    ProgramBundle,
    TrainingPlan,
    NutritionPlan,
    SafetyReport,
    FeasibilityReport,
    MultimodalSession,
    MultimodalInterval,
    MultimodalDrill,
)
from ultimate_ai_consultation.api.schemas.meta import ProgramVersion, Provenance
from ultimate_ai_consultation.services.ai.personalization import explain_tradeoffs
from ultimate_ai_consultation.config import get_settings
from ultimate_ai_consultation.api.adapters import consultation_to_user_profile, validate_consultation_data, ConsultationValidationError
from ultimate_ai_consultation.services.program_generator import PlanGenerator
from ultimate_ai_consultation.services.program_generator.plan_generator import CompletePlan

logger = logging.getLogger(__name__)


class ProgramGenerationError(Exception):
    """Raised when program generation fails for any reason."""
    pass


def generate_program_from_consultation(
    consultation: ConsultationTranscript,
    options: Optional[GenerationOptions] = None,
) -> Tuple[ProgramBundle, List[str]]:
    """
    Generate a complete training and nutrition program from consultation data.
    
    This is the main API function that orchestrates the entire generation pipeline.
    
    Args:
        consultation: Complete consultation transcript with user data
        options: Optional generation options for customization
    
    Returns:
        (ProgramBundle, warnings) - Complete program package and any warnings
    
    Raises:
        ConsultationValidationError: If consultation data is invalid
        ProgramGenerationError: If program generation fails
    
    Example:
        >>> from api.schemas.inputs import ConsultationTranscript, UserDemographics
        >>> consultation = ConsultationTranscript(...)
        >>> program, warnings = generate_program_from_consultation(consultation)
        >>> print(f"Program ID: {program.program_id}")
        >>> print(f"Training: {len(program.training_plan.weekly_sessions)} sessions/week")
        >>> print(f"Nutrition: {len(program.nutrition_plan.daily_meal_plans)} days")
    """
    warnings: List[str] = []
    
    logger.info(
        f"Starting program generation for user_id={consultation.user_id}, "
        f"session_id={consultation.session_id}"
    )
    
    try:
        # Step 1: Validate consultation data
        validation_warnings = validate_consultation_data(consultation)
        warnings.extend(validation_warnings)
        
        if validation_warnings:
            logger.warning(
                f"Consultation validation warnings: {len(validation_warnings)} issues found"
            )
        
        # Step 2: Transform consultation to UserProfile
        logger.info("Transforming consultation to UserProfile")
        user_profile, adapter_warnings = consultation_to_user_profile(consultation, options)
        warnings.extend(adapter_warnings)
        
        if adapter_warnings:
            logger.warning(
                f"Adapter transformation warnings: {len(adapter_warnings)} issues found"
            )
        
        # Step 3: Generate complete program using Phase 1 generator
        logger.info("Generating complete program with Phase 1 generator")
        generator = PlanGenerator()
        
        try:
            complete_plan, generator_warnings = generator.generate_complete_plan(
                profile=user_profile,
                plan_version=1,
                meals_per_day=(options.meals_per_day if options else 3),
            )
            warnings.extend(generator_warnings)
            
            if generator_warnings:
                logger.warning(
                    f"Program generation warnings: {len(generator_warnings)} issues found"
                )
        
        except ValueError as e:
            # Generator raises ValueError for infeasible/unsafe plans
            logger.error(f"Program generation failed: {e}")
            raise ProgramGenerationError(f"Cannot generate safe/feasible program: {e}")
        
        # Step 4: Transform to output schema (ProgramBundle)
        logger.info("Transforming to output schema")
        program_bundle = _transform_to_program_bundle(
            complete_plan=complete_plan,
            consultation=consultation,
            options=options,
            warnings=warnings
        )
        
        logger.info(
            f"Program generation complete: program_id={program_bundle.program_id}, "
            f"warnings={len(warnings)}"
        )
        
        return program_bundle, warnings
    
    except ConsultationValidationError:
        # Re-raise validation errors as-is
        raise
    
    except ProgramGenerationError:
        # Re-raise generation errors as-is
        raise
    
    except Exception as e:
        # Wrap unexpected errors
        logger.exception(f"Unexpected error during program generation: {e}")
        raise ProgramGenerationError(f"Unexpected error: {e}")


def _transform_to_program_bundle(
    complete_plan: CompletePlan,
    consultation: ConsultationTranscript,
    options: Optional[GenerationOptions],
    warnings: List[str]
) -> ProgramBundle:
    """
    Transform internal CompletePlan to external ProgramBundle schema.
    
    This function bridges the internal generator output with the public API schema.
    """
    from ultimate_ai_consultation.services.program_generator.plan_generator import UserProfile
    
    # Transform training program
    training_plan = _transform_training_plan(complete_plan, consultation)
    
    # Transform nutrition plan
    nutrition_plan = _transform_nutrition_plan(complete_plan)
    
    # Build safety report
    safety_report = SafetyReport(
        passed=complete_plan.safety_result.passed,
        level=complete_plan.safety_result.level.value,
        issues=[],  # TODO: Extract from violations
        # Optional fields use defaults:
        # modifications_applied=None
        # requires_medical_clearance=False
        # requires_trainer_supervision=False
        # validated_at=datetime.now()
    )
    
    # Build feasibility report
    feasibility_report = FeasibilityReport(
        feasible=complete_plan.feasibility_result.feasible,
        status=complete_plan.feasibility_result.status.value,
        runtime_ms=complete_plan.feasibility_result.runtime_ms,
        iterations=complete_plan.feasibility_result.iterations,
        optimal_params=complete_plan.feasibility_result.optimal_params,
        diagnostics=None,  # TODO: Transform diagnostics if needed
        trade_off_options=[
            {
                "description": option.description,
                "impact": "medium",  # TODO: Add impact to TradeOff
            }
            for option in (complete_plan.feasibility_result.trade_offs or [])
        ] if complete_plan.feasibility_result.trade_offs else None,
        # validated_at uses default (datetime.now())
    )

    # Optional: enrich trade-off explanations with AI (cheap, compact)
    try:
        settings = get_settings()
        if settings.ENABLE_LLM_PERSONALIZATION and (feasibility_report.trade_offs or []) and feasibility_report.status in ("suboptimal",):
            enriched = explain_tradeoffs(
                constraints={
                    "sessions_per_week": complete_plan.training_sessions_per_week,
                    "available_days": getattr(complete_plan, "available_days", None),
                },
                tradeoffs=feasibility_report.trade_offs or [],
            )
            if enriched:
                feasibility_report.trade_offs = enriched  # type: ignore[assignment]
    except Exception:
        # Never let AI enrichment break program generation
        pass
    
    # Create program version
    version = ProgramVersion(
        schema_version="1.0.0",
        generator_version="phase_1",
        api_version="1.0.0",
    )
    
    # Create provenance
    provenance = Provenance(
        consultation_session_id=consultation.session_id,
        consultation_completed_at=consultation.completed_at,
        generated_at=complete_plan.created_at,
        generated_by="phase_1_generator",
        generator_config={
            "tdee_method": "ensemble",
            "macro_method": "goal_based",
            "training_method": "volume_landmarks",
            "meal_method": "macro_matching",
        },
        input_hash=None,  # TODO: Implement hash of consultation data
        warnings=warnings,
    )
    
    # Build multimodal sessions (optional)
    multimodal_sessions_out = None
    if complete_plan.multimodal_sessions_weekly:
        multimodal_sessions_out = []
        for s in complete_plan.multimodal_sessions_weekly:
            intervals = None
            drills = None
            if s.intervals:
                intervals = [
                    MultimodalInterval(
                        work_minutes=iv.work_minutes,
                        rest_minutes=iv.rest_minutes,
                        target=iv.target,
                    )
                    for iv in s.intervals
                ]
            if s.drills:
                drills = [
                    MultimodalDrill(
                        name=d.name,
                        duration_minutes=d.duration_minutes,
                        focus=d.focus,
                    )
                    for d in s.drills
                ]
            multimodal_sessions_out.append(
                MultimodalSession(
                    session_kind=s.session_kind.value if hasattr(s.session_kind, "value") else str(s.session_kind),
                    modality=s.modality,
                    day_of_week=s.day_of_week,
                    time_of_day=s.time_of_day,
                    start_hour=s.start_hour,
                    end_hour=s.end_hour,
                    duration_minutes=s.duration_minutes,
                    intensity_target=s.intensity_target,
                    intervals=intervals,
                    drills=drills,
                    notes=s.notes,
                )
            )

    # Build complete program bundle
    program_bundle = ProgramBundle(
        program_id=complete_plan.plan_id,
        user_id=complete_plan.user_id,
        version=version,
        provenance=provenance,
        created_at=complete_plan.created_at,
        valid_until=complete_plan.next_reassessment_date,
        primary_goal=complete_plan.goal.value,
        timeline_weeks=12,  # TODO: Extract from options or UserProfile
        training_plan=training_plan,
        nutrition_plan=nutrition_plan,
        tdee_kcal=complete_plan.tdee_result.tdee_mean,
        target_calories_kcal=complete_plan.daily_calorie_target,
        macro_targets={
            "protein_g": complete_plan.macro_targets.protein_g,
            "carbs_g": complete_plan.macro_targets.carbs_g,
            "fat_g": complete_plan.macro_targets.fat_g,
            "calories": complete_plan.macro_targets.calories,
        },
        expected_rate_of_change_kg_per_week=complete_plan.rate_of_change_kg_per_week,
        safety_report=safety_report,
        feasibility_report=feasibility_report,
        program_notes=complete_plan.notes,
        coach_instructions=None,  # TODO: Generate coach-specific instructions
        multimodal_sessions_weekly=multimodal_sessions_out,
    )
    
    return program_bundle


def _transform_training_plan(complete_plan: CompletePlan, consultation: ConsultationTranscript) -> TrainingPlan:
    """Transform internal TrainingProgram to output TrainingPlan."""
    from ultimate_ai_consultation.api.schemas.outputs import TrainingSession, ExerciseInstruction
    
    training_program = complete_plan.training_program
    
    # Helper: derive default coarse windows
    def tod_for_hour(h: int) -> str:
        return "morning" if 5 <= h < 12 else ("afternoon" if 12 <= h < 17 else "evening")

    # Build day -> preferred time_of_day list and explicit time windows if provided
    avail = consultation.training_availability or []
    day_slots = [a.day_of_week.lower() for a in avail if a.day_of_week] or [
        "monday",
        "wednesday",
        "friday",
        "saturday",
    ]
    tod_map = {a.day_of_week.lower(): (a.time_of_day or ["evening"]) for a in avail if a.day_of_week}
    # explicit windows: list of (start,end) per day
    explicit_windows = {}
    for a in avail:
        if not a.day_of_week:
            continue
        day = a.day_of_week.lower()
        win = []
        for tw in (a.time_windows or []):
            win.append((tw.start_hour, tw.end_hour))
        if win:
            explicit_windows[day] = win

    # Reservations from multimodal fixed sessions (avoid placing lifting there)
    fixed_reservations = {}
    if getattr(complete_plan, "multimodal_sessions_weekly", None):
        for s in complete_plan.multimodal_sessions_weekly:
            d = (s.day_of_week or "").lower()
            if not d or s.start_hour is None or s.end_hour is None:
                continue
            fixed_reservations.setdefault(d, []).append((s.start_hour, s.end_hour))

    # Transform sessions
    sessions = []
    for idx, session in enumerate(training_program.weekly_sessions):
        # Transform exercises
        exercises = []
        for exercise in session.exercises:
            exercises.append(ExerciseInstruction(
                exercise_name=exercise.name,
                sets=exercise.sets,
                rep_range=exercise.rep_range,
                rir=exercise.rir,
                rest_seconds=exercise.rest_seconds,
                muscle_groups_primary=exercise.muscle_groups,
                equipment_needed=[],  # TODO: Extract from exercise database
                instructions=exercise.notes,
            ))

        # Assign day/time-of-day with per-day packing
        # Try the planned day, else rotate
        tried_days = 0
        assigned_day = None
        assigned_tod = None
        while tried_days < len(day_slots) and assigned_day is None:
            day = day_slots[(idx + tried_days) % len(day_slots)]
            # Determine candidate windows for this day
            windows = explicit_windows.get(day)
            if windows:
                # pick first window not overlapping fixed reservations
                res = fixed_reservations.get(day, [])
                placed = False
                for (sh, eh) in windows:
                    overlap = any(not (eh <= a or sh >= b) for (a, b) in res)
                    if not overlap:
                        assigned_day = day
                        assigned_tod = tod_for_hour(sh)
                        # Reserve it to avoid stacking too many sessions; approximate
                        fixed_reservations.setdefault(day, []).append((sh, eh))
                        placed = True
                        break
                if placed:
                    break
            # Fall back to time_of_day buckets
            tod_choices = tod_map.get(day, ["morning", "afternoon", "evening"])
            # If there are fixed reservations, avoid picking their time_of_day
            reserved_tods = {tod_for_hour(sh) for (sh, eh) in fixed_reservations.get(day, [])}
            tod = next((t for t in tod_choices if t not in reserved_tods), None)
            if tod:
                assigned_day = day
                assigned_tod = tod
                # Reserve a coarse window for this TOD to limit collisions
                if tod == "morning":
                    fixed_reservations.setdefault(day, []).append((6, 12))
                elif tod == "afternoon":
                    fixed_reservations.setdefault(day, []).append((12, 17))
                else:
                    fixed_reservations.setdefault(day, []).append((17, 21))
                break
            tried_days += 1
        day = assigned_day or day_slots[idx % len(day_slots)]
        tod = assigned_tod or (tod_map.get(day, ["evening"]) or [None])[0]

        sessions.append(TrainingSession(
            session_name=session.session_name,
            exercises=exercises,
            estimated_duration_minutes=session.estimated_duration_minutes,
            total_sets=len(session.exercises) * (session.exercises[0].sets if session.exercises else 0),  # Approximate
            day_of_week=day,
            time_of_day=tod,
            notes=session.notes,
        ))
    
    # Build training plan (append optional coach notes)
    extra_notes = None
    try:
        from ultimate_ai_consultation.services.ai.personalization import coach_notes_for_shift_worker
        from ultimate_ai_consultation.config import get_settings
        settings = get_settings()
        if settings.ENABLE_LLM_PERSONALIZATION:
            # Simple shift-worker heuristic from consultation data
            has_sleep_diff = any((d.category or "").lower() == "sleep" for d in (consultation.difficulties or []))
            evening_bias = sum(1 for a in (consultation.training_availability or []) if "evening" in (a.time_of_day or []))
            if has_sleep_diff or evening_bias >= 2:
                ctx = {
                    "availability": [a.model_dump() for a in (consultation.training_availability or [])],
                    "preferred_meal_times": [m.model_dump() for m in (consultation.preferred_meal_times or [])],
                    "difficulties": [d.model_dump() for d in (consultation.difficulties or [])],
                }
                extra_notes = coach_notes_for_shift_worker(ctx)
    except Exception:
        extra_notes = None

    tp_notes = training_program.progression_notes
    if extra_notes:
        tp_notes = (tp_notes or "").strip()
        if tp_notes:
            tp_notes += "\n\nCoach Notes:\n" + extra_notes
        else:
            tp_notes = "Coach Notes:\n" + extra_notes

    training_plan = TrainingPlan(
        split_type=training_program.split_type.value,
        sessions_per_week=training_program.sessions_per_week,
        weekly_sessions=sessions,
        weekly_volume_per_muscle=training_program.weekly_volume_per_muscle,
        primary_intensity_zone="hypertrophy",  # TODO: Extract from program
        deload_week=training_program.deload_week,
        program_notes=tp_notes,
    )
    
    return training_plan


def _transform_nutrition_plan(complete_plan: CompletePlan) -> NutritionPlan:
    """Transform internal meal plans to output NutritionPlan."""
    from ultimate_ai_consultation.api.schemas.outputs import DailyMealPlan, Meal, FoodItem
    
    # Transform daily meal plans
    daily_plans = []
    for meal_plan in complete_plan.meal_plans:
        # Transform meals
        meals = []
        for meal in meal_plan.meals:
            # Transform foods
            foods = []
            for component in meal.components:
                foods.append(FoodItem(
                    food_name=component.food.name,
                    serving_size=component.servings * component.food.serving_size_g,
                    serving_unit="g",
                    calories=component.calories,
                    protein_g=component.protein_g,
                    carbs_g=component.carbs_g,
                    fat_g=component.fat_g,
                    fiber_g=0.0,  # TODO: Add fiber to internal model
                ))
            
            meals.append(Meal(
                meal_name=meal.meal_name,
                meal_time=meal.meal_type.value,
                foods=foods,
                total_calories=meal.total_calories,
                total_protein_g=meal.total_protein_g,
                total_carbs_g=meal.total_carbs_g,
                total_fat_g=meal.total_fat_g,
                notes=meal.prep_notes,
            ))
        
        # Calculate plan_date from program start date + day number
        from datetime import datetime, timedelta
        program_start = complete_plan.program_start_date if hasattr(complete_plan, 'program_start_date') else datetime.now().date()
        plan_date = program_start + timedelta(days=meal_plan.day_number - 1)

        daily_plans.append(DailyMealPlan(
            plan_date=plan_date,
            training_day=meal_plan.training_day,
            meals=meals,
            daily_calories=meal_plan.daily_totals.get("calories", 0),
            daily_protein_g=meal_plan.daily_totals.get("protein", 0),
            daily_carbs_g=meal_plan.daily_totals.get("carbs", 0),
            daily_fat_g=meal_plan.daily_totals.get("fat", 0),
        ))
    
    # Calculate macro percentages from grams
    # Protein: 4 cal/g, Carbs: 4 cal/g, Fat: 9 cal/g
    total_calories = complete_plan.daily_calorie_target
    protein_calories = complete_plan.macro_targets.protein_g * 4
    carbs_calories = complete_plan.macro_targets.carbs_g * 4
    fat_calories = complete_plan.macro_targets.fat_g * 9

    protein_percentage = round((protein_calories / total_calories) * 100, 1) if total_calories > 0 else 30.0
    carbs_percentage = round((carbs_calories / total_calories) * 100, 1) if total_calories > 0 else 40.0
    fat_percentage = round((fat_calories / total_calories) * 100, 1) if total_calories > 0 else 30.0

    # Calculate calorie range (±10%)
    calorie_range_lower = round(total_calories * 0.9)
    calorie_range_upper = round(total_calories * 1.1)

    # Build nutrition plan
    nutrition_plan = NutritionPlan(
        # Required macro targets
        daily_calorie_target=complete_plan.daily_calorie_target,
        daily_protein_g=complete_plan.macro_targets.protein_g,
        daily_carbs_g=complete_plan.macro_targets.carbs_g,
        daily_fat_g=complete_plan.macro_targets.fat_g,

        # Calorie ranges
        calorie_range_lower=calorie_range_lower,
        calorie_range_upper=calorie_range_upper,

        # Meal plans (renamed from daily_meal_plans)
        meal_plans=daily_plans,

        # Dietary preferences
        dietary_preference="omnivore",  # TODO: Extract from UserProfile
        excluded_foods=[],  # TODO: Extract from UserProfile

        # Macro percentages
        protein_percentage=protein_percentage,
        carbs_percentage=carbs_percentage,
        fat_percentage=fat_percentage,

        # Optional fields
        meal_timing_strategy="flexible",
        supplement_recommendations=[],  # TODO: Add supplement logic
        notes="Follow meal plan as closely as possible. Adjust portions as needed.",
    )

    return nutrition_plan


__all__ = [
    "generate_program_from_consultation",
    "ProgramGenerationError",
]
