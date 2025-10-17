"""
Pydantic models for activity tracking.

Handles validation for diverse activity types with flexible metrics.

DOCUMENTATION REFERENCES:
- System Architecture: /ACTIVITY_TRACKING_SYSTEM.md
- Bug Prevention Guide: /ACTIVITY_TRACKING_BUG_PREVENTION.md

CRITICAL: These models MUST stay in sync with frontend TypeScript types
Location: ULTIMATE_COACH_FRONTEND/lib/types/activities.ts
Last Synced: 2025-10-16

TYPE SYNC REQUIREMENT:
Any changes to these models MUST be reflected in the frontend types.
Breaking changes require API versioning (see ACTIVITY_TRACKING_SYSTEM.md Section 7.1)

BUG PREVENTION:
- All fields have explicit validation ranges to prevent constraint violations
- METs ranges are category-specific to catch unrealistic values
- Validators log warnings instead of errors for edge cases (user may have legitimate reasons)
- Duration can be calculated OR manual (service layer handles conflicts)
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
import structlog

logger = structlog.get_logger()

# Category-specific METs ranges for realistic intensity validation
# BUG PREVENTION: These ranges catch data entry errors (e.g., yoga = 15 METs)
# Note: Validators LOG warnings but don't raise errors (users may have edge cases)
# Reference: ACTIVITY_TRACKING_BUG_PREVENTION.md Section 3.3
METS_RANGES = {
    'cardio_steady_state': (3.0, 15.0),    # Walking (3.0) to running (15.0)
    'cardio_interval': (5.0, 18.0),        # HIIT (10.0), sprints (18.0)
    'strength_training': (3.0, 8.0),       # Weight lifting (5.0), circuit (8.0)
    'sports': (4.0, 12.0),                 # Tennis (7.0), basketball (8.0)
    'flexibility': (1.5, 4.0),             # Stretching (2.5), power yoga (4.0)
    'other': (1.0, 20.0)                   # Full range for unknown activities
}


class ActivityBase(BaseModel):
    """
    Base activity fields shared across create/update operations.

    BUG PREVENTION:
    - All fields have explicit validation to prevent database constraint violations
    - Optional fields allow service layer to auto-calculate missing values
    - Validators ensure data consistency (e.g., end_time > start_time)

    CALCULATION CHAIN:
    1. duration_minutes: Auto-calculated from (end_time - start_time) if not provided
    2. intensity_mets: Auto-looked up from activity_name if not provided
    3. calories_burned: Auto-calculated using METs × weight × duration if not provided

    See: ACTIVITY_TRACKING_SYSTEM.md Section 8 (Calculation Formulas)
    """

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
    start_time: datetime = Field(
        ...,
        description="Activity start time (ISO 8601 UTC). CRITICAL: Must be UTC timezone."
    )
    end_time: Optional[datetime] = Field(
        None,
        description="Activity end time (ISO 8601 UTC). CRITICAL: Must be UTC, must be > start_time"
    )
    duration_minutes: Optional[int] = Field(
        None,
        ge=1,
        le=1440,  # Max 24 hours (BUG PREVENTION: Prevents absurd durations)
        description="Duration in minutes. AUTO-CALCULATED if end_time provided and this is None"
    )
    calories_burned: Optional[int] = Field(
        None,
        ge=0,
        le=10000,  # BUG PREVENTION: Sanity check (10k+ kcal unrealistic for single activity)
        description="Calories burned. AUTO-CALCULATED using METs formula if not provided"
    )
    intensity_mets: Optional[float] = Field(
        None,
        ge=1.0,
        le=20.0,  # BUG PREVENTION: 1.0=rest, 20.0=max human effort
        description="Metabolic Equivalent of Task. AUTO-LOOKED UP from activity_name if not provided"
    )
    metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Activity-specific JSONB metrics (distance, HR, exercises, etc.). See schema docs."
    )
    notes: Optional[str] = Field(
        None,
        max_length=500,
        description="User notes about the activity"
    )

    @validator('category')
    def validate_category(cls, v):
        """
        Validate activity category against allowed values.

        CRITICAL: This list MUST match:
        - Database CHECK constraint in activities table
        - Frontend TypeScript ActivityCategory type
        - METs ranges dictionary above

        BUG PREVENTION: Database has final constraint, but catching here gives better error messages.
        """
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
        """
        Ensure end_time is after start_time.

        BUG PREVENTION (Bug 2.2 in prevention guide):
        - Frontend must convert local time → UTC before sending
        - This validator works in UTC (no timezone conversion here)
        - Catches time travel bugs (end before start)

        EDGE CASE: DST transitions
        - Frontend handles DST (e.g., 2 AM doesn't exist on spring forward)
        - Backend only validates UTC timestamps
        """
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

        BUG PREVENTION (Bug 3.3 in prevention guide):
        - Catches data entry errors (e.g., "yoga" with METs=15)
        - LOGS WARNING instead of raising error (user may have legitimate reasons)
        - Service layer performs METs lookup if this is None

        IMPORTANT: This is SOFT validation
        - We warn but don't block unusual values
        - Database has hard constraints (1.0-20.0)
        - Service layer provides auto-lookup if None

        Example edge cases that would trigger warning but are valid:
        - Very light yoga: METs=1.5 (below cardio range)
        - Extreme HIIT: METs=18.0 (above cardio_steady_state range)
        """
        # If METs not provided, it will be calculated automatically
        if v is None:
            return v

        category = values.get('category')
        if not category:
            return v  # Category validation will catch this

        min_mets, max_mets = METS_RANGES.get(category, (1.0, 20.0))

        if v < min_mets or v > max_mets:
            logger.warning(
                "unusual_mets_value",
                category=category,
                mets=v,
                min_mets=min_mets,
                max_mets=max_mets,
                msg="METs outside typical range for category - verify with user"
            )

        return v

    @validator('duration_minutes')
    def validate_duration(cls, v, values):
        """
        Warn if both duration and end_time are provided (potential conflict).

        Duration can be calculated from start_time + end_time OR manually entered.
        If both exist, service layer will recalculate from times.

        BUG PREVENTION (Bug 3.2 in prevention guide):
        - Service layer ALWAYS recalculates if timestamps change
        - This warning helps developers catch potential conflicts
        - Timestamps are source of truth (more accurate than manual entry)

        PRIORITY: end_time > duration_minutes
        If both provided, service layer uses: (end_time - start_time)

        USE CASES:
        1. User provides start_time + end_time → duration auto-calculated ✅
        2. User provides start_time + duration_minutes → end_time computed ✅
        3. User provides all three → timestamps win, duration recalculated ⚠️ (logged here)
        """
        if v and values.get('end_time'):
            logger.info(
                "duration_recalculation",
                duration_provided=v,
                start_time=values.get('start_time'),
                end_time=values.get('end_time'),
                msg="Both duration_minutes and end_time provided - duration will be recalculated from timestamps"
            )
        return v


class CreateActivityRequest(ActivityBase):
    """
    Request model for creating a new activity.

    Inherits all validation from ActivityBase.

    REQUIRED FIELDS:
    - category: str (one of 6 valid categories)
    - activity_name: str (1-100 chars)
    - start_time: datetime (ISO 8601 UTC)

    OPTIONAL FIELDS (auto-calculated if omitted):
    - end_time: datetime
    - duration_minutes: int (calculated from timestamps)
    - calories_burned: int (calculated using METs formula)
    - intensity_mets: float (looked up from activity_name)
    - metrics: dict (activity-specific data)
    - notes: str

    SERVICE LAYER PROCESSING:
    1. Validates all fields (this model)
    2. Calculates duration if end_time provided and duration_minutes is None
    3. Looks up METs if intensity_mets is None
    4. Calculates calories if calories_burned is None
    5. Validates JSONB metrics schema
    6. Inserts into database
    7. Triggers async matching to planned sessions (non-blocking)

    See: ACTIVITY_TRACKING_SYSTEM.md Section 5.1 (Create Activity Flow)
    """
    pass


class UpdateActivityRequest(BaseModel):
    """
    Request model for updating an activity (all fields optional).

    PARTIAL UPDATE PATTERN:
    - All fields optional (PATCH semantics)
    - Only provided fields are updated
    - Uses Pydantic exclude_unset=True

    RECALCULATION LOGIC:
    - If start_time or end_time updated WITHOUT duration_minutes → recalculate duration
    - If intensity_mets or duration_minutes updated WITHOUT calories_burned → recalculate calories

    BUG PREVENTION (Bug 5.1 in prevention guide):
    - Service layer verifies ownership before update (user_id match)
    - Returns 403 if user tries to update another user's activity
    - Returns 404 if activity doesn't exist or deleted

    SECURITY:
    - NEVER allows updating user_id (prevents activity hijacking)
    - NEVER allows updating id (immutable primary key)
    - NEVER allows updating created_at (audit trail)

    See: ACTIVITY_TRACKING_SYSTEM.md Section 3.5 (Update Activity API)
    """

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
    """
    Full activity response with database fields.

    This model represents the complete activity entity as stored in database.
    Used for API responses (GET /activities, POST /activities, etc.)

    CRITICAL: This MUST match:
    - Database schema (activities table)
    - Frontend TypeScript Activity interface

    DATABASE FIELDS NOT EXPOSED:
    - deleted_at: Soft delete timestamp (filtered in queries)
    - template_id: Foreign key to activity_templates (future feature)
    - wearable_sync_id: External wearable ID (wearable integration)
    - wearable_provider: Provider name (garmin, strava, etc.)

    TIMEZONE HANDLING:
    - start_time, end_time: Always UTC in database
    - Frontend converts to user's local timezone for display
    - See: ACTIVITY_TRACKING_SYSTEM.md Section 9 (Timezone Handling)

    NULL HANDLING:
    - end_time: NULL if activity ongoing or duration manually entered
    - notes: NULL if user didn't add notes
    - metrics: Empty dict {} if no additional metrics

    See: ACTIVITY_TRACKING_SYSTEM.md Section 4.1 (TypeScript Types)
    """

    id: UUID = Field(..., description="Activity UUID (immutable)")
    user_id: UUID = Field(..., description="User UUID who owns this activity")
    category: str = Field(..., description="Activity category (one of 6 types)")
    activity_name: str = Field(..., description="Custom activity name")
    start_time: datetime = Field(..., description="Start time (ISO 8601 UTC)")
    end_time: Optional[datetime] = Field(None, description="End time (ISO 8601 UTC), NULL if ongoing")
    duration_minutes: int = Field(..., description="Duration in minutes (1-1440)")
    calories_burned: int = Field(..., description="Calories burned (0-10000)")
    intensity_mets: float = Field(..., description="METs intensity (1.0-20.0)")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Activity-specific JSONB metrics")
    notes: Optional[str] = Field(None, description="User notes (max 500 chars)")
    created_at: datetime = Field(..., description="Record creation time (UTC)")
    updated_at: datetime = Field(..., description="Last update time (UTC)")

    class Config:
        """Pydantic config for ORM mode."""
        from_attributes = True  # Allow ORM objects (SQLAlchemy models)


class DailySummary(BaseModel):
    """
    Daily activity summary with aggregated statistics.

    Returned by GET /api/v1/activities/summary endpoint.
    Aggregates all activities for a given date (target_date query param).

    CALCULATION FORMULAS:
    - total_calories_burned = SUM(calories_burned) WHERE DATE(start_time AT TIME ZONE user_tz) = target_date
    - total_duration_minutes = SUM(duration_minutes)
    - average_intensity = AVG(intensity_mets)
    - activity_count = COUNT(*)
    - daily_goal_calories = profiles.daily_calorie_burn_goal (default 500)
    - goal_percentage = (total_calories / daily_goal) × 100

    BUG PREVENTION (Bug 2.3 in prevention guide):
    - CRITICAL: Use user's timezone for date comparison, NOT UTC date
    - SQL: DATE(start_time AT TIME ZONE user_timezone) = target_date
    - Prevents activities showing up in wrong day

    EDGE CASES:
    - No activities for date: All totals = 0, goal_percentage = 0
    - Exceeds goal: goal_percentage > 100 (e.g., 150% if burned 750/500)
    - User has no goal set: daily_goal_calories defaults to 500

    FRONTEND USAGE:
    - Display progress bar (goal_percentage)
    - Show daily stats (calories, duration, count)
    - Color-code based on goal achievement

    See: ACTIVITY_TRACKING_SYSTEM.md Section 8.4 (Goal Percentage Calculation)
    """

    total_calories_burned: int = Field(
        ...,
        description="Total calories burned today (sum of all activities)"
    )
    total_duration_minutes: int = Field(
        ...,
        description="Total activity duration in minutes (sum)"
    )
    average_intensity: float = Field(
        ...,
        description="Average METs across all activities (mean intensity)"
    )
    activity_count: int = Field(
        ...,
        description="Number of activities logged today"
    )
    daily_goal_calories: int = Field(
        ...,
        description="User's daily calorie burn goal from profile (default 500)"
    )
    goal_percentage: float = Field(
        ...,
        description="Progress toward daily goal as percentage (can exceed 100)"
    )


class ActivityListResponse(BaseModel):
    """
    Paginated activity list response.

    Returned by GET /api/v1/activities endpoint.

    PAGINATION:
    - limit: Number of results per page (1-100, default 20)
    - offset: Number of results to skip (for page navigation)
    - total: Total number of matching activities (for calculating page count)

    BUG PREVENTION (Bug 7.3 in prevention guide):
    - Max limit enforced at 100 to prevent memory issues
    - Default limit is 20 for performance
    - Total count allows frontend to show "Page 1 of 10"

    FRONTEND USAGE:
    - Calculate pages: Math.ceil(total / limit)
    - Next page: offset + limit
    - Previous page: offset - limit
    - Has next: offset + limit < total
    - Has previous: offset > 0

    QUERY FILTERING:
    - start_date, end_date: Filter by date range
    - Automatically filters WHERE deleted_at IS NULL
    - Ordered by start_time DESC (newest first)

    See: ACTIVITY_TRACKING_SYSTEM.md Section 3.1 (List Activities API)
    """

    activities: List[Activity] = Field(..., description="List of activities for current page")
    total: int = Field(..., description="Total count of matching activities (all pages)")
    limit: int = Field(..., description="Page size (activities per page)")
    offset: int = Field(..., description="Number of activities skipped (for pagination)")


class SuccessResponse(BaseModel):
    """
    Generic success response for operations with no return data.

    Used for:
    - DELETE /api/v1/activities/{id} (soft delete)
    - Other operations that confirm success without returning entity

    STANDARD FORMAT:
    - success: Always true (failed requests return error responses)
    - message: Human-readable success message

    BUG PREVENTION (Bug 7.2 in prevention guide):
    - Consistent response format across all endpoints
    - Frontend can reliably check response.success
    - message provides user-facing feedback

    Example usage:
    ```
    return SuccessResponse(
        success=True,
        message="Activity deleted successfully"
    )
    ```
    """

    success: bool = True
    message: str
