import uuid
from pathlib import Path
from typing import Dict, Any, List

import pytest

from api.schemas.inputs import (
    ConsultationTranscript,
    UserDemographics,
    TrainingModalityInput,
    TrainingAvailabilityInput,
    PreferredMealTimeInput,
    TypicalMealFoodInput,
    ImprovementGoalInput,
    DifficultyInput,
    NonNegotiableInput,
    UpcomingEventInput,
    GenerationOptions,
    DietaryMode,
    EquipmentAvailability,
)
from api.generate_program import generate_program_from_consultation


def _make_uuid() -> str:
    return str(uuid.uuid4())


def persona_inputs() -> List[Dict[str, Any]]:
    """Collection of diverse persona input dicts for program generation tests."""
    base_days = [
        TrainingAvailabilityInput(day_of_week="monday", time_of_day=["evening"], duration_minutes=60),
        TrainingAvailabilityInput(day_of_week="wednesday", time_of_day=["evening"], duration_minutes=60),
        TrainingAvailabilityInput(day_of_week="friday", time_of_day=["evening"], duration_minutes=60),
        TrainingAvailabilityInput(day_of_week="saturday", time_of_day=["morning"], duration_minutes=75),
    ]

    return [
        {
            "slug": "beginner_hypertrophy_male",
            "consultation": ConsultationTranscript(
                user_id=_make_uuid(),
                session_id=_make_uuid(),
                demographics=UserDemographics(
                    user_id=_make_uuid(), age=28, sex_at_birth="male", weight_kg=82.0, height_cm=178.0
                ),
                training_modalities=[
                    TrainingModalityInput(modality="bodybuilding", proficiency="beginner", years_experience=0, is_primary=True)
                ],
                training_availability=base_days,
                preferred_meal_times=[
                    PreferredMealTimeInput(time_of_day="breakfast", typical_hour=8),
                    PreferredMealTimeInput(time_of_day="lunch", typical_hour=12),
                    PreferredMealTimeInput(time_of_day="dinner", typical_hour=19),
                ],
                typical_foods=[
                    TypicalMealFoodInput(food_name="chicken", meal_time="dinner", frequency="weekly"),
                    TypicalMealFoodInput(food_name="rice", meal_time="dinner", frequency="weekly"),
                ],
                improvement_goals=[
                    ImprovementGoalInput(goal_type="muscle_gain", description="Build muscle", priority=8, timeline_weeks=16)
                ],
                difficulties=[],
                non_negotiables=[],
            ),
            "options": GenerationOptions(program_duration_weeks=12, meals_per_day=3, dietary_mode=DietaryMode.FLEXIBLE),
        },
        {
            "slug": "busy_parent_minimal_equipment_female",
            "consultation": ConsultationTranscript(
                user_id=_make_uuid(),
                session_id=_make_uuid(),
                demographics=UserDemographics(
                    user_id=_make_uuid(), age=36, sex_at_birth="female", weight_kg=70.0, height_cm=165.0
                ),
                training_modalities=[
                    TrainingModalityInput(modality="general_fitness", proficiency="beginner", years_experience=1, is_primary=True)
                ],
                training_availability=[
                    TrainingAvailabilityInput(day_of_week="tuesday", time_of_day=["morning"], duration_minutes=45),
                    TrainingAvailabilityInput(day_of_week="thursday", time_of_day=["morning"], duration_minutes=45),
                    TrainingAvailabilityInput(day_of_week="saturday", time_of_day=["morning"], duration_minutes=60),
                ],
                preferred_meal_times=[PreferredMealTimeInput(time_of_day="dinner", typical_hour=18)],
                typical_foods=[TypicalMealFoodInput(food_name="pasta", meal_time="dinner", frequency="weekly")],
                improvement_goals=[
                    ImprovementGoalInput(goal_type="fat_loss", description="Lose 5kg", priority=9, timeline_weeks=12)
                ],
                difficulties=[DifficultyInput(category="time", description="Kids schedule", severity=6)],
                non_negotiables=[NonNegotiableInput(constraint="no_gym_commute", reason="Childcare")],
            ),
            "options": GenerationOptions(
                program_duration_weeks=12,
                meals_per_day=3,
                dietary_mode=DietaryMode.FLEXIBLE,
                equipment_available=EquipmentAvailability.MINIMAL,
            ),
        },
        {
            "slug": "vegan_endurance_weight_loss_female",
            "consultation": ConsultationTranscript(
                user_id=_make_uuid(),
                session_id=_make_uuid(),
                demographics=UserDemographics(
                    user_id=_make_uuid(), age=30, sex_at_birth="female", weight_kg=75.0, height_cm=170.0
                ),
                training_modalities=[
                    TrainingModalityInput(modality="running", proficiency="intermediate", years_experience=3, is_primary=True)
                ],
                training_availability=base_days,
                preferred_meal_times=[
                    PreferredMealTimeInput(time_of_day="breakfast", typical_hour=9),
                    PreferredMealTimeInput(time_of_day="dinner", typical_hour=19),
                ],
                typical_foods=[
                    TypicalMealFoodInput(food_name="tofu", meal_time="dinner", frequency="weekly"),
                    TypicalMealFoodInput(food_name="beans", meal_time="lunch", frequency="weekly"),
                ],
                improvement_goals=[
                    ImprovementGoalInput(goal_type="fat_loss", description="Cut 7kg", priority=8, timeline_weeks=20)
                ],
                difficulties=[],
                non_negotiables=[NonNegotiableInput(constraint="vegan", reason="Ethical")],
            ),
            "options": GenerationOptions(program_duration_weeks=16, meals_per_day=3, dietary_mode=DietaryMode.VEGAN),
        },
        {
            "slug": "advanced_powerlifter_male",
            "consultation": ConsultationTranscript(
                user_id=_make_uuid(),
                session_id=_make_uuid(),
                demographics=UserDemographics(
                    user_id=_make_uuid(), age=35, sex_at_birth="male", weight_kg=95.0, height_cm=180.0
                ),
                training_modalities=[
                    TrainingModalityInput(modality="powerlifting", proficiency="advanced", years_experience=8, is_primary=True)
                ],
                training_availability=base_days,
                preferred_meal_times=[PreferredMealTimeInput(time_of_day="dinner", typical_hour=20)],
                typical_foods=[TypicalMealFoodInput(food_name="steak", meal_time="dinner", frequency="weekly")],
                improvement_goals=[
                    ImprovementGoalInput(goal_type="strength", description="Total +50kg", priority=10, timeline_weeks=24)
                ],
                difficulties=[],
                non_negotiables=[],
            ),
            "options": GenerationOptions(program_duration_weeks=20, meals_per_day=4, dietary_mode=DietaryMode.OMNIVORE),
        },
        {
            "slug": "senior_mobility_focused_female",
            "consultation": ConsultationTranscript(
                user_id=_make_uuid(),
                session_id=_make_uuid(),
                demographics=UserDemographics(
                    user_id=_make_uuid(), age=68, sex_at_birth="female", weight_kg=62.0, height_cm=160.0
                ),
                training_modalities=[
                    TrainingModalityInput(modality="mobility", proficiency="beginner", years_experience=0, is_primary=True)
                ],
                training_availability=[
                    TrainingAvailabilityInput(day_of_week="monday", time_of_day=["morning"], duration_minutes=30),
                    TrainingAvailabilityInput(day_of_week="wednesday", time_of_day=["morning"], duration_minutes=30),
                    TrainingAvailabilityInput(day_of_week="friday", time_of_day=["morning"], duration_minutes=30),
                ],
                preferred_meal_times=[PreferredMealTimeInput(time_of_day="lunch", typical_hour=12)],
                typical_foods=[TypicalMealFoodInput(food_name="salad", meal_time="lunch", frequency="daily")],
                improvement_goals=[
                    ImprovementGoalInput(goal_type="health", description="Improve mobility and balance", priority=8, timeline_weeks=12)
                ],
                difficulties=[DifficultyInput(category="injury", description="Knee discomfort", severity=4)],
                non_negotiables=[],
            ),
            "options": GenerationOptions(program_duration_weeks=12, meals_per_day=3, dietary_mode=DietaryMode.FLEXIBLE),
        },
        {
            "slug": "shift_worker_evening_only_male",
            "consultation": ConsultationTranscript(
                user_id=_make_uuid(),
                session_id=_make_uuid(),
                demographics=UserDemographics(
                    user_id=_make_uuid(), age=41, sex_at_birth="male", weight_kg=88.0, height_cm=182.0
                ),
                training_modalities=[
                    TrainingModalityInput(modality="general_fitness", proficiency="intermediate", years_experience=4, is_primary=True)
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
            ),
            "options": GenerationOptions(program_duration_weeks=16, meals_per_day=3, dietary_mode=DietaryMode.FLEXIBLE),
        },
        {
            "slug": "triathlete_event_in_12_weeks_female",
            "consultation": ConsultationTranscript(
                user_id=_make_uuid(),
                session_id=_make_uuid(),
                demographics=UserDemographics(
                    user_id=_make_uuid(), age=32, sex_at_birth="female", weight_kg=60.0, height_cm=168.0
                ),
                training_modalities=[
                    TrainingModalityInput(modality="triathlon", proficiency="intermediate", years_experience=2, is_primary=True)
                ],
                training_availability=base_days,
                preferred_meal_times=[PreferredMealTimeInput(time_of_day="dinner", typical_hour=19)],
                typical_foods=[TypicalMealFoodInput(food_name="fish", meal_time="dinner", frequency="weekly")],
                improvement_goals=[
                    ImprovementGoalInput(goal_type="performance", description="Finish strong", priority=9, timeline_weeks=12)
                ],
                upcoming_events=[UpcomingEventInput(event_name="Olympic Tri", event_type="race", weeks_until=12, priority=10)],
                difficulties=[],
                non_negotiables=[],
            ),
            "options": GenerationOptions(program_duration_weeks=12, meals_per_day=4, dietary_mode=DietaryMode.PESCATARIAN),
        },
        {
            "slug": "obese_beginner_time_constraint_male",
            "consultation": ConsultationTranscript(
                user_id=_make_uuid(),
                session_id=_make_uuid(),
                demographics=UserDemographics(
                    user_id=_make_uuid(), age=45, sex_at_birth="male", weight_kg=125.0, height_cm=175.0
                ),
                training_modalities=[
                    TrainingModalityInput(modality="walking", proficiency="beginner", years_experience=0, is_primary=True)
                ],
                training_availability=[
                    TrainingAvailabilityInput(day_of_week="monday", time_of_day=["morning"], duration_minutes=30),
                    TrainingAvailabilityInput(day_of_week="wednesday", time_of_day=["morning"], duration_minutes=30),
                ],
                preferred_meal_times=[PreferredMealTimeInput(time_of_day="dinner", typical_hour=20)],
                typical_foods=[TypicalMealFoodInput(food_name="sandwich", meal_time="lunch", frequency="daily")],
                improvement_goals=[
                    ImprovementGoalInput(goal_type="fat_loss", description="Lose 20kg", priority=10, timeline_weeks=52)
                ],
                difficulties=[DifficultyInput(category="time", description="Work hours", severity=7)],
                non_negotiables=[],
            ),
            "options": GenerationOptions(program_duration_weeks=24, meals_per_day=3, dietary_mode=DietaryMode.FLEXIBLE),
        },
    ]


def _bundle_to_text(program_bundle) -> str:
    """Render a concise human-readable training summary with a nutrition outline."""
    lines = []
    lines.append(f"Program ID: {program_bundle.program_id}")
    lines.append(f"Sessions per week: {program_bundle.training_plan.sessions_per_week}")
    lines.append(f"Split: {program_bundle.training_plan.split_type}")
    lines.append("\nTraining Sessions:")
    for s in program_bundle.training_plan.weekly_sessions:
        lines.append(f"- {s.day_of_week or 'unscheduled'} {s.time_of_day or ''} | {s.session_name} ({s.estimated_duration_minutes}m)")
        for e in s.exercises[:4]:  # show first few
            lines.append(f"    * {e.exercise_name}: {e.sets} x {e.rep_range} (rest {e.rest_seconds}s)")
    lines.append("\nNutrition (first 2 days):")
    for d in program_bundle.nutrition_plan.daily_meal_plans[:2]:
        lines.append(f"Day {d.day_number} | {'Training' if d.training_day else 'Rest'} | kcal={d.daily_totals.get('calories', 0)}")
        for m in d.meals:
            lines.append(f"  - {m.meal_time}: {m.meal_name} ({int(m.total_calories)} kcal)")
    return "\n".join(lines)


@pytest.mark.parametrize("case", persona_inputs(), ids=lambda c: c["slug"])  # type: ignore[arg-type]
def test_generate_program_for_personas(case, tmp_path: Path):
    consultation: ConsultationTranscript = case["consultation"]
    options: GenerationOptions = case["options"]

    bundle, warnings = generate_program_from_consultation(consultation, options)

    # Basic structural assertions
    assert bundle.training_plan.sessions_per_week >= 1
    assert len(bundle.training_plan.weekly_sessions) >= 1
    assert len(bundle.nutrition_plan.daily_meal_plans) >= 7
    assert bundle.safety_report.clearance_granted is True
    assert bundle.feasibility_report.is_feasible is True

    # Write a human-readable summary for inspection
    text = _bundle_to_text(bundle)
    out_file = tmp_path / f"{case['slug']}.txt"
    out_file.write_text(text, encoding="utf-8")

    assert out_file.exists(), "Expected output text file to be created"
    content = out_file.read_text(encoding="utf-8")
    # Content sanity checks
    assert "Training Sessions:" in content
    assert "Nutrition (first 2 days):" in content
    # Ensure at least one exercise line is present
    assert "* " in content

