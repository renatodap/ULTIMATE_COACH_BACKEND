"""
Pydantic models for daily check-ins and streaks

Supports accountability system:
- Daily check-ins (energy, hunger, stress, sleep, motivation)
- Streak tracking (current, longest, total)
- Notification preferences
"""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# DAILY CHECK-IN MODELS
# ============================================================================

class CheckInBase(BaseModel):
    """Base fields for check-in (user input)"""

    check_in_date: date = Field(..., description="Check-in date (user's local date)")
    energy_level: int = Field(..., ge=1, le=10, description="Energy level (1-10)")
    hunger_level: int = Field(..., ge=1, le=10, description="Hunger level (1-10)")
    stress_level: int = Field(..., ge=1, le=10, description="Stress level (1-10)")
    sleep_quality: int = Field(..., ge=1, le=10, description="Sleep quality (1-10)")
    motivation: int = Field(..., ge=1, le=10, description="Motivation level (1-10)")
    notes: Optional[str] = Field(None, max_length=1000, description="Optional notes")


class CreateCheckInRequest(CheckInBase):
    """Request body for creating a check-in"""
    pass


class UpdateCheckInRequest(BaseModel):
    """Request body for updating a check-in (all fields optional)"""

    energy_level: Optional[int] = Field(None, ge=1, le=10)
    hunger_level: Optional[int] = Field(None, ge=1, le=10)
    stress_level: Optional[int] = Field(None, ge=1, le=10)
    sleep_quality: Optional[int] = Field(None, ge=1, le=10)
    motivation: Optional[int] = Field(None, ge=1, le=10)
    notes: Optional[str] = Field(None, max_length=1000)


class CheckInResponse(CheckInBase):
    """Full check-in response (includes AI-calculated fields)"""

    id: str
    user_id: str
    adherence_score: Optional[int] = Field(None, description="AI-calculated adherence (0-100%)")
    adaptive_deficit: Optional[int] = Field(None, description="AI-determined calorie adjustment")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# STREAK MODELS
# ============================================================================

class UserStreakResponse(BaseModel):
    """User streak data"""

    user_id: str
    current_streak: int = Field(..., description="Current consecutive check-in days")
    longest_streak: int = Field(..., description="Longest streak ever achieved")
    last_check_in_date: Optional[date] = Field(None, description="Last check-in date")
    total_check_ins: int = Field(..., description="Lifetime total check-ins")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# NOTIFICATION PREFERENCES MODELS
# ============================================================================

class NotificationPreferencesBase(BaseModel):
    """Base notification preferences"""

    daily_check_in_reminders: bool = True
    meal_logging_reminders: bool = True
    workout_reminders: bool = True
    coach_notifications: bool = True
    streak_notifications: bool = True
    weekly_summary: bool = True


class UpdateNotificationPreferencesRequest(BaseModel):
    """Request to update notification preferences (all optional)"""

    daily_check_in_reminders: Optional[bool] = None
    meal_logging_reminders: Optional[bool] = None
    workout_reminders: Optional[bool] = None
    coach_notifications: Optional[bool] = None
    streak_notifications: Optional[bool] = None
    weekly_summary: Optional[bool] = None


class NotificationPreferencesResponse(NotificationPreferencesBase):
    """Full notification preferences response"""

    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
