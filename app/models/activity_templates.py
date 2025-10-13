"""
Pydantic models for activity templates.

Templates are user-defined patterns for recurring workouts with auto-matching capability.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime, time
from uuid import UUID
import structlog

logger = structlog.get_logger()

# Valid activity types (must match database constraint and activities table)
VALID_ACTIVITY_TYPES = [
    'running',
    'cycling',
    'swimming',
    'strength_training',
    'yoga',
    'walking',
    'hiking',
    'sports',
    'flexibility',
    'cardio_steady_state',
    'cardio_interval',
    'other'
]


class TemplateBase(BaseModel):
    """Base template fields shared across create/update operations."""

    template_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Template name (e.g., 'Morning 5K Route', 'Leg Day')"
    )
    activity_type: str = Field(
        ...,
        description="Activity type (running, cycling, strength_training, etc.)"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Template description/notes"
    )
    icon: str = Field(
        default='🏃',
        max_length=10,
        description="Emoji icon for template"
    )

    # Expected ranges for auto-matching
    expected_distance_m: Optional[float] = Field(
        None,
        gt=0,
        description="Expected distance in meters"
    )
    distance_tolerance_percent: int = Field(
        default=10,
        ge=0,
        le=100,
        description="Distance matching tolerance (±%)"
    )
    expected_duration_minutes: Optional[int] = Field(
        None,
        gt=0,
        description="Expected duration in minutes"
    )
    duration_tolerance_percent: int = Field(
        default=15,
        ge=0,
        le=100,
        description="Duration matching tolerance (±%)"
    )

    # Pre-filled data for manual logs
    default_exercises: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Default exercises for strength training templates"
    )
    default_metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Default metrics (distance, HR, etc.)"
    )
    default_notes: Optional[str] = Field(
        None,
        max_length=500,
        description="Default notes to pre-fill"
    )

    # Auto-matching configuration
    auto_match_enabled: bool = Field(
        default=True,
        description="Enable auto-matching for this template"
    )
    min_match_score: int = Field(
        default=70,
        ge=0,
        le=100,
        description="Minimum confidence score (0-100) to auto-suggest"
    )
    require_gps_match: bool = Field(
        default=False,
        description="Require GPS route match (only for templates with GPS data)"
    )

    # Time-based matching
    typical_start_time: Optional[time] = Field(
        None,
        description="Typical start time for this activity"
    )
    time_window_hours: int = Field(
        default=2,
        ge=0,
        le=12,
        description="Time window for matching (±hours)"
    )
    preferred_days: Optional[List[int]] = Field(
        None,
        description="Preferred days of week (1=Monday, 7=Sunday)"
    )

    # Workout goals
    target_zone: Optional[str] = Field(
        None,
        max_length=50,
        description="Target HR zone or effort level"
    )
    goal_notes: Optional[str] = Field(
        None,
        max_length=500,
        description="Workout goal/purpose"
    )

    @validator('activity_type')
    def validate_activity_type(cls, v):
        """Validate activity type against allowed values."""
        if v not in VALID_ACTIVITY_TYPES:
            raise ValueError(
                f"activity_type must be one of {VALID_ACTIVITY_TYPES}, got '{v}'"
            )
        return v

    @validator('preferred_days')
    def validate_preferred_days(cls, v):
        """Ensure preferred_days are valid day numbers (1-7)."""
        if v is not None:
            if not all(1 <= day <= 7 for day in v):
                raise ValueError("preferred_days must contain values between 1-7 (Monday-Sunday)")
            if len(v) != len(set(v)):
                raise ValueError("preferred_days must not contain duplicates")
        return v

    @validator('default_exercises')
    def validate_default_exercises(cls, v, values):
        """Validate exercise structure if provided."""
        activity_type = values.get('activity_type')

        # Only validate if we have exercises and activity type
        if v and activity_type == 'strength_training':
            for exercise in v:
                if not isinstance(exercise, dict):
                    raise ValueError("Each exercise must be a dictionary")

                # Required fields for exercises
                required_fields = ['name']
                for field in required_fields:
                    if field not in exercise:
                        raise ValueError(f"Exercise missing required field: {field}")

        return v


class CreateTemplateRequest(TemplateBase):
    """Request model for creating a new template."""

    created_from_activity_id: Optional[UUID] = Field(
        None,
        description="Activity ID this template was created from (if applicable)"
    )


class UpdateTemplateRequest(BaseModel):
    """Request model for updating a template (all fields optional)."""

    template_name: Optional[str] = Field(None, min_length=1, max_length=100)
    activity_type: Optional[str] = None
    description: Optional[str] = Field(None, max_length=500)
    icon: Optional[str] = Field(None, max_length=10)

    expected_distance_m: Optional[float] = Field(None, gt=0)
    distance_tolerance_percent: Optional[int] = Field(None, ge=0, le=100)
    expected_duration_minutes: Optional[int] = Field(None, gt=0)
    duration_tolerance_percent: Optional[int] = Field(None, ge=0, le=100)

    default_exercises: Optional[List[Dict[str, Any]]] = None
    default_metrics: Optional[Dict[str, Any]] = None
    default_notes: Optional[str] = Field(None, max_length=500)

    auto_match_enabled: Optional[bool] = None
    min_match_score: Optional[int] = Field(None, ge=0, le=100)
    require_gps_match: Optional[bool] = None

    typical_start_time: Optional[time] = None
    time_window_hours: Optional[int] = Field(None, ge=0, le=12)
    preferred_days: Optional[List[int]] = None

    target_zone: Optional[str] = Field(None, max_length=50)
    goal_notes: Optional[str] = Field(None, max_length=500)

    is_active: Optional[bool] = None

    @validator('activity_type')
    def validate_activity_type(cls, v):
        """Validate activity type if provided."""
        if v is not None and v not in VALID_ACTIVITY_TYPES:
            raise ValueError(
                f"activity_type must be one of {VALID_ACTIVITY_TYPES}, got '{v}'"
            )
        return v

    @validator('preferred_days')
    def validate_preferred_days(cls, v):
        """Validate preferred_days if provided."""
        if v is not None:
            if not all(1 <= day <= 7 for day in v):
                raise ValueError("preferred_days must contain values between 1-7 (Monday-Sunday)")
            if len(v) != len(set(v)):
                raise ValueError("preferred_days must not contain duplicates")
        return v


class ActivityTemplate(BaseModel):
    """Full template response with database fields."""

    id: UUID = Field(..., description="Template UUID")
    user_id: UUID = Field(..., description="User UUID who created the template")

    template_name: str
    activity_type: str
    description: Optional[str]
    icon: str

    expected_distance_m: Optional[float]
    distance_tolerance_percent: int
    expected_duration_minutes: Optional[int]
    duration_tolerance_percent: int

    default_exercises: List[Dict[str, Any]]
    default_metrics: Dict[str, Any]
    default_notes: Optional[str]

    auto_match_enabled: bool
    min_match_score: int
    require_gps_match: bool

    typical_start_time: Optional[time]
    time_window_hours: int
    preferred_days: Optional[List[int]]

    gps_route_hash: Optional[str]
    gps_track_id: Optional[UUID]

    target_zone: Optional[str]
    goal_notes: Optional[str]

    use_count: int
    last_used_at: Optional[datetime]

    is_active: bool
    created_from_activity_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config for ORM mode."""
        from_attributes = True


