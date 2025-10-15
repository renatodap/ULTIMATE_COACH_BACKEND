"""
E2E test: verifies multimodal sessions are attached when preferences are provided.
"""

from datetime import datetime

from api import generate_program_from_consultation
from api.schemas.inputs import (
    ConsultationTranscript,
    UserDemographics,
    TrainingAvailabilityInput,
    ImprovementGoalInput,
    ModalityPreferenceInput,
    FacilityAccessInput,
)


def test_e2e_multimodal_sessions_present():
    consultation = ConsultationTranscript(
        user_id="e2e-multi-user-001",
        session_id="e2e-multi-session-001",
        completed_at=datetime.now(),
        demographics=UserDemographics(
            user_id="e2e-multi-user-001",
            age=30,
            sex_at_birth="male",
            weight_kg=80.0,
            height_cm=180.0,
        ),
        training_availability=[
            TrainingAvailabilityInput(day_of_week="monday", time_of_day=["evening"], duration_minutes=90),
            TrainingAvailabilityInput(day_of_week="wednesday", time_of_day=["evening"], duration_minutes=90),
            TrainingAvailabilityInput(day_of_week="friday", time_of_day=["evening"], duration_minutes=90),
        ],
        improvement_goals=[
            ImprovementGoalInput(goal_type="muscle_gain", description="Build muscle", priority=10, timeline_weeks=12),
        ],
        facility_access=[
            FacilityAccessInput(facility_type="court", days_available=["saturday", "sunday"]),
        ],
        modality_preferences=[
            ModalityPreferenceInput(modality="running", priority=9, target_sessions_per_week=1, intensity_preference="moderate"),
            ModalityPreferenceInput(modality="tennis", priority=7, target_sessions_per_week=1, facility_needed="court"),
        ],
    )

    program, warnings = generate_program_from_consultation(consultation)

    # multimodal should exist and include 1-2 sessions depending on headroom
    assert program.multimodal_sessions_weekly is not None
    assert 1 <= len(program.multimodal_sessions_weekly) <= 3

