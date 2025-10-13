"""
Pydantic models for dashboard API responses.

Aggregates data from multiple sources for unified dashboard view.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict
from decimal import Decimal


class TodayNutritionSummary(BaseModel):
    """Today's nutrition summary."""

    calories_consumed: Decimal = Field(..., description="Calories consumed today")
    calories_goal: Optional[int] = Field(None, description="Daily calorie goal")
    calories_remaining: Optional[int] = Field(None, description="Calories remaining (goal - consumed)")

    protein_consumed: Decimal = Field(..., description="Protein consumed (g)")
    protein_goal: Optional[Decimal] = Field(None, description="Protein goal (g)")

    carbs_consumed: Decimal = Field(..., description="Carbs consumed (g)")
    carbs_goal: Optional[Decimal] = Field(None, description="Carbs goal (g)")

    fat_consumed: Decimal = Field(..., description="Fat consumed (g)")
    fat_goal: Optional[Decimal] = Field(None, description="Fat goal (g)")

    meals_count: int = Field(..., description="Number of meals logged today")
    meals_by_type: Dict[str, int] = Field(
        default_factory=dict,
        description="Meal count by type (breakfast, lunch, etc.)"
    )


class TodayActivitySummary(BaseModel):
    """Today's activity summary."""

    total_calories_burned: int = Field(..., description="Total calories burned today")
    total_duration_minutes: int = Field(..., description="Total activity duration (minutes)")
    average_intensity: float = Field(..., description="Average METs")
    activity_count: int = Field(..., description="Number of activities logged today")
    daily_goal_calories: int = Field(..., description="Daily calorie burn goal")
    goal_percentage: float = Field(..., description="Progress toward goal (0-100+)")


class WeightProgressSummary(BaseModel):
    """Weight progress summary."""

    current_weight: Optional[float] = Field(None, description="Current weight (kg)")
    goal_weight: Optional[float] = Field(None, description="Goal weight from profile (kg)")
    latest_recorded_at: Optional[str] = Field(None, description="When latest weight was recorded")

    # 7-day trend
    previous_weight: Optional[float] = Field(None, description="Weight 7 days ago (kg)")
    change_kg: float = Field(0.0, description="Weight change over 7 days")
    change_percentage: float = Field(0.0, description="Percentage change")
    trend_direction: str = Field("stable", description="up, down, or stable")
    avg_change_per_week: float = Field(0.0, description="Average kg change per week")

    # Progress to goal
    progress_percentage: Optional[float] = Field(
        None,
        description="Progress toward goal weight (0-100)"
    )
    remaining_kg: Optional[float] = Field(None, description="Kg remaining to goal")


class WeeklyStats(BaseModel):
    """Weekly activity and consistency stats."""

    days_active: int = Field(..., description="Days with logged activities this week")
    days_with_meals: int = Field(..., description="Days with logged meals this week")
    total_workouts: int = Field(..., description="Total workouts this week")
    total_meals: int = Field(..., description="Total meals this week")
    avg_calories_consumed: Optional[int] = Field(None, description="Average daily calories this week")
    avg_calories_burned: Optional[int] = Field(None, description="Average daily calories burned this week")


class DashboardSummary(BaseModel):
    """Complete dashboard summary."""

    # User info
    user_id: str = Field(..., description="User UUID")
    display_name: Optional[str] = Field(None, description="User's display name or email")

    # Today's data
    nutrition: TodayNutritionSummary = Field(..., description="Today's nutrition summary")
    activity: TodayActivitySummary = Field(..., description="Today's activity summary")

    # Net calories (consumed - burned)
    net_calories: int = Field(..., description="Net calories today (consumed - burned)")

    # Weight progress
    weight: WeightProgressSummary = Field(..., description="Weight progress summary")

    # Weekly stats
    weekly: WeeklyStats = Field(..., description="Weekly consistency stats")

    # Metadata
    date: str = Field(..., description="Date for this summary (YYYY-MM-DD)")
