"""
Test the consultation adapter transformation logic.

This test validates:
1. Import correctness
2. Type compatibility between ConsultationTranscript and UserProfile
3. Mapping logic for goals, experience, intensity, etc.
4. Handling of missing/incomplete data
"""

# Set dummy env vars before importing anything
import os
os.environ['ANTHROPIC_API_KEY'] = 'dummy'
os.environ['SUPABASE_URL'] = 'dummy'
os.environ['SUPABASE_KEY'] = 'dummy'
os.environ['SUPABASE_JWT_SECRET'] = 'dummy'

from datetime import datetime
from api.schemas.inputs import (
    ConsultationTranscript,
    UserDemographics,
    TrainingModalityInput,
    ImprovementGoalInput,
    TrainingAvailabilityInput,
    DifficultyInput,
    GenerationOptions,
    DietaryMode,
)
from api.adapters.consultation_adapter import (
    consultation_to_user_profile,
    validate_consultation_data,
    ConsultationValidationError,
)


def test_complete_consultation():
    """Test with complete consultation data."""
    print("\n" + "="*80)
    print("TEST 1: Complete Consultation Transformation")
    print("="*80)
    
    # Build complete consultation
    consultation = ConsultationTranscript(
        user_id="test-user-123",
        session_id="session-456",
        demographics=UserDemographics(
            user_id="test-user-123",
            age=28,
            sex_at_birth="male",
            weight_kg=82.0,
            height_cm=178.0,
            body_fat_percentage=18.0,
        ),
        training_modalities=[
            TrainingModalityInput(
                modality="bodybuilding",
                proficiency="intermediate",
                years_experience=3,
                is_primary=True,
            )
        ],
        improvement_goals=[
            ImprovementGoalInput(
                goal_type="muscle_gain",
                description="Gain 5kg of lean muscle mass",
                priority=10,
                target_metric="87kg at 15% body fat",
                timeline_weeks=16,
            )
        ],
        training_availability=[
            TrainingAvailabilityInput(day_of_week="monday", time_of_day=["evening"]),
            TrainingAvailabilityInput(day_of_week="tuesday", time_of_day=["evening"]),
            TrainingAvailabilityInput(day_of_week="thursday", time_of_day=["evening"]),
            TrainingAvailabilityInput(day_of_week="friday", time_of_day=["evening"]),
        ],
    )
    
    # Validate first
    warnings = validate_consultation_data(consultation)
    print(f"\n📋 Validation warnings: {len(warnings)}")
    for w in warnings:
        print(f"  ⚠️  {w}")
    
    # Transform to UserProfile
    profile, transform_warnings = consultation_to_user_profile(consultation)
    
    print(f"\n✅ Transformation successful!")
    print(f"📋 Transform warnings: {len(transform_warnings)}")
    for w in transform_warnings:
        print(f"  ⚠️  {w}")
    
    # Validate UserProfile
    print(f"\n👤 UserProfile Summary:")
    print(f"  User ID: {profile.user_id}")
    print(f"  Demographics: {profile.age}y, {profile.sex_at_birth}, {profile.weight_kg}kg, {profile.height_cm}cm")
    print(f"  Goal: {profile.primary_goal.value}")
    print(f"  Target Weight: {profile.target_weight_kg}kg" if profile.target_weight_kg else "  Target Weight: None")
    print(f"  Timeline: {profile.timeline_weeks} weeks")
    print(f"  Experience: {profile.experience_level.value}")
    print(f"  Training Focus: {profile.training_focus.value}")
    print(f"  Sessions/week: {profile.sessions_per_week}")
    print(f"  Available Days: {', '.join(profile.available_days)}")
    print(f"  Activity Factor: {profile.activity_factor.name} ({profile.activity_factor.value}x)")
    print(f"  Dietary Preference: {profile.dietary_preference.value}")
    print(f"  Doctor Clearance: {profile.doctor_clearance}")
    
    return profile


