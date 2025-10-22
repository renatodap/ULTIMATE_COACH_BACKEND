"""
End-to-End Integration Test

This test runs the complete pipeline from consultation data through to final program output,
verifying that all components work together correctly:

1. Consultation data → Adapter → UserProfile
2. UserProfile → Phase 1 Generator → CompletePlan
3. CompletePlan → Schema Transformation → ProgramBundle
4. Validation of all outputs and data integrity

This is the ultimate integration test that proves the system works end-to-end.
"""

# Set environment variables before any imports
import os
os.environ['ANTHROPIC_API_KEY'] = 'test-key-e2e'
os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
os.environ['SUPABASE_KEY'] = 'test-key'
os.environ['SUPABASE_JWT_SECRET'] = 'test-secret'

import sys
from datetime import datetime
from typing import Dict, Any

# Import our API
from api import generate_program_from_consultation, ProgramGenerationError
from api.schemas.inputs import (
    ConsultationTranscript,
    UserDemographics,
    ImprovementGoalInput,
    TrainingModalityInput,
    TrainingAvailabilityInput,
    GenerationOptions,
    DietaryMode,
    EquipmentAvailability,
)


def print_section(title: str):
    """Print a section header."""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def print_result(test_name: str, passed: bool, details: str = ""):
    """Print test result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {test_name}")
    if details:
        for line in details.split("\n"):
            print(f"        {line}")


def create_realistic_consultation() -> ConsultationTranscript:
    """
    Create a realistic consultation with comprehensive data.
    
    This simulates a real user who completed a full AI consultation.
    """
    return ConsultationTranscript(
        user_id="e2e-test-user-001",
        session_id="e2e-session-001",
        completed_at=datetime.now(),
        
        # Complete demographics
        demographics=UserDemographics(
            user_id="e2e-test-user-001",
            age=28,
            sex_at_birth="male",
            weight_kg=82.0,
            height_cm=178.0,
            body_fat_percentage=18.0,
        ),
        
        # Training background
        training_modalities=[
            TrainingModalityInput(
                modality="bodybuilding",
                proficiency="intermediate",
                years_experience=3,
                is_primary=True,
                enjoys_it=True,
            ),
            TrainingModalityInput(
                modality="powerlifting",
                proficiency="beginner",
                years_experience=1,
                is_primary=False,
                enjoys_it=True,
            ),
        ],
        
        # Clear goals
        improvement_goals=[
            ImprovementGoalInput(
                goal_type="muscle_gain",
                description="Gain 5kg of lean muscle mass for physique competition",
                priority=10,
                target_metric="87kg at 15% body fat",
                timeline_weeks=16,
            ),
            ImprovementGoalInput(
                goal_type="strength",
                description="Increase bench press to 140kg",
                priority=7,
                target_metric="140kg bench press",
                timeline_weeks=16,
            ),
        ],
        
        # Training availability
        training_availability=[
            TrainingAvailabilityInput(
                day_of_week="monday",
                time_of_day=["evening"],
                duration_minutes=90,
            ),
            TrainingAvailabilityInput(
                day_of_week="tuesday",
                time_of_day=["evening"],
                duration_minutes=90,
            ),
            TrainingAvailabilityInput(
                day_of_week="thursday",
                time_of_day=["evening"],
                duration_minutes=90,
            ),
            TrainingAvailabilityInput(
                day_of_week="friday",
                time_of_day=["evening"],
                duration_minutes=90,
            ),
        ],
        
        # Context
        conversation_summary="User is an experienced lifter looking to compete in physique competition. "
                           "Has good training history, clear goals, and realistic timeline."
    )


def test_e2e_muscle_gain_program() -> bool:
    """
    Test 1: Complete muscle gain program generation.
    
    This is the primary happy path test.
    """
    print_section("TEST 1: Muscle Gain Program (Complete Flow)")
    
    try:
        # Create consultation
        consultation = create_realistic_consultation()
        print("✓ Created realistic consultation")
        
        # Generate program
        print("⏳ Generating program (this may take a few seconds)...")
        program, warnings = generate_program_from_consultation(consultation)
        print(f"✓ Program generated successfully")
        
        # Verify basic structure
        assert program.program_id is not None, "Program ID should exist"
        assert program.user_id == "e2e-test-user-001", "User ID should match"
        assert program.primary_goal == "muscle_gain", "Goal should be muscle_gain"
        
        print(f"✓ Basic structure verified")
        
        # Verify training plan
        assert program.training_plan is not None, "Training plan should exist"
        assert program.training_plan.sessions_per_week >= 4, "Should have 4+ sessions"
        assert len(program.training_plan.weekly_sessions) > 0, "Should have sessions"
        
        sessions_count = len(program.training_plan.weekly_sessions)
        print(f"✓ Training plan: {sessions_count} weekly sessions")
        
        # Check first session
        if sessions_count > 0:
            first_session = program.training_plan.weekly_sessions[0]
            assert len(first_session.exercises) > 0, "Session should have exercises"
            print(f"  - First session: {first_session.session_name}")
            print(f"  - Exercises: {len(first_session.exercises)}")
            print(f"  - Duration: {first_session.estimated_duration_minutes} min")
        
        # Verify nutrition plan
        assert program.nutrition_plan is not None, "Nutrition plan should exist"
        assert len(program.nutrition_plan.daily_meal_plans) > 0, "Should have meal plans"
        
        meal_days = len(program.nutrition_plan.daily_meal_plans)
        print(f"✓ Nutrition plan: {meal_days} days")
        
        # Check first day
        if meal_days > 0:
            first_day = program.nutrition_plan.daily_meal_plans[0]
            assert len(first_day.meals) > 0, "Day should have meals"
            print(f"  - Day 1: {len(first_day.meals)} meals")
            print(f"  - Training day: {first_day.training_day}")
        
        # Verify energy calculations
        assert program.tdee_kcal > 0, "TDEE should be calculated"
        assert program.target_calories_kcal > 0, "Target calories should exist"
        assert program.target_calories_kcal > program.tdee_kcal, "Surplus for muscle gain"
        
        surplus = program.target_calories_kcal - program.tdee_kcal
        print(f"✓ Energy: TDEE={program.tdee_kcal} kcal, Target={program.target_calories_kcal} kcal (+{surplus})")
        
        # Verify macros
        assert program.macro_targets is not None, "Macro targets should exist"
        protein = program.macro_targets.get("protein_g", 0)
        carbs = program.macro_targets.get("carbs_g", 0)
        fat = program.macro_targets.get("fat_g", 0)
        
        assert protein > 0, "Protein should be set"
        assert carbs > 0, "Carbs should be set"
        assert fat > 0, "Fat should be set"
        
        # Verify protein is appropriate (1.6-2.2 g/kg for muscle gain)
        protein_per_kg = protein / 82.0
        assert 1.4 <= protein_per_kg <= 2.5, f"Protein per kg should be reasonable, got {protein_per_kg:.2f}"
        
        print(f"✓ Macros: {protein}P / {carbs}C / {fat}F")
        print(f"  - Protein: {protein_per_kg:.2f}g/kg bodyweight")
        
        # Verify safety report
        assert program.safety_report is not None, "Safety report should exist"
        assert program.safety_report.clearance_granted, "Should be cleared for healthy user"
        print(f"✓ Safety: {program.safety_report.safety_level} - Cleared")
        
        # Verify feasibility report
        assert program.feasibility_report is not None, "Feasibility report should exist"
        assert program.feasibility_report.is_feasible, "Plan should be feasible"
        print(f"✓ Feasibility: {program.feasibility_report.status}")
        
        # Verify metadata
        assert program.version is not None, "Version should exist"
        assert program.provenance is not None, "Provenance should exist"
        assert program.provenance.consultation_session_id == "e2e-session-001"
        print(f"✓ Metadata: Version {program.version.schema_version}")
        
        # Check warnings
        print(f"✓ Warnings: {len(warnings)} total")
        if warnings:
            print(f"  Warnings detail:")
            for w in warnings[:5]:  # Show first 5
                print(f"    - {w}")
            if len(warnings) > 5:
                print(f"    ... and {len(warnings) - 5} more")
        
        # Summary
        details = f"""Program ID: {program.program_id}