class TemplateStats(BaseModel):
    """Template usage statistics and analytics."""

    template_id: UUID
    total_uses: int = Field(..., description="Total times this template was used")

    # Performance metrics (None if no activities yet)
    avg_duration_minutes: Optional[float] = Field(
        None,
        description="Average activity duration"
    )
    avg_distance_m: Optional[float] = Field(
        None,
        description="Average distance (if applicable)"
    )
    avg_calories: Optional[float] = Field(
        None,
        description="Average calories burned"
    )

    # Trends
    trend_pace_percent: Optional[float] = Field(
        None,
        description="Pace trend (negative = getting faster)"
    )
    trend_consistency_score: Optional[float] = Field(
        None,
        description="Consistency score 0-100 (how often user does this)"
    )

    # Best performance
    best_activity_id: Optional[UUID] = Field(
        None,
        description="Activity ID with best performance"
    )
    best_performance_date: Optional[datetime] = Field(
        None,
        description="Date of best performance"
    )
    best_performance_metric: Optional[str] = Field(
        None,
        description="What made it best (e.g., 'Fastest pace: 5:45/km')"
    )

    # Usage timing
    first_used: Optional[datetime]
    last_used: Optional[datetime]
    days_since_last_use: Optional[int]


class TemplateListResponse(BaseModel):
    """Paginated template list response."""

    templates: List[ActivityTemplate]
    total: int
    limit: int
    offset: int


class CreateTemplateFromActivityRequest(BaseModel):
    """Request to create template from existing activity."""

    template_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name for the new template"
    )
    auto_match_enabled: bool = Field(
        default=True,
        description="Enable auto-matching for this template"
    )
    require_gps_match: bool = Field(
        default=False,
        description="Require GPS route match (if activity has GPS data)"
    )


class SuccessResponse(BaseModel):
    """Generic success response."""

    success: bool = True
    message: str
