"""
Complete Plan Generation Example

Demonstrates end-to-end usage of Phase 1B system:
1. Create user profile
2. Generate complete 14-day program
3. Export grocery list
4. Save to database (JSON format)
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ultimate_ai_consultation.libs.calculators.macros import Goal
from ultimate_ai_consultation.libs.calculators.tdee import ActivityFactor
from ultimate_ai_consultation.services.program_generator import (
    PlanGenerator,
    UserProfile,
    ExperienceLevel,
    IntensityZone,
    DietaryPreference,
    GroceryListGenerator,
)


def main():
    """Run complete plan generation example"""

    print("=" * 70)
    print("ULTIMATE AI CONSULTATION - Complete Plan Generation Demo")
    print("=" * 70)
    print()

    # ========================================================================
    # STEP 1: Create User Profile from Consultation Data
    # ========================================================================
    print("Step 1: Creating user profile from consultation...")

    user_profile = UserProfile(
        # Demographics
        user_id="user_demo_123",
        age=28,
        sex_at_birth="male",
        weight_kg=82.0,
        height_cm=178,
        body_fat_percentage=18.0,
        # Goals
        primary_goal=Goal.MUSCLE_GAIN,
        target_weight_kg=88.0,
        timeline_weeks=16,
        # Training
        sessions_per_week=5,
        experience_level=ExperienceLevel.INTERMEDIATE,
        training_focus=IntensityZone.HYPERTROPHY,
        available_days=["monday", "tuesday", "wednesday", "thursday", "friday"],
        # Nutrition
        dietary_preference=DietaryPreference.NONE,
        food_allergies=[],
        # Activity
        activity_factor=ActivityFactor.VERY_ACTIVE,
        # Medical (all clear)
        medical_conditions=[],
        medications=[],
        injuries=[],
        doctor_clearance=True,
    )

    print(f"  ✓ Profile created for {user_profile.user_id}")
    print(f"    - Age: {user_profile.age}, Weight: {user_profile.weight_kg}kg")
    print(f"    - Goal: {user_profile.primary_goal.value}")
    print(f"    - Training: {user_profile.sessions_per_week}x/week, {user_profile.experience_level.value}")
    print()

    # ========================================================================
    # STEP 2: Generate Complete Plan
    # ========================================================================
    print("Step 2: Generating complete 14-day program...")
    print("  - Running safety validation...")
    print("  - Calculating TDEE with ensemble method...")
    print("  - Determining calorie and macro targets...")
    print("  - Validating feasibility with constraint solver...")
    print("  - Building training program...")
    print("  - Assembling meal plans...")

    plan_generator = PlanGenerator()

    try:
        complete_plan, warnings = plan_generator.generate_complete_plan(
            profile=user_profile, plan_version=1
        )

        print(f"  ✓ Plan generated successfully!")
        print()

        if warnings:
            print("  ⚠️  Warnings:")
            for warning in warnings:
                print(f"      - {warning}")
            print()

    except ValueError as e:
        print(f"  ✗ Plan generation failed: {e}")
        return

    # ========================================================================
    # STEP 3: Display Plan Summary
    # ========================================================================
    print("Step 3: Plan Summary")
    print("-" * 70)

    print(f"Plan ID: {complete_plan.plan_id}")
    print(f"Goal: {complete_plan.goal.value}")
    print(f"Duration: {complete_plan.duration_days} days")
    print()

    print("ENERGY EXPENDITURE:")
    print(f"  TDEE: {complete_plan.tdee_result.tdee_mean:.0f} kcal/day")
    print(
        f"  Confidence Interval: {complete_plan.tdee_result.ci_lower:.0f} - {complete_plan.tdee_result.ci_upper:.0f} kcal"
    )
    print(f"  Confidence: {complete_plan.tdee_result.confidence:.1%}")
    print()

    print("CALORIE & MACRO TARGETS:")
    print(f"  Daily Calories: {complete_plan.daily_calorie_target} kcal")
    print(f"  Protein: {complete_plan.macro_targets.protein_g}g")
    print(f"  Carbs: {complete_plan.macro_targets.carbs_g}g")
    print(f"  Fat: {complete_plan.macro_targets.fat_g}g")
    print(
        f"  Expected Rate of Change: {complete_plan.rate_of_change_kg_per_week:+.2f} kg/week"
    )
    print(f"  Rationale: {', '.join(complete_plan.macro_targets.rationale)}")
    print()

    print("TRAINING PROGRAM:")
    print(f"  Split: {complete_plan.training_program.split_type.value}")
    print(f"  Sessions per Week: {complete_plan.training_program.sessions_per_week}")
    print(f"  Deload Every: {complete_plan.training_program.deload_week} weeks")
    print()

    # Show first workout session as example
    first_session = complete_plan.training_program.weekly_sessions[0]
    print(f"  Example Session: {first_session.session_name}")
    print(f"  Duration: ~{first_session.estimated_duration_minutes} minutes")
    print(f"  Exercises:")
    for exercise in first_session.exercises[:3]:  # Show first 3 exercises
        print(
            f"    - {exercise.name}: {exercise.sets} sets x {exercise.rep_range} reps @ {exercise.rir} RIR"
        )
    print(f"    ... and {len(first_session.exercises) - 3} more exercises")
    print()

    print("WEEKLY VOLUME PER MUSCLE:")
    for muscle, sets in sorted(
        complete_plan.training_program.weekly_volume_per_muscle.items()
    ):
        print(f"  {muscle.capitalize()}: {sets} sets/week")
    print()

    print("NUTRITION PLAN:")
    print(f"  Total Meals: {sum(len(mp.meals) for mp in complete_plan.meal_plans)}")

    # Show Day 1 meals as example
    day1 = complete_plan.meal_plans[0]
    print(f"\n  Day 1 Example (Training Day: {day1.training_day}):")
    for meal in day1.meals:
        print(f"    - {meal.meal_name}: {meal.total_calories:.0f} kcal")
        print(
            f"      ({meal.total_protein_g:.0f}P / {meal.total_carbs_g:.0f}C / {meal.total_fat_g:.0f}F)"
        )
    print()

    # ========================================================================
    # STEP 4: Generate Grocery List
    # ========================================================================
    print("Step 4: Generating grocery list...")

    grocery_generator = GroceryListGenerator()
    grocery_list = grocery_generator.generate_grocery_list(
        meal_plans=complete_plan.meal_plans, bulk_buying=True
    )

    print(f"  ✓ Grocery list generated!")
    print(f"    - Total Items: {grocery_list.total_items}")
    print(f"    - Total Cost: ${grocery_list.total_estimated_cost_usd:.2f}")
    print(f"    - Cost per Day: ${grocery_list.cost_per_day_usd:.2f}")
    print()

    # Show items by category
    print("  Items by Category:")
    for category, items in grocery_list.items_by_category.items():
        total_category_cost = sum(item.estimated_cost_usd for item in items)
        print(f"    {category.value.upper()}: {len(items)} items (${total_category_cost:.2f})")

    print()

    # Show bulk opportunities
    if grocery_list.bulk_buying_opportunities:
        print("  Bulk Buying Opportunities:")
        for opp in grocery_list.bulk_buying_opportunities[:3]:
            print(f"    • {opp}")
        print()

    # ========================================================================
    # STEP 5: Export Results
    # ========================================================================
    print("Step 5: Exporting results...")

    # Export plan to JSON
    plan_json = plan_generator.export_plan_to_json(complete_plan)
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    json_path = output_dir / f"{complete_plan.plan_id}.json"
    with open(json_path, "w") as f:
        f.write(plan_json)
    print(f"  ✓ Plan exported to: {json_path}")

    # Export grocery list to text
    grocery_text = grocery_generator.export_to_text(grocery_list)
    grocery_path = output_dir / f"grocery_list_{complete_plan.user_id}.txt"
    with open(grocery_path, "w") as f:
        f.write(grocery_text)
    print(f"  ✓ Grocery list exported to: {grocery_path}")

    # Export grocery list to markdown
    grocery_md = grocery_generator.export_to_markdown(grocery_list)
    grocery_md_path = output_dir / f"grocery_list_{complete_plan.user_id}.md"
    with open(grocery_md_path, "w") as f:
        f.write(grocery_md)
    print(f"  ✓ Grocery list (markdown) exported to: {grocery_md_path}")

    print()
    print("=" * 70)
    print("COMPLETE! All components working successfully.")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. Review generated plan in output directory")
    print("  2. Store plan JSON in plan_versions table")
    print("  3. Send plan to user via unified coach")
    print("  4. Begin bi-weekly reassessment cycle (Phase 2)")


if __name__ == "__main__":
    main()