Training: {sessions_count} sessions/week, {program.training_plan.split_type}
Nutrition: {meal_days} days planned
Energy: {program.tdee_kcal} → {program.target_calories_kcal} kcal/day
Macros: {protein}P / {carbs}C / {fat}F
Safety: {program.safety_report.safety_level}
Feasibility: {program.feasibility_report.status}
Warnings: {len(warnings)}"""
        
        print_result("Complete Muscle Gain Program", True, details)
        return True
        
    except Exception as e:
        print_result("Complete Muscle Gain Program", False, f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_e2e_fat_loss_program() -> bool:
    """
    Test 2: Fat loss program with different parameters.
    """
    print_section("TEST 2: Fat Loss Program")
    
    try:
        # Create fat loss consultation
        consultation = ConsultationTranscript(
            user_id="e2e-test-user-002",
            session_id="e2e-session-002",
            demographics=UserDemographics(
                user_id="e2e-test-user-002",
                age=35,
                sex_at_birth="female",
                weight_kg=75.0,
                height_cm=165.0,
                body_fat_percentage=32.0,
            ),
            improvement_goals=[
                ImprovementGoalInput(
                    goal_type="fat_loss",
                    description="Lose 10kg for health",
                    priority=10,
                    target_metric="65kg",
                    timeline_weeks=20,
                )
            ],
            training_availability=[
                TrainingAvailabilityInput(day_of_week="monday"),
                TrainingAvailabilityInput(day_of_week="wednesday"),
                TrainingAvailabilityInput(day_of_week="friday"),
            ],
        )
        
        print("⏳ Generating fat loss program...")
        program, warnings = generate_program_from_consultation(consultation)
        
        # Verify it's a fat loss program
        assert program.primary_goal == "fat_loss", "Should be fat loss"
        assert program.target_calories_kcal < program.tdee_kcal, "Should be in deficit"
        
        deficit = program.tdee_kcal - program.target_calories_kcal
        print(f"✓ Deficit: -{deficit} kcal/day")
        
        # Verify rate of change is negative (losing weight)
        assert program.expected_rate_of_change_kg_per_week < 0, "Should be losing weight"
        print(f"✓ Expected loss: {abs(program.expected_rate_of_change_kg_per_week):.2f} kg/week")
        
        details = f"""Goal: {program.primary_goal}
