import uuid

from api.schemas.inputs import (
    ConsultationTranscript,
    UserDemographics,
    TrainingModalityInput,
    TrainingAvailabilityInput,
    PreferredMealTimeInput,
    TypicalMealFoodInput,
    ImprovementGoalInput,
    DifficultyInput,
    GenerationOptions,
    DietaryMode,
)
from api.generate_program import generate_program_from_consultation


def _bundle_to_text(program_bundle) -> str:
    lines = []
    lines.append(f"Program ID: {program_bundle.program_id}")
    lines.append(f"Sessions per week: {program_bundle.training_plan.sessions_per_week}")
    lines.append(f"Split: {program_bundle.training_plan.split_type}")
    lines.append("\nTraining Sessions:")
    for s in program_bundle.training_plan.weekly_sessions:
        lines.append(
            f"- {s.day_of_week or 'unscheduled'} {s.time_of_day or ''} | {s.session_name} ({s.estimated_duration_minutes}m)"
        )
        for e in s.exercises[:4]:
            lines.append(
                f"    * {e.exercise_name}: {e.sets} x {e.rep_range} (rest {e.rest_seconds}s)"
            )
    lines.append("\nNutrition (first 2 days):")
    for d in program_bundle.nutrition_plan.daily_meal_plans[:2]:
        lines.append(
            f"Day {d.day_number} | {'Training' if d.training_day else 'Rest'} | kcal={d.daily_totals.get('calories', 0)}"
        )
        for m in d.meals:
            lines.append(f"  - {m.meal_time}: {m.meal_name} ({int(m.total_calories)} kcal)")
    return "\n".join(lines)


def main():
    consultation = ConsultationTranscript(
        user_id=str(uuid.uuid4()),
        session_id=str(uuid.uuid4()),
        demographics=UserDemographics(
            user_id=str(uuid.uuid4()), age=41, sex_at_birth="male", weight_kg=88.0, height_cm=182.0
        ),
        training_modalities=[
            TrainingModalityInput(
                modality="general_fitness", proficiency="intermediate", years_experience=4, is_primary=True
            )
        ],
        training_availability=[
            TrainingAvailabilityInput(day_of_week="monday", time_of_day=["evening"], duration_minutes=60),
            TrainingAvailabilityInput(day_of_week="tuesday", time_of_day=["evening"], duration_minutes=60),
            TrainingAvailabilityInput(day_of_week="thursday", time_of_day=["evening"], duration_minutes=60),
        ],
        preferred_meal_times=[
            PreferredMealTimeInput(time_of_day="breakfast", typical_hour=11),
            PreferredMealTimeInput(time_of_day="dinner", typical_hour=22),
        ],
        typical_foods=[TypicalMealFoodInput(food_name="eggs", meal_time="breakfast", frequency="daily")],
        improvement_goals=[
            ImprovementGoalInput(goal_type="recomp", description="Recomp", priority=6, timeline_weeks=16)
        ],
        difficulties=[DifficultyInput(category="sleep", description="Late shifts", severity=5)],
        non_negotiables=[],
    )

    options = GenerationOptions(program_duration_weeks=16, meals_per_day=3, dietary_mode=DietaryMode.FLEXIBLE)

    bundle, warnings = generate_program_from_consultation(consultation, options)
    print(_bundle_to_text(bundle))
    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"- {w}")


if __name__ == "__main__":
    main()

