"""
Pydantic models for exercise sets tracking.

Models for individual set tracking in strength training activities.
"""

from pydantic import BaseModel, Field, model_validator
from typing import Optional
from uuid import UUID
from datetime import datetime


class ExerciseSetBase(BaseModel):
    """Base model for exercise sets"""
    exercise_id: UUID = Field(..., description="Exercise ID from exercises table")
    set_number: int = Field(..., ge=1, le=50, description="Set number (1-50)")

    # Weight-based sets
    reps: Optional[int] = Field(None, ge=1, le=1000, description="Number of reps")
    weight_kg: Optional[float] = Field(None, ge=0, le=1000, description="Weight in kg")

    # Time/distance based sets (for cardio/bodyweight)
    duration_seconds: Optional[int] = Field(None, ge=1, le=3600, description="Duration in seconds")
    distance_meters: Optional[float] = Field(None, gt=0, description="Distance in meters")

    # Performance tracking
    rpe: Optional[int] = Field(None, ge=1, le=10, description="Rate of Perceived Exertion (1-10)")
    tempo: Optional[str] = Field(None, max_length=20, description="Tempo (e.g., 3-1-2-0)")
    rest_seconds: Optional[int] = Field(None, ge=0, le=600, description="Rest after set (seconds)")

    # Completion tracking
    completed: bool = Field(True, description="Whether set was completed")
    failure: bool = Field(False, description="Whether set went to failure")
    notes: Optional[str] = Field(None, max_length=500, description="Set notes")

    @model_validator(mode='after')
    def validate_set_data(self):
        """
        Ensure at least one type of set data is provided.
        Must have either:
        - reps + weight_kg
        - duration_seconds
        - distance_meters
        """
        has_reps_weight = self.reps is not None and self.weight_kg is not None
        has_duration = self.duration_seconds is not None
        has_distance = self.distance_meters is not None

        if not (has_reps_weight or has_duration or has_distance):
            raise ValueError(
                "Must provide either (reps + weight_kg), duration_seconds, or distance_meters"
            )
        return self


class CreateExerciseSetRequest(ExerciseSetBase):
    """Request model for creating an exercise set"""
    activity_id: UUID = Field(..., description="Activity this set belongs to")


class UpdateExerciseSetRequest(BaseModel):
    """Request model for updating an exercise set (all fields optional)"""
    set_number: Optional[int] = Field(None, ge=1, le=50)
    reps: Optional[int] = Field(None, ge=1, le=1000)
    weight_kg: Optional[float] = Field(None, ge=0, le=1000)
    duration_seconds: Optional[int] = Field(None, ge=1, le=3600)
    distance_meters: Optional[float] = Field(None, gt=0)
    rpe: Optional[int] = Field(None, ge=1, le=10)
    tempo: Optional[str] = Field(None, max_length=20)
    rest_seconds: Optional[int] = Field(None, ge=0, le=600)
    completed: Optional[bool] = None
    failure: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=500)


class ExerciseSet(ExerciseSetBase):
    """Complete exercise set model (response)"""
    id: UUID
    activity_id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExerciseSetWithDetails(ExerciseSet):
    """Exercise set with exercise details included"""
    exercise_name: str
    exercise_category: str
    primary_muscle_groups: list[str]


class ExerciseSearchResult(BaseModel):
    """Search result for exercises"""
    id: UUID
    name: str
    description: Optional[str]
    category: str
    primary_muscle_groups: list[str]
    equipment_needed: list[str]
    difficulty_level: Optional[str]
    usage_count: int
    rank: Optional[float] = Field(None, description="Search relevance rank")

    class Config:
        from_attributes = True


class PersonalRecord(BaseModel):
    """Personal record for an exercise"""
    user_id: UUID
    exercise_id: UUID
    max_weight_kg: Optional[float] = None
    max_weight_reps: Optional[int] = None
    max_weight_date: Optional[datetime] = None
    max_estimated_1rm: Optional[float] = None
    max_1rm_date: Optional[datetime] = None
    max_set_volume: Optional[float] = None
    max_volume_date: Optional[datetime] = None

    class Config:
        from_attributes = True


class ExerciseHistory(BaseModel):
    """Exercise history record"""
    user_id: UUID
    exercise_id: UUID
    exercise_name: str
    category: str
    activity_id: UUID
    activity_name: str
    start_time: datetime
    set_number: int
    reps: Optional[int]
    weight_kg: Optional[float]
    duration_seconds: Optional[int]
    distance_meters: Optional[float]
    rpe: Optional[int]
    completed: bool
    estimated_1rm: Optional[float] = Field(None, description="Estimated 1RM using Epley formula")
    set_volume: Optional[float] = Field(None, description="Total volume (reps × weight)")

    class Config:
        from_attributes = True


class BulkCreateExerciseSetsRequest(BaseModel):
    """Request to create multiple exercise sets at once"""
    activity_id: UUID = Field(..., description="Activity these sets belong to")
    sets: list[ExerciseSetBase] = Field(..., min_items=1, max_items=100)


class ExerciseSetsResponse(BaseModel):
    """Response containing multiple exercise sets"""
    sets: list[ExerciseSet]
    total: int


class SuccessResponse(BaseModel):
    """Generic success response"""
    success: bool
    message: str