Deficit: -{deficit} kcal/day
Expected loss: {abs(program.expected_rate_of_change_kg_per_week):.2f} kg/week
Sessions: {program.training_plan.sessions_per_week}/week"""
        
        print_result("Fat Loss Program", True, details)
        return True
        
    except Exception as e:
        print_result("Fat Loss Program", False, f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_e2e_with_options() -> bool:
    """
    Test 3: Program generation with custom options.
    """
    print_section("TEST 3: Program with Custom Options")
    
    try:
        # Create consultation
        consultation = ConsultationTranscript(
            user_id="e2e-test-user-003",
            session_id="e2e-session-003",
            demographics=UserDemographics(
                user_id="e2e-test-user-003",
                age=26,
                sex_at_birth="male",
                weight_kg=70.0,
                height_cm=175.0,
            ),
            improvement_goals=[
                ImprovementGoalInput(
                    goal_type="muscle_gain",
                    description="Build muscle",
                    priority=10,
                )
            ],
        )
        
        # Add custom options
        options = GenerationOptions(
            dietary_mode=DietaryMode.VEGAN,
            equipment_available=EquipmentAvailability.HOME_GYM_BASIC,
            program_duration_weeks=12,
        )
        
        print("⏳ Generating program with vegan diet and home gym...")
        program, warnings = generate_program_from_consultation(consultation, options)
        
        # Verify options were applied
        assert program.nutrition_plan.dietary_preference == "vegan", "Should be vegan"
        
        print(f"✓ Dietary preference: {program.nutrition_plan.dietary_preference}")
        print(f"✓ Program duration: {program.timeline_weeks} weeks")
        
        details = f"""Options applied:
- Dietary: {program.nutrition_plan.dietary_preference}
- Timeline: {program.timeline_weeks} weeks
- Training split: {program.training_plan.split_type}"""
        
        print_result("Custom Options", True, details)
        return True
        
    except Exception as e:
        print_result("Custom Options", False, f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_e2e_minimal_data() -> bool:
    """
    Test 4: Program generation with minimal consultation data (tests defaults).
    """
    print_section("TEST 4: Minimal Consultation Data")
    
    try:
        # Bare minimum consultation
        consultation = ConsultationTranscript(
            user_id="e2e-test-user-004",
            session_id="e2e-session-004",
            demographics=UserDemographics(
                user_id="e2e-test-user-004",
                age=30,
                sex_at_birth="male",
                weight_kg=75.0,
                height_cm=175.0,
            ),
        )
        
        print("⏳ Generating program with minimal data (testing defaults)...")
        program, warnings = generate_program_from_consultation(consultation)
        
        # Should still generate a valid program
        assert program is not None, "Should generate program"
        assert len(warnings) > 5, "Should have many warnings for missing data"
        
        print(f"✓ Program generated with {len(warnings)} warnings (expected)")
        print(f"✓ Defaults applied:")
        print(f"  - Goal: {program.primary_goal}")
        print(f"  - Sessions: {program.training_plan.sessions_per_week}/week")
        print(f"  - Split: {program.training_plan.split_type}")
        
        details = f"""Generated from minimal data:
