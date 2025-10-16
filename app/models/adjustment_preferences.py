"""
Pydantic models for daily adjustment approval workflow.

Models for:
- Adjustment preferences (per-trigger settings)
- Approval/rejection requests
- Notifications
- User feedback
"""

from datetime import datetime
from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


# ============================================================================
# Adjustment Preferences
# ============================================================================

TriggerAction = Literal["auto_apply", "ask_me", "disable"]


class AdjustmentPreferences(BaseModel):
    """User preferences for daily adjustment approval workflow"""

    user_id: str = Field(..., description="User UUID")

    # Global toggle
    daily_adjustments_enabled: bool = Field(
        True, description="Master toggle for daily adjustments"
    )

    # Per-trigger preferences
    poor_sleep_training: TriggerAction = Field("auto_apply")
    poor_sleep_nutrition: TriggerAction = Field("auto_apply")

    high_stress_training: TriggerAction = Field("auto_apply")
    high_stress_nutrition: TriggerAction = Field("ask_me")

    high_soreness_training: TriggerAction = Field("auto_apply")
    high_soreness_nutrition: TriggerAction = Field("disable")

    injury_training: TriggerAction = Field("ask_me")
    injury_nutrition: TriggerAction = Field("disable")

    missed_workout_training: TriggerAction = Field("disable")
    missed_workout_nutrition: TriggerAction = Field("auto_apply")

    low_adherence_training: TriggerAction = Field("ask_me")
    low_adherence_nutrition: TriggerAction = Field("ask_me")

    high_adherence_training: TriggerAction = Field("auto_apply")
    high_adherence_nutrition: TriggerAction = Field("auto_apply")

    # Timing settings
    auto_apply_grace_period_minutes: int = Field(
        120, description="Minutes before auto-applying high-confidence adjustments", ge=0, le=1440
    )
    undo_window_hours: int = Field(
        24, description="Hours user can undo an adjustment", ge=1, le=72
    )

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UpdateAdjustmentPreferences(BaseModel):
    """Request to update adjustment preferences (all fields optional)"""

    daily_adjustments_enabled: Optional[bool] = None

    poor_sleep_training: Optional[TriggerAction] = None
    poor_sleep_nutrition: Optional[TriggerAction] = None

    high_stress_training: Optional[TriggerAction] = None
    high_stress_nutrition: Optional[TriggerAction] = None

    high_soreness_training: Optional[TriggerAction] = None
    high_soreness_nutrition: Optional[TriggerAction] = None

    injury_training: Optional[TriggerAction] = None
    injury_nutrition: Optional[TriggerAction] = None

    missed_workout_training: Optional[TriggerAction] = None
    missed_workout_nutrition: Optional[TriggerAction] = None

    low_adherence_training: Optional[TriggerAction] = None
    low_adherence_nutrition: Optional[TriggerAction] = None

    high_adherence_training: Optional[TriggerAction] = None
    high_adherence_nutrition: Optional[TriggerAction] = None

    auto_apply_grace_period_minutes: Optional[int] = Field(None, ge=0, le=1440)
    undo_window_hours: Optional[int] = Field(None, ge=1, le=72)


# ============================================================================
# Approval Requests
# ============================================================================


class ApproveAdjustmentRequest(BaseModel):
    """Request to approve a pending adjustment"""

    user_id: str = Field(..., description="User UUID")
    override_id: str = Field(..., description="Day override UUID")
    notes: Optional[str] = Field(None, description="Optional user notes")


class RejectAdjustmentRequest(BaseModel):
    """Request to reject a pending adjustment"""

    user_id: str = Field(..., description="User UUID")
    override_id: str = Field(..., description="Day override UUID")
    reason: Optional[str] = Field(None, description="Why user rejected")


class UndoAdjustmentRequest(BaseModel):
    """Request to undo an applied adjustment"""

    user_id: str = Field(..., description="User UUID")
    override_id: str = Field(..., description="Day override UUID")
    reason: Optional[str] = Field(None, description="Why user undid adjustment")


# ============================================================================
# Notifications
# ============================================================================

NotificationType = Literal[
    "adjustment_pending",
    "adjustment_auto_applied",
    "reassessment_due",
    "reassessment_complete",
    "general",
]

NotificationPriority = Literal["low", "normal", "high", "urgent"]

NotificationAction = Literal["approved", "rejected", "undone", "viewed", "dismissed"]


class Notification(BaseModel):
    """User notification model"""

    id: str = Field(..., description="Notification UUID")
    user_id: str = Field(..., description="User UUID")

    notification_type: NotificationType
    title: str
    message: str

    # Reference to related entity
    ref_type: Optional[Literal["day_override", "program", "plan_change_event"]] = None
    ref_id: Optional[str] = None

    # State
    read_at: Optional[datetime] = None
    dismissed_at: Optional[datetime] = None

    # Action tracking
    action_taken: Optional[NotificationAction] = None
    action_taken_at: Optional[datetime] = None

    # Metadata
    priority: NotificationPriority = "normal"
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    created_at: datetime


class CreateNotificationRequest(BaseModel):
    """Request to create notification"""

    user_id: str
    notification_type: NotificationType
    title: str
    message: str
    ref_type: Optional[Literal["day_override", "program", "plan_change_event"]] = None
    ref_id: Optional[str] = None
    priority: NotificationPriority = "normal"
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# User Feedback
# ============================================================================


class AdjustmentFeedback(BaseModel):
    """User feedback on adjustment for ML learning"""

    id: str
    user_id: str
    day_override_id: str

    action: Literal["approved", "rejected", "undone"]

    user_context: Dict[str, Any] = Field(
        default_factory=dict, description="Sleep, stress, soreness at time of feedback"
    )
    adjustment_details: Dict[str, Any] = Field(
        default_factory=dict, description="What was suggested"
    )

    time_to_decision_seconds: Optional[int] = Field(
        None, description="How long before user responded"
    )

    created_at: datetime


# ============================================================================
# Response Models
# ============================================================================


class ApprovalActionResponse(BaseModel):
    """Response after approve/reject/undo action"""

    success: bool
    message: str
    day_override: Optional[Dict[str, Any]] = None
    notification_id: Optional[str] = None
    feedback_id: Optional[str] = None


class PendingAdjustmentsResponse(BaseModel):
    """Response with list of pending adjustments"""

    pending_adjustments: list[Dict[str, Any]]
    count: int
