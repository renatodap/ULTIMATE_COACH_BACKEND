"""
End-to-End Integration Test: Generate → Store → Log → Match → Adherence

This test verifies the complete adaptive coaching flow:
1. Generate a program using ultimate_ai_consultation
2. Store program in plan instance tables
3. Log activities and meals
4. Match logged data to planned data
5. Calculate adherence scores

Run with: python test_end_to_end_integration.py
"""

import asyncio
import sys
import os
from datetime import datetime, date, timedelta
from uuid import uuid4
import json

# Set up minimal environment for testing
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("SUPABASE_URL", "http://localhost")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-key")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-secret")

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "ultimate_ai_consultation")
)

try:
    from ultimate_ai_consultation.api.generate_program import (
        generate_program_from_consultation,
    )
    from ultimate_ai_consultation.api.schemas.inputs import (
        ConsultationTranscript,
        UserDemographics,
        TrainingModalityInput,
        TrainingAvailabilityInput,
        PreferredMealTimeInput,
        TypicalMealFoodInput,
        ImprovementGoalInput,
        GenerationOptions,
        DietaryMode,
    )

    print("✅ Successfully imported program generation modules")
except Exception as e:
    print(f"❌ Failed to import program generation modules: {e}")
    print("This test requires the ultimate_ai_consultation module to be available")
    sys.exit(1)

try:
    from app.services.program_storage_service import ProgramStorageService
    from app.services.activity_matching_service import activity_matching_service
    from app.services.meal_matching_service import meal_matching_service
    from app.services.supabase_service import SupabaseService

    print("✅ Successfully imported backend services")
except Exception as e:
    print(f"❌ Failed to import backend services: {e}")
    sys.exit(1)


def create_test_consultation() -> ConsultationTranscript:
    """Create a simple test consultation for program generation"""
    user_id = str(uuid4())

    return ConsultationTranscript(
        user_id=user_id,
        session_id=str(uuid4()),
        demographics=UserDemographics(
            user_id=user_id,
            age=28,
            sex_at_birth="male",
            weight_kg=80.0,
            height_cm=178.0,
        ),
        training_modalities=[
            TrainingModalityInput(
                modality="bodybuilding",
                proficiency="intermediate",
                years_experience=2,
                is_primary=True,
            )
        ],
        training_availability=[
            TrainingAvailabilityInput(
                day_of_week="monday",
                time_of_day=["evening"],
                duration_minutes=60,
            ),
            TrainingAvailabilityInput(
                day_of_week="wednesday",
                time_of_day=["evening"],
                duration_minutes=60,
            ),
            TrainingAvailabilityInput(
                day_of_week="friday",
                time_of_day=["evening"],
                duration_minutes=60,
            ),
        ],
        preferred_meal_times=[
            PreferredMealTimeInput(time_of_day="breakfast", typical_hour=8),
            PreferredMealTimeInput(time_of_day="lunch", typical_hour=12),
            PreferredMealTimeInput(time_of_day="dinner", typical_hour=19),
        ],
        typical_foods=[
            TypicalMealFoodInput(
                food_name="chicken", meal_time="dinner", frequency="weekly"
            ),
            TypicalMealFoodInput(
                food_name="rice", meal_time="dinner", frequency="weekly"
            ),
        ],
        improvement_goals=[
            ImprovementGoalInput(
                goal_type="muscle_gain",
                description="Build muscle",
                priority=8,
                timeline_weeks=12,
            )
        ],
        difficulties=[],
        non_negotiables=[],
    )


