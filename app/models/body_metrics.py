"""
Pydantic models for body metrics tracking.

Handles validation for weight and body composition measurements.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, timezone
from uuid import UUID
import structlog

logger = structlog.get_logger()


class BodyMetricBase(BaseModel):
    """Base body metric fields shared across create/update operations."""

    recorded_at: datetime = Field(
        ...,
        description="When the measurement was taken (can be backdated)"
    )
    weight_kg: float = Field(
        ...,
        ge=30.0,
        le=300.0,
        description="Weight in kilograms (30-300 kg)"
    )
    height_cm: Optional[float] = Field(
        None,
        ge=100.0,
        le=300.0,
        description="Height in centimeters (100-300 cm)"
    )
    body_fat_percentage: Optional[float] = Field(
        None,
        ge=3.0,
        le=60.0,
        description="Body fat percentage (3-60%)"
    )
    notes: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional notes about this measurement"
    )

    @validator('recorded_at')
    def validate_recorded_at(cls, v):
        """Ensure recorded_at is not in the future. Handle aware/naive datetimes."""
        # Normalize both to timezone-aware UTC for safe comparison
        if v.tzinfo is None:
            v_aware = v.replace(tzinfo=timezone.utc)
        else:
            v_aware = v.astimezone(timezone.utc)
        now_utc = datetime.now(timezone.utc)
        if v_aware > now_utc:
            raise ValueError("recorded_at cannot be in the future")
        return v

    @validator('weight_kg')
    def validate_weight(cls, v):
        """Round weight to 2 decimal places for consistency."""
        return round(v, 2)

    @validator('body_fat_percentage')
    def validate_body_fat(cls, v):
        """Round body fat percentage to 1 decimal place."""
        if v is not None:
            return round(v, 1)
        return v


class CreateBodyMetricRequest(BodyMetricBase):
    """Request model for creating a new body metric entry."""
    pass


class UpdateBodyMetricRequest(BaseModel):
    """Request model for updating a body metric (all fields optional)."""

    recorded_at: Optional[datetime] = None
    weight_kg: Optional[float] = Field(None, ge=30.0, le=300.0)
    height_cm: Optional[float] = Field(None, ge=100.0, le=300.0)
    body_fat_percentage: Optional[float] = Field(None, ge=3.0, le=60.0)
    notes: Optional[str] = Field(None, max_length=500)

    @validator('recorded_at')
    def validate_recorded_at(cls, v):
        """Ensure recorded_at is not in the future."""
        if v and v > datetime.now():
            raise ValueError("recorded_at cannot be in the future")
        return v

    @validator('weight_kg')
    def validate_weight(cls, v):
        """Round weight to 2 decimal places for consistency."""
        if v is not None:
            return round(v, 2)
        return v

    @validator('body_fat_percentage')
    def validate_body_fat(cls, v):
        """Round body fat percentage to 1 decimal place."""
        if v is not None:
            return round(v, 1)
        return v


class BodyMetric(BaseModel):
    """Full body metric response with database fields."""

    id: UUID = Field(..., description="Body metric UUID")
    user_id: UUID = Field(..., description="User UUID who created this metric")
    recorded_at: datetime
    weight_kg: float
    height_cm: Optional[float]
    body_fat_percentage: Optional[float]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config for ORM mode."""
        from_attributes = True


class BodyMetricListResponse(BaseModel):
    """Paginated body metrics list response."""

    metrics: List[BodyMetric]
    total: int
    limit: int
    offset: int


class WeightTrend(BaseModel):
    """Weight trend analysis over a period."""

    current_weight: float = Field(..., description="Most recent weight (kg)")
    previous_weight: Optional[float] = Field(
        None,
        description="Previous weight for comparison (kg)"
    )
    change_kg: float = Field(..., description="Weight change (positive = gain, negative = loss)")
    change_percentage: float = Field(..., description="Percentage change")
    trend_direction: str = Field(
        ...,
        description="Trend direction: 'up', 'down', or 'stable'"
    )
    days_between: int = Field(..., description="Days between measurements")
    avg_change_per_week: float = Field(
        ...,
        description="Average kg change per week"
    )


class SuccessResponse(BaseModel):
    """Generic success response."""

    success: bool = True
    message: str