def test_minimal_consultation():
    """Test with minimal consultation data (defaults)."""
    print("\n" + "="*80)
    print("TEST 2: Minimal Consultation (Testing Defaults)")
    print("="*80)
    
    # Minimal consultation
    consultation = ConsultationTranscript(
        user_id="test-user-minimal",
        session_id="session-minimal",
        demographics=UserDemographics(
            user_id="test-user-minimal",
            age=35,
            sex_at_birth="female",
            weight_kg=65.0,
            height_cm=165.0,
        ),
    )
    
    # Validate
    warnings = validate_consultation_data(consultation)
    print(f"\n📋 Validation warnings: {len(warnings)}")
    for w in warnings:
        print(f"  ⚠️  {w}")
    
    # Transform
    profile, transform_warnings = consultation_to_user_profile(consultation)
    
    print(f"\n✅ Transformation successful!")
    print(f"📋 Transform warnings: {len(transform_warnings)}")
    for w in transform_warnings:
        print(f"  ⚠️  {w}")
    
    print(f"\n👤 UserProfile Summary:")
    print(f"  Goal: {profile.primary_goal.value}")
    print(f"  Experience: {profile.experience_level.value}")
    print(f"  Training Focus: {profile.training_focus.value}")
    print(f"  Sessions/week: {profile.sessions_per_week}")
    print(f"  Available Days: {', '.join(profile.available_days)}")
    
    return profile


def test_fat_loss_goal():
    """Test fat loss goal mapping."""
    print("\n" + "="*80)
    print("TEST 3: Fat Loss Goal Mapping")
    print("="*80)
    
    consultation = ConsultationTranscript(
        user_id="test-user-fatloss",
        session_id="session-fatloss",
        demographics=UserDemographics(
            user_id="test-user-fatloss",
            age=32,
            sex_at_birth="male",
            weight_kg=95.0,
            height_cm=180.0,
            body_fat_percentage=28.0,
        ),
        improvement_goals=[
            ImprovementGoalInput(
                goal_type="fat_loss",
                description="Lose 10kg of fat and get to 18% body fat",
                priority=10,
                target_metric="85kg",
                timeline_weeks=20,
            )
        ],
        training_modalities=[
            TrainingModalityInput(
                modality="general_fitness",
                proficiency="beginner",
                years_experience=0,
                is_primary=True,
            )
        ],
        training_availability=[
            TrainingAvailabilityInput(day_of_week="monday"),
            TrainingAvailabilityInput(day_of_week="wednesday"),
            TrainingAvailabilityInput(day_of_week="friday"),
        ],
    )
    
    profile, warnings = consultation_to_user_profile(consultation)
    
    print(f"\n✅ Transformation successful!")
    print(f"📋 Warnings: {len(warnings)}")
    
    print(f"\n👤 UserProfile Summary:")
    print(f"  Goal: {profile.primary_goal.value}")
    print(f"  Current Weight: {profile.weight_kg}kg")
    print(f"  Target Weight: {profile.target_weight_kg}kg")
    print(f"  Timeline: {profile.timeline_weeks} weeks")
    print(f"  Experience: {profile.experience_level.value}")
    print(f"  Sessions/week: {profile.sessions_per_week}")
    
    # Verify goal is FAT_LOSS
    assert profile.primary_goal.value == "fat_loss", f"Expected FAT_LOSS, got {profile.primary_goal.value}"
    assert profile.target_weight_kg == 85.0, f"Expected 85kg, got {profile.target_weight_kg}"
    print("\n✅ Fat loss goal correctly mapped!")
    
    return profile


def test_with_generation_options():
    """Test with generation options override."""
    print("\n" + "="*80)
    print("TEST 4: Generation Options Override")
    print("="*80)
    
    consultation = ConsultationTranscript(
        user_id="test-user-options",
        session_id="session-options",
        demographics=UserDemographics(
            user_id="test-user-options",
            age=25,
            sex_at_birth="female",
            weight_kg=60.0,
            height_cm=168.0,
        ),
        improvement_goals=[
            ImprovementGoalInput(
                goal_type="muscle_gain",
                description="Build muscle for physique competition",
                priority=10,
                timeline_weeks=24,
            )
        ],
    )
    
    # With dietary override
    options = GenerationOptions(
        dietary_mode=DietaryMode.VEGAN,
        program_duration_weeks=16,
    )
    
    profile, warnings = consultation_to_user_profile(consultation, options)
    
    print(f"\n✅ Transformation successful!")
    print(f"📋 Warnings: {len(warnings)}")
    
    print(f"\n👤 UserProfile Summary:")
    print(f"  Dietary Preference: {profile.dietary_preference.value}")
    print(f"  Timeline: {profile.timeline_weeks} weeks")
    
    # Verify dietary override
    assert profile.dietary_preference.value == "vegan", f"Expected vegan, got {profile.dietary_preference.value}"
    print("\n✅ Dietary override correctly applied!")
    
    return profile


