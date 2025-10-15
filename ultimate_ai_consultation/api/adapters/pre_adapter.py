"""
Pre-Adapter: Build ConsultationTranscript from App State

Utility to construct a ConsultationTranscript using existing user data
from the main app (metrics, logs, activities, foods) so plan generation
can leverage real user context without manual re-entry.

This module runs entirely inside the consultation package and does not
perform any network/database IO — call it from the backend where you
already have the data and then pass the transcript to the generator.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional

from api.schemas.inputs import (
    ConsultationTranscript,
    UserDemographics,
    TrainingAvailabilityInput,
    TypicalMealFoodInput,
    ImprovementGoalInput,
    UpcomingEventInput,
    ModalityPreferenceInput,
    FacilityAccessInput,
)


def build_transcript_from_app_state(
    user_id: str,
    session_id: str,
    app_state: Dict[str, Any],
) -> ConsultationTranscript:
    """
    Construct a ConsultationTranscript from an app_state dict.

    Expected keys (optional):
    - demographics: {age, sex_at_birth, weight_kg, height_cm, body_fat_percentage}
    - availability: [{day_of_week, time_of_day[], duration_minutes}]
    - foods: [{food_name, meal_time, frequency}]
    - goals: [{goal_type, description, priority, timeline_weeks, target_metric}]
    - events: [{event_name, event_type, weeks_until, event_date}]
    - modalities: [{modality, priority, target_sessions_per_week, seriousness, seriousness_score, facility_needed}]
    - facilities: [{facility_type, days_available, notes}]
    - cardio_preference: "avoid"|"neutral"|"prefer"
    """
    demo = app_state.get("demographics", {})
    demographics = UserDemographics(
        user_id=user_id,
        age=int(demo.get("age", 30)),
        sex_at_birth=str(demo.get("sex_at_birth", "male")),
        weight_kg=float(demo.get("weight_kg", 75.0)),
        height_cm=float(demo.get("height_cm", 175.0)),
        body_fat_percentage=demo.get("body_fat_percentage"),
    )

    availability = [
        TrainingAvailabilityInput(
            day_of_week=entry.get("day_of_week", "monday"),
            time_of_day=entry.get("time_of_day", []),
            duration_minutes=entry.get("duration_minutes"),
        )
        for entry in app_state.get("availability", [])
    ]

    foods = [
        TypicalMealFoodInput(
            food_name=f.get("food_name", "Chicken"),
            meal_time=f.get("meal_time", "dinner"),
            frequency=f.get("frequency", "weekly"),
        )
        for f in app_state.get("foods", [])
    ]

    goals = [
        ImprovementGoalInput(
            goal_type=g.get("goal_type", "muscle_gain"),
            description=g.get("description", ""),
            priority=int(g.get("priority", 5)),
            target_metric=g.get("target_metric"),
            timeline_weeks=g.get("timeline_weeks"),
        )
        for g in app_state.get("goals", [])
    ]

    events = [
        UpcomingEventInput(
            event_name=e.get("event_name", "Race"),
            event_type=e.get("event_type", "race"),
            weeks_until=e.get("weeks_until"),
            event_date=e.get("event_date"),
        )
        for e in app_state.get("events", [])
    ]

    modalities = [
        ModalityPreferenceInput(
            modality=m.get("modality", "running"),
            priority=int(m.get("priority", 5)),
            target_sessions_per_week=m.get("target_sessions_per_week"),
            min_duration_minutes=m.get("min_duration_minutes"),
            max_duration_minutes=m.get("max_duration_minutes"),
            facility_needed=m.get("facility_needed"),
            intensity_preference=m.get("intensity_preference"),
            seriousness=m.get("seriousness"),
            seriousness_score=m.get("seriousness_score"),
        )
        for m in app_state.get("modalities", [])
    ]

    facilities = [
        FacilityAccessInput(
            facility_type=f.get("facility_type", "court"),
            days_available=f.get("days_available", []),
            notes=f.get("notes"),
        )
        for f in app_state.get("facilities", [])
    ]

    transcript = ConsultationTranscript(
        user_id=user_id,
        session_id=session_id,
        completed_at=datetime.now(),
        demographics=demographics,
        training_availability=availability,
        typical_foods=foods,
        improvement_goals=goals,
        upcoming_events=events,
        modality_preferences=modalities,
        facility_access=facilities,
        conversation_summary=app_state.get("conversation_summary"),
        # Global stance on cardio
        cardio_preference=app_state.get("cardio_preference"),
    )

    return transcript