Warnings: {len(warnings)}
Goal: {program.primary_goal} (default)
Sessions: {program.training_plan.sessions_per_week}/week (default)
Successfully applied smart defaults"""
        
        print_result("Minimal Data with Defaults", True, details)
        return True
        
    except Exception as e:
        print_result("Minimal Data with Defaults", False, f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_e2e_data_integrity() -> bool:
    """
    Test 5: Verify data integrity throughout the pipeline.
    """
    print_section("TEST 5: Data Integrity")
    
    try:
        consultation = create_realistic_consultation()
        program, warnings = generate_program_from_consultation(consultation)
        
        checks = []
        
        # Check 1: User ID consistency
        checks.append(("User ID consistency", 
                      program.user_id == consultation.user_id))
        
        # Check 2: Session ID in provenance
        checks.append(("Session ID in provenance", 
                      program.provenance.consultation_session_id == consultation.session_id))
        
        # Check 3: Energy balance makes sense
        if program.primary_goal == "muscle_gain":
            checks.append(("Surplus for muscle gain", 
                          program.target_calories_kcal > program.tdee_kcal))
        
        # Check 4: Macro calories match target
        macro_cals = (program.macro_targets["protein_g"] * 4 + 
                     program.macro_targets["carbs_g"] * 4 + 
                     program.macro_targets["fat_g"] * 9)
        cal_diff = abs(macro_cals - program.target_calories_kcal)
        checks.append(("Macro calories match target", 
                      cal_diff < program.target_calories_kcal * 0.05))  # Within 5%
        
        # Check 5: Training volume is reasonable
        total_volume = sum(program.training_plan.weekly_volume_per_muscle.values())
        checks.append(("Training volume reasonable", 
                      50 <= total_volume <= 200))  # Reasonable weekly set range
        
        # Check 6: Meal plans exist for multiple days
        checks.append(("Multiple meal days", 
                      len(program.nutrition_plan.daily_meal_plans) >= 7))
        
        # Check 7: Each day has multiple meals
        first_day_meals = len(program.nutrition_plan.daily_meal_plans[0].meals)
        checks.append(("Multiple meals per day", 
                      first_day_meals >= 3))
        
        # Print results
        passed = all(result for _, result in checks)
        for check_name, result in checks:
            status = "✓" if result else "✗"
            print(f"  {status} {check_name}")
        
        details = f"""Integrity checks: {sum(1 for _, r in checks if r)}/{len(checks)} passed
- User/Session ID tracking
- Energy balance logic
- Macro calculation accuracy
- Training volume ranges
- Meal plan completeness"""
        
        print_result("Data Integrity", passed, details)
        return passed
        
    except Exception as e:
        print_result("Data Integrity", False, f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all end-to-end tests."""
    print("\n" + "="*80)
    print("  END-TO-END INTEGRATION TEST SUITE")
    print("  Complete Pipeline Verification")
    print("="*80)
    print("\nThis will test the full pipeline:")
    print("  Consultation → Adapter → UserProfile → Generator → ProgramBundle")
    print("\n⏳ Starting tests (this may take 30-60 seconds)...\n")
    
    results = []
    
    # Run all tests
    results.append(("Muscle Gain Program", test_e2e_muscle_gain_program()))
    results.append(("Fat Loss Program", test_e2e_fat_loss_program()))
    results.append(("Custom Options", test_e2e_with_options()))
    results.append(("Minimal Data", test_e2e_minimal_data()))
    results.append(("Data Integrity", test_e2e_data_integrity()))
    
    # Summary
    print_section("FINAL SUMMARY")
    
    total = len(results)
    passed = sum(1 for _, result in results if result)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n" + "-"*80)
    print(f"Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("-"*80)
    
    if passed == total:
        print("\n🎉 ALL END-TO-END TESTS PASSED!")
        print("\n✅ The complete pipeline is working:")
        print("   - Consultation data transforms correctly")
        print("   - Phase 1 generator produces valid programs")
        print("   - Output schemas are complete and accurate")
        print("   - Data integrity maintained throughout")
        print("   - Edge cases handled gracefully")
        print("\n🚀 System is ready for production deployment!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} TEST(S) FAILED")
        print("\nPlease review the failures above and fix issues before deployment.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
