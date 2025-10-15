"""
Unit tests for ModalityPlanner (Phase A).
"""

from services.program_generator.modality_planner import (
    ModalityPlanner,
    ModalityPreference,
    FacilityAccess,
)


def test_planner_basic_running_and_tennis():
    planner = ModalityPlanner()
    prefs = [
        ModalityPreference(modality="running", priority=9, target_sessions_per_week=2, intensity_preference="moderate"),
        ModalityPreference(modality="tennis", priority=8, target_sessions_per_week=1, facility_needed="court"),
    ]
    facilities = [FacilityAccess(facility_type="court", days_available=["saturday", "sunday"])]

    sessions = planner.plan_week(
        preferences=prefs,
        available_days=["monday", "wednesday", "saturday"],
        resistance_sessions_per_week=4,
        facility_access=facilities,
    )

    # Headroom with 4x lifting is 2 extra sessions; ensure we get at most 2
    assert 0 < len(sessions) <= 2

    # If tennis is scheduled, it should land on a facility day
    tennis_days = [s.day_of_week for s in sessions if s.modality == "tennis"]
    for d in tennis_days:
        assert d in ["saturday", "sunday"]