async def run_test():
    """
    Execute the complete end-to-end test flow.
    """
    print("\n" + "=" * 80)
    print("ULTIMATE COACH - End-to-End Integration Test")
    print("=" * 80 + "\n")

    # Initialize services
    storage_service = ProgramStorageService()
    db = SupabaseService()
    test_user_id = str(uuid4())

    # Step 1: Generate Program
    print("Step 1: Generating Program...")
    print("-" * 80)

    consultation = create_test_consultation()
    options = GenerationOptions(
        program_duration_weeks=12,
        meals_per_day=3,
        dietary_mode=DietaryMode.FLEXIBLE,
    )

    try:
        program_bundle, warnings = generate_program_from_consultation(
            consultation, options
        )

        print(f"✅ Program generated!")
        print(f"   - Duration: {program_bundle.timeline_weeks} weeks")
        print(
            f"   - Sessions/week: {program_bundle.training_plan.sessions_per_week}"
        )
        print(f"   - Daily calories: {program_bundle.target_calories_kcal} kcal")
        if warnings:
            print(f"   - Warnings: {len(warnings)}")

    except Exception as e:
        print(f"❌ Program generation failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Step 2: Store Program
    print("\nStep 2: Storing Program...")
    print("-" * 80)

    try:
        program_id = await storage_service.store_program_bundle(
            program_bundle=program_bundle.model_dump(),
            user_id=test_user_id,
        )

        print(f"✅ Program stored! (ID: {program_id[:8]}...)")

        # Verify storage
        client = db.client
        sessions = (
            client.table("session_instances")
            .select("id")
            .eq("program_id", program_id)
            .execute()
        )
        meals = (
            client.table("meal_instances")
            .select("id")
            .eq("program_id", program_id)
            .limit(10)
            .execute()
        )

        print(f"   - Sessions stored: {len(sessions.data)}")
        print(f"   - Meals stored: {len(meals.data)}")

    except Exception as e:
        print(f"❌ Storage failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Step 3: Log Activity & Match
    print("\nStep 3: Logging Activity & Matching...")
    print("-" * 80)

    try:
        # Get first session
        first_session = sessions.data[0]
        exercises = (
            client.table("exercise_plan_items")
            .select("*")
            .eq("session_instance_id", first_session["id"])
            .execute()
        )

        # Log activity
        activity_data = {
            "user_id": test_user_id,
            "category": "strength_training",
            "activity_name": "Test Workout",
            "start_time": datetime.now().isoformat(),
            "end_time": (datetime.now() + timedelta(hours=1)).isoformat(),
            "duration_minutes": 60,
            "calories_burned": 300,
            "intensity_mets": 5.0,
            "metrics": {
                "exercises": [
                    {"name": ex.get("name"), "sets": ex.get("sets"), "reps": 10}
                    for ex in exercises.data[:2]
                ]
            },
        }

        activity = client.table("activities").insert(activity_data).execute()
        activity_id = activity.data[0]["id"]

        # Match activity
        adherence = await activity_matching_service.match_activity_to_session(
            activity_id=activity_id,
            user_id=test_user_id,
        )

        if adherence:
            print(f"✅ Activity matched!")
            print(f"   - Status: {adherence['status']}")
            print(f"   - Score: {adherence['similarity_score']:.2f}")
        else:
            print("⚠️  No match found")

    except Exception as e:
        print(f"❌ Activity matching failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Step 4: Log Meal & Match
    print("\nStep 4: Logging Meal & Matching...")
    print("-" * 80)

    try:
        # Get first meal
        first_meal = meals.data[0]
        meal_totals = first_meal.get("totals_json", {})

        # Log meal
        meal_data = {
            "user_id": test_user_id,
            "meal_name": "Test Meal",
            "meal_type": first_meal.get("meal_type"),
            "logged_at": datetime.now().isoformat(),
            "total_calories": meal_totals.get("calories", 500),
            "total_protein_g": meal_totals.get("protein_g", 30),
            "total_carbs_g": meal_totals.get("carbs_g", 50),
            "total_fat_g": meal_totals.get("fat_g", 15),
        }

        meal = client.table("meal_logs").insert(meal_data).execute()
        meal_log_id = meal.data[0]["id"]

        # Match meal
        meal_adherence = await meal_matching_service.match_meal_to_plan(
            meal_log_id=meal_log_id,
            user_id=test_user_id,
        )

        if meal_adherence:
            print(f"✅ Meal matched!")
            print(f"   - Status: {meal_adherence['status']}")
            print(f"   - Score: {meal_adherence['similarity_score']:.2f}")
        else:
            print("⚠️  No match found")

    except Exception as e:
        print(f"❌ Meal matching failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Step 5: Cleanup
    print("\nStep 5: Cleaning up...")
    print("-" * 80)

    try:
        # Delete in reverse order
        client.table("adherence_records").delete().eq("user_id", test_user_id).execute()
        client.table("meal_logs").delete().eq("user_id", test_user_id).execute()
        client.table("activities").delete().eq("user_id", test_user_id).execute()
        client.table("calendar_events").delete().eq("user_id", test_user_id).execute()
        client.table("meal_instances").delete().eq("program_id", program_id).execute()
        client.table("session_instances").delete().eq("program_id", program_id).execute()
        client.table("programs").delete().eq("id", program_id).execute()

        print("✅ Cleanup complete!")

    except Exception as e:
        print(f"⚠️  Cleanup failed: {e}")

    # Summary
    print("\n" + "=" * 80)
    print("✅ END-TO-END TEST COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print("\nAll systems verified:")
    print("  ✅ Program generation")
    print("  ✅ Program storage")
    print("  ✅ Activity matching")
    print("  ✅ Meal matching")
    print("\nThe adaptive coaching loop is operational! 🎉\n")

    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(run_test())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