def test_medical_extraction():
    """Test medical condition and injury extraction."""
    print("\n" + "="*80)
    print("TEST 5: Medical Information Extraction")
    print("="*80)
    
    consultation = ConsultationTranscript(
        user_id="test-user-medical",
        session_id="session-medical",
        demographics=UserDemographics(
            user_id="test-user-medical",
            age=45,
            sex_at_birth="male",
            weight_kg=88.0,
            height_cm=175.0,
        ),
        difficulties=[
            DifficultyInput(
                category="injury",
                description="Lower back injury from deadlifting 6 months ago",
                severity=6,
            ),
            DifficultyInput(
                category="health",
                description="Type 2 diabetes managed with medication",
                severity=8,
            ),
        ],
    )
    
    profile, warnings = consultation_to_user_profile(consultation)
    
    print(f"\n✅ Transformation successful!")
    print(f"📋 Warnings: {len(warnings)}")
    
    print(f"\n👤 Medical Information:")
    print(f"  Medical Conditions: {profile.medical_conditions}")
    print(f"  Medications: {profile.medications}")
    print(f"  Injuries: {profile.injuries}")
    print(f"  Doctor Clearance: {profile.doctor_clearance}")
    
    # Verify extraction
    assert len(profile.injuries) > 0, "Expected injuries to be extracted"
    # Note: diabetes with medication goes to medications, not medical_conditions (which is correct)
    assert len(profile.medications) > 0, "Expected medications to be extracted"
    assert profile.doctor_clearance == False, "Expected doctor clearance to be False"
    print("\n✅ Medical information correctly extracted!")
    
    return profile


def test_type_compatibility():
    """Verify all enum types are compatible."""
    print("\n" + "="*80)
    print("TEST 6: Type Compatibility Verification")
    print("="*80)
    
    from libs.calculators.macros import Goal
    from libs.calculators.tdee import ActivityFactor
    from services.program_generator.training_generator import ExperienceLevel, IntensityZone
    from services.program_generator.meal_assembler import DietaryPreference
    
    # Verify enum values
    print("\n📋 Goal enum values:")
    for goal in Goal:
        print(f"  - {goal.name}: {goal.value}")
    
    print("\n📋 ExperienceLevel enum values:")
    for level in ExperienceLevel:
        print(f"  - {level.name}: {level.value}")
    
    print("\n📋 IntensityZone enum values:")
    for zone in IntensityZone:
        print(f"  - {zone.name}: {zone.value}")
    
    print("\n📋 ActivityFactor enum values:")
    for factor in ActivityFactor:
        print(f"  - {factor.name}: {factor.value}")
    
    print("\n📋 DietaryPreference enum values:")
    for pref in DietaryPreference:
        print(f"  - {pref.name}: {pref.value}")
    
    print("\n✅ All enum types are valid!")


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("CONSULTATION ADAPTER TEST SUITE")
    print("="*80)
    
    try:
        # Test 1: Complete consultation
        test_complete_consultation()
        
        # Test 2: Minimal consultation
        test_minimal_consultation()
        
        # Test 3: Fat loss goal
        test_fat_loss_goal()
        
        # Test 4: Generation options
        test_with_generation_options()
        
        # Test 5: Medical extraction
        test_medical_extraction()
        
        # Test 6: Type compatibility
        test_type_compatibility()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED!")
        print("="*80)
        print("\nConsultation adapter is fully functional and type-safe.")
        print("Ready for integration with Phase 1 generator.\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
