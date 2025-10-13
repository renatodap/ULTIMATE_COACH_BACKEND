"""
Pydantic models for activity tracking.

Handles validation for diverse activity types with flexible metrics.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

# Category-specific METs ranges for realistic intensity validation
METS_RANGES = {
    'cardio_steady_state': (3.0, 15.0),    # Walking to running
    'cardio_interval': (5.0, 18.0),        # HIIT, sprints
    'strength_training': (3.0, 8.0),       # Weight lifting
    'sports': (4.0, 12.0),                 # Tennis, basketball, etc.
    'flexibility': (1.5, 4.0),             # Yoga, stretching
    'other': (1.0, 20.0)                   # Full range for unknown activities
}


class ActivityBase(BaseModel):
    """Base activity fields shared across create/update operations."""

    category: str = Field(
        ...,
        description="Activity category (cardio_steady_state, strength_training, etc.)"
    )
    activity_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Custom activity name (e.g., 'Morning Run', 'Leg Day')"
    )
    start_time: datetime = Field(..., description="Activity start time (ISO 8601)")
    end_time: Optional[datetime] = Field(None, description="Activity end time (ISO 8601)")
    duration_minutes: Optional[int] = Field(
        None,
        ge=1,
        le=1440,  # Max 24 hours
        description="Duration in minutes (calculated from times or manual)"
    )
    calories_burned: int = Field(
        ...,
        ge=0,
        le=10000,  # Sanity check
        description="Calories burned during activity"
    )
    intensity_mets: float = Field(
        ...,
        ge=1.0,
        le=20.0,
        description="Metabolic Equivalent of Task (1.0=rest, 8.0=running)"
    )
    metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Activity-specific metrics (distance, HR, exercises, etc.)"
    )
    notes: Optional[str] = Field(
        None,
        max_length=500,
        description="User notes about the activity"
    )

    @validator('category')
    def validate_category(cls, v):
        """Validate activity category against allowed values."""
        valid_categories = [
            'cardio_steady_state',
            'cardio_interval',
            'strength_training',
            'sports',
            'flexibility',
            'other'
        ]
        if v not in valid_categories:
            raise ValueError(
                f"Category must be one of {valid_categories}, got '{v}'"
            )
        return v

    @validator('end_time')
    def validate_end_time(cls, v, values):
        """Ensure end_time is after start_time."""
        if v and 'start_time' in values:
            if v <= values['start_time']:
                raise ValueError("end_time must be after start_time")
        return v

    @validator('intensity_mets')
    def validate_intensity_mets(cls, v, values):
        """
        Validate METs value is realistic for the activity category.

        Provides category-specific validation to catch unrealistic intensity values.
        Logs warnings for values outside typical range but allows them (user may have edge cases).
        """
        category = values.get('category')
        if not category:
            return v  # Category validation will catch this

        min_mets, max_mets = METS_RANGES.get(category, (1.0, 20.0))

        if v < min_mets or v > max_mets:
            logger.warning(
                f"Unusual METs value for {category}: {v} "
                f"(typical range: {min_mets}-{max_mets})"
            )
            # Note: We log but don't raise - user might have legitimate edge cases
            # e.g., very light yoga (1.5) or extreme HIIT (18.0)

        return v

    @validator('duration_minutes')
    def validate_duration(cls, v, values):
        """
        Warn if both duration and end_time are provided (potential conflict).

        Duration can be calculated from start_time + end_time OR manually entered.
        If both exist, service layer will recalculate from times.
        """
        if v and values.get('end_time'):
            logger.info(
                "Both duration_minutes and end_time provided - "
                "duration will be recalculated from timestamps"
            )
        return v


class CreateActivityRequest(ActivityBase):
    """Request model for creating a new activity."""
    pass


class UpdateActivityRequest(BaseModel):
    """Request model for updating an activity (all fields optional)."""

    activity_name: Optional[str] = Field(None, min_length=1, max_length=100)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=1, le=1440)
    calories_burned: Optional[int] = Field(None, ge=0, le=10000)
    intensity_mets: Optional[float] = Field(None, ge=1.0, le=20.0)
    metrics: Optional[Dict[str, Any]] = None
    notes: Optional[str] = Field(None, max_length=500)

    @validator('end_time')
    def validate_end_time(cls, v, values):
        """Ensure end_time is after start_time if both provided."""
        if v and 'start_time' in values and values['start_time']:
            if v <= values['start_time']:
                raise ValueError("end_time must be after start_time")
        return v


class Activity(BaseModel):
    """Full activity response with database fields."""

    id: UUID = Field(..., description="Activity UUID")
    user_id: UUID = Field(..., description="User UUID who created the activity")
    category: str
    activity_name: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_minutes: int
    calories_burned: int
    intensity_mets: float
    metrics: Dict[str, Any]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config for ORM mode."""
        from_attributes = True


class DailySummary(BaseModel):
    """Daily activity summary with aggregated statistics."""

    total_calories_burned: int = Field(
        ...,
        description="Total calories burned today"
    )
    total_duration_minutes: int = Field(
        ...,
        description="Total activity duration in minutes"
    )
    average_intensity: float = Field(
        ...,
        description="Average METs across all activities"
    )
    activity_count: int = Field(
        ...,
        description="Number of activities logged today"
    )
    daily_goal_calories: int = Field(
        ...,
        description="User's daily calorie burn goal"
    )
    goal_percentage: float = Field(
        ...,
        description="Progress toward daily goal (0-100+)"
    )


class ActivityListResponse(BaseModel):
    """Paginated activity list response."""

    activities: List[Activity]
    total: int
    limit: int
    offset: int


class SuccessResponse(BaseModel):
    """Generic success response."""

    success: bool = True
    message: str
