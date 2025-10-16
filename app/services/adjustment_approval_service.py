"""
Adjustment Approval Service

Handles the approval workflow for daily adjustments:
1. User receives notification when adjustment is recommended
2. User can approve, reject, or ignore
3. High-confidence adjustments auto-apply after grace period (2 hours default)
4. User can undo adjustments within undo window (24 hours default)
5. Track user feedback to learn preferences
"""

import structlog
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from uuid import uuid4

from app.services.supabase_service import SupabaseService
from app.models.adjustment_preferences import (
    AdjustmentPreferences,
    TriggerAction,
)

logger = structlog.get_logger()


class AdjustmentApprovalService:
    """
    Service for managing adjustment approval workflow.

    Key responsibilities:
    - Check user preferences for trigger types
    - Create notifications for pending adjustments
    - Handle approve/reject/undo actions
    - Track user feedback for ML learning
    - Auto-apply high-confidence adjustments after grace period
    """

    def __init__(self):
        self.db = SupabaseService()

    async def get_user_preferences(
        self, user_id: str
    ) -> AdjustmentPreferences:
        """
        Get user's adjustment preferences. Creates default if doesn't exist.

        Args:
            user_id: User UUID

        Returns:
            AdjustmentPreferences
        """
        try:
            result = (
                self.db.client.table("adjustment_preferences")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )

            if result.data:
                return AdjustmentPreferences(**result.data[0])
            else:
                # Create default preferences
                default_prefs = {
                    "user_id": user_id,
                    "daily_adjustments_enabled": True,
                    "auto_apply_grace_period_minutes": 120,
                    "undo_window_hours": 24,
                }

                created = (
                    self.db.client.table("adjustment_preferences")
                    .insert(default_prefs)
                    .execute()
                )

                logger.info("created_default_preferences", user_id=user_id)
                return AdjustmentPreferences(**created.data[0])

        except Exception as e:
            logger.error("get_user_preferences_failed", user_id=user_id, error=str(e))
            raise

    async def update_user_preferences(
        self, user_id: str, updates: Dict[str, Any]
    ) -> AdjustmentPreferences:
        """
        Update user's adjustment preferences.

        Args:
            user_id: User UUID
            updates: Dictionary of fields to update

        Returns:
            Updated AdjustmentPreferences
        """
        try:
            # Ensure preferences exist
            await self.get_user_preferences(user_id)

            # Update
            result = (
                self.db.client.table("adjustment_preferences")
                .update(updates)
                .eq("user_id", user_id)
                .execute()
            )

            logger.info(
                "updated_user_preferences",
                user_id=user_id,
                fields_updated=list(updates.keys()),
            )

            return AdjustmentPreferences(**result.data[0])

        except Exception as e:
            logger.error("update_user_preferences_failed", user_id=user_id, error=str(e))
            raise

    async def should_request_approval(
        self,
        user_id: str,
        trigger_type: str,  # e.g., "poor_sleep", "high_stress"
        adjustment_type: str,  # "nutrition" or "training"
    ) -> TriggerAction:
        """
        Check user's preferences to determine action for this trigger.

        Args:
            user_id: User UUID
            trigger_type: Trigger that caused adjustment (poor_sleep, high_stress, etc)
            adjustment_type: Type of adjustment (nutrition or training)

        Returns:
            "auto_apply" | "ask_me" | "disable"
        """
        try:
            prefs = await self.get_user_preferences(user_id)

            # Check global toggle
            if not prefs.daily_adjustments_enabled:
                return "disable"

            # Get specific preference
            pref_key = f"{trigger_type}_{adjustment_type}"

            if hasattr(prefs, pref_key):
                action = getattr(prefs, pref_key)
                logger.info(
                    "preference_check",
                    user_id=user_id,
                    trigger=trigger_type,
                    adjustment=adjustment_type,
                    action=action,
                )
                return action
            else:
                # Default to ask_me for unknown triggers
                logger.warning(
                    "unknown_preference_key",
                    user_id=user_id,
                    key=pref_key,
                )
                return "ask_me"

        except Exception as e:
            logger.error("should_request_approval_failed", user_id=user_id, error=str(e))
            # Fail safe: ask user
            return "ask_me"

    async def create_adjustment_notification(
        self,
        user_id: str,
        day_override_id: str,
        adjustment_summary: Dict[str, Any],
    ) -> str:
        """
        Create notification for pending adjustment.

        Args:
            user_id: User UUID
            day_override_id: Override UUID
            adjustment_summary: Details about the adjustment

        Returns:
            Notification ID
        """
        try:
            # Build notification message
            title = "Daily Adjustment Suggested"

            message_parts = []

            # Nutrition adjustment
            if adjustment_summary.get("nutrition_override"):
                calorie_adj = adjustment_summary["nutrition_override"].get("calorie_adjustment", 0)
                if calorie_adj != 0:
                    message_parts.append(f"Calories: {calorie_adj:+d} kcal")

            # Training adjustment
            if adjustment_summary.get("training_override"):
                volume_mult = adjustment_summary["training_override"].get("volume_multiplier", 1.0)
                if volume_mult != 1.0:
                    percent_change = int((volume_mult - 1.0) * 100)
                    message_parts.append(f"Training volume: {percent_change:+d}%")

            reason = adjustment_summary.get("reason_details", "Adjustment recommended")

            message = f"{reason}\n\n" + "\n".join(message_parts)

            # Calculate expiration (grace period)
            prefs = await self.get_user_preferences(user_id)
            expires_at = datetime.utcnow() + timedelta(
                minutes=prefs.auto_apply_grace_period_minutes
            )

            notification_data = {
                "user_id": user_id,
                "notification_type": "adjustment_pending",
                "title": title,
                "message": message,
                "ref_type": "day_override",
                "ref_id": day_override_id,
                "priority": "normal",
                "expires_at": expires_at.isoformat(),
                "metadata": {
                    "adjustment_summary": adjustment_summary,
                    "confidence": adjustment_summary.get("confidence", 0.5),
                },
            }

            result = (
                self.db.client.table("notifications")
                .insert(notification_data)
                .execute()
            )

            notification_id = result.data[0]["id"]

            logger.info(
                "adjustment_notification_created",
                user_id=user_id,
                day_override_id=day_override_id,
                notification_id=notification_id,
                expires_at=expires_at.isoformat(),
            )

            return notification_id

        except Exception as e:
            logger.error(
                "create_adjustment_notification_failed",
                user_id=user_id,
                error=str(e),
            )
            raise

    async def approve_adjustment(
        self, user_id: str, day_override_id: str, notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Approve a pending adjustment.

        Flow:
        1. Update day_override status to 'approved'
        2. Update notification (mark read, set action_taken)
        3. Create feedback record for ML
        4. Return updated override

        Args:
            user_id: User UUID
            day_override_id: Override UUID
            notes: Optional user notes

        Returns:
            Updated day_override
        """
        try:
            # Get override
            override_result = (
                self.db.client.table("day_overrides")
                .select("*")
                .eq("id", day_override_id)
                .eq("user_id", user_id)
                .execute()
            )

            if not override_result.data:
                raise ValueError(f"Day override {day_override_id} not found")

            override = override_result.data[0]

            # Check if already processed
            if override["status"] != "pending":
                raise ValueError(
                    f"Cannot approve: adjustment already {override['status']}"
                )

            # Update override
            now = datetime.utcnow()
            updated_override = (
                self.db.client.table("day_overrides")
                .update(
                    {
                        "status": "approved",
                        "approved_at": now.isoformat(),
                        "override_reason": notes,
                    }
                )
                .eq("id", day_override_id)
                .execute()
            )

            # Update notification
            notification_result = (
                self.db.client.table("notifications")
                .update(
                    {
                        "read_at": now.isoformat(),
                        "action_taken": "approved",
                        "action_taken_at": now.isoformat(),
                    }
                )
                .eq("ref_id", day_override_id)
                .eq("notification_type", "adjustment_pending")
                .execute()
            )

            # Create feedback record
            time_to_decision = (
                int((now - datetime.fromisoformat(override["created_at"])).total_seconds())
                if override.get("created_at")
                else None
            )

            feedback_data = {
                "user_id": user_id,
                "day_override_id": day_override_id,
                "action": "approved",
                "user_context": {},  # Could be populated from user_context_log
                "adjustment_details": {
                    "reason_code": override.get("reason_code"),
                    "confidence": override.get("confidence"),
                },
                "time_to_decision_seconds": time_to_decision,
            }

            feedback = (
                self.db.client.table("adjustment_feedback")
                .insert(feedback_data)
                .execute()
            )

            logger.info(
                "adjustment_approved",
                user_id=user_id,
                day_override_id=day_override_id,
                time_to_decision_seconds=time_to_decision,
            )

            return updated_override.data[0]

        except Exception as e:
            logger.error(
                "approve_adjustment_failed",
                user_id=user_id,
                day_override_id=day_override_id,
                error=str(e),
            )
            raise

    async def reject_adjustment(
        self, user_id: str, day_override_id: str, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reject a pending adjustment.

        Flow:
        1. Update day_override status to 'rejected'
        2. Update notification
        3. Create feedback record for ML
        4. Learn from rejection (future: update preference weights)

        Args:
            user_id: User UUID
            day_override_id: Override UUID
            reason: Why user rejected

        Returns:
            Updated day_override
        """
        try:
            # Get override
            override_result = (
                self.db.client.table("day_overrides")
                .select("*")
                .eq("id", day_override_id)
                .eq("user_id", user_id)
                .execute()
            )

            if not override_result.data:
                raise ValueError(f"Day override {day_override_id} not found")

            override = override_result.data[0]

            # Check if already processed
            if override["status"] != "pending":
                raise ValueError(
                    f"Cannot reject: adjustment already {override['status']}"
                )

            # Update override
            now = datetime.utcnow()
            updated_override = (
                self.db.client.table("day_overrides")
                .update(
                    {
                        "status": "rejected",
                        "rejected_at": now.isoformat(),
                        "override_reason": reason,
                    }
                )
                .eq("id", day_override_id)
                .execute()
            )

            # Update notification
            self.db.client.table("notifications").update(
                {
                    "read_at": now.isoformat(),
                    "action_taken": "rejected",
                    "action_taken_at": now.isoformat(),
                }
            ).eq("ref_id", day_override_id).eq(
                "notification_type", "adjustment_pending"
            ).execute()

            # Create feedback record
            time_to_decision = (
                int((now - datetime.fromisoformat(override["created_at"])).total_seconds())
                if override.get("created_at")
                else None
            )

            feedback_data = {
                "user_id": user_id,
                "day_override_id": day_override_id,
                "action": "rejected",
                "adjustment_details": {
                    "reason_code": override.get("reason_code"),
                    "confidence": override.get("confidence"),
                    "user_reason": reason,
                },
                "time_to_decision_seconds": time_to_decision,
            }

            self.db.client.table("adjustment_feedback").insert(feedback_data).execute()

            logger.info(
                "adjustment_rejected",
                user_id=user_id,
                day_override_id=day_override_id,
                reason=reason,
                time_to_decision_seconds=time_to_decision,
            )

            return updated_override.data[0]

        except Exception as e:
            logger.error(
                "reject_adjustment_failed",
                user_id=user_id,
                day_override_id=day_override_id,
                error=str(e),
            )
            raise

    async def undo_adjustment(
        self, user_id: str, day_override_id: str, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Undo an approved or auto-applied adjustment.

        Flow:
        1. Check if within undo window
        2. Update day_override status to 'undone'
        3. Mark as user_overridden
        4. Create feedback record
        5. Revert plan to original state

        Args:
            user_id: User UUID
            day_override_id: Override UUID
            reason: Why user undid

        Returns:
            Updated day_override
        """
        try:
            # Get override
            override_result = (
                self.db.client.table("day_overrides")
                .select("*")
                .eq("id", day_override_id)
                .eq("user_id", user_id)
                .execute()
            )

            if not override_result.data:
                raise ValueError(f"Day override {day_override_id} not found")

            override = override_result.data[0]

            # Check status
            if override["status"] not in ["approved", "auto_applied"]:
                raise ValueError(
                    f"Cannot undo: adjustment is {override['status']}"
                )

            # Check undo window
            prefs = await self.get_user_preferences(user_id)
            undo_window = timedelta(hours=prefs.undo_window_hours)

            applied_at = (
                datetime.fromisoformat(override["approved_at"])
                if override.get("approved_at")
                else datetime.fromisoformat(override["created_at"])
            )

            if datetime.utcnow() > applied_at + undo_window:
                raise ValueError(
                    f"Undo window expired (max {prefs.undo_window_hours} hours)"
                )

            # Update override
            now = datetime.utcnow()
            updated_override = (
                self.db.client.table("day_overrides")
                .update(
                    {
                        "status": "undone",
                        "undone_at": now.isoformat(),
                        "user_overridden": True,
                        "override_reason": reason,
                    }
                )
                .eq("id", day_override_id)
                .execute()
            )

            # Create feedback record
            feedback_data = {
                "user_id": user_id,
                "day_override_id": day_override_id,
                "action": "undone",
                "adjustment_details": {
                    "reason_code": override.get("reason_code"),
                    "confidence": override.get("confidence"),
                    "user_reason": reason,
                },
            }

            self.db.client.table("adjustment_feedback").insert(feedback_data).execute()

            logger.info(
                "adjustment_undone",
                user_id=user_id,
                day_override_id=day_override_id,
                reason=reason,
            )

            return updated_override.data[0]

        except Exception as e:
            logger.error(
                "undo_adjustment_failed",
                user_id=user_id,
                day_override_id=day_override_id,
                error=str(e),
            )
            raise

    async def get_pending_adjustments(
        self, user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all pending adjustments for user.

        Returns adjustments that are:
        - Status = 'pending'
        - Not expired

        Args:
            user_id: User UUID

        Returns:
            List of pending adjustments with notifications
        """
        try:
            # Get pending overrides
            overrides = (
                self.db.client.table("day_overrides")
                .select("*")
                .eq("user_id", user_id)
                .eq("status", "pending")
                .order("created_at", desc=True)
                .execute()
            )

            # Get associated notifications
            if overrides.data:
                override_ids = [o["id"] for o in overrides.data]

                notifications = (
                    self.db.client.table("notifications")
                    .select("*")
                    .in_("ref_id", override_ids)
                    .eq("notification_type", "adjustment_pending")
                    .execute()
                )

                # Map notifications to overrides
                notif_map = {n["ref_id"]: n for n in notifications.data}

                # Enrich overrides with notifications
                enriched = []
                for override in overrides.data:
                    override["notification"] = notif_map.get(override["id"])
                    enriched.append(override)

                return enriched
            else:
                return []

        except Exception as e:
            logger.error("get_pending_adjustments_failed", user_id=user_id, error=str(e))
            raise

    async def auto_apply_adjustment(
        self, day_override_id: str, user_id: str
    ) -> Dict[str, Any]:
        """
        Auto-apply a pending adjustment after grace period expires.

        Flow:
        1. Update day_override status to 'auto_applied'
        2. Update notification
        3. Create feedback record
        4. Send notification that adjustment was auto-applied

        Args:
            day_override_id: Override UUID
            user_id: User UUID

        Returns:
            Updated day_override
        """
        try:
            # Get override
            override_result = (
                self.db.client.table("day_overrides")
                .select("*")
                .eq("id", day_override_id)
                .eq("user_id", user_id)
                .execute()
            )

            if not override_result.data:
                raise ValueError(f"Day override {day_override_id} not found")

            override = override_result.data[0]

            # Check if still pending
            if override["status"] != "pending":
                logger.warning(
                    "auto_apply_skipped_not_pending",
                    day_override_id=day_override_id,
                    status=override["status"],
                )
                return override

            # Update override
            now = datetime.utcnow()
            updated_override = (
                self.db.client.table("day_overrides")
                .update(
                    {
                        "status": "auto_applied",
                        "approved_at": now.isoformat(),
                    }
                )
                .eq("id", day_override_id)
                .execute()
            )

            # Update pending notification
            self.db.client.table("notifications").update(
                {
                    "read_at": now.isoformat(),
                    "action_taken": "auto_applied",
                    "action_taken_at": now.isoformat(),
                }
            ).eq("ref_id", day_override_id).eq(
                "notification_type", "adjustment_pending"
            ).execute()

            # Create auto-applied notification
            auto_applied_notif = {
                "user_id": user_id,
                "notification_type": "adjustment_auto_applied",
                "title": "Adjustment Auto-Applied",
                "message": f"Your daily adjustment was automatically applied. You can undo it within {self.db.client.table('adjustment_preferences').select('undo_window_hours').eq('user_id', user_id).single().execute().data[0].get('undo_window_hours', 24)} hours.",
                "ref_type": "day_override",
                "ref_id": day_override_id,
                "priority": "normal",
            }

            self.db.client.table("notifications").insert(auto_applied_notif).execute()

            # Create feedback record
            feedback_data = {
                "user_id": user_id,
                "day_override_id": day_override_id,
                "action": "approved",  # Auto-apply counts as approval
                "adjustment_details": {
                    "reason_code": override.get("reason_code"),
                    "confidence": override.get("confidence"),
                    "auto_applied": True,
                },
            }

            self.db.client.table("adjustment_feedback").insert(feedback_data).execute()

            logger.info(
                "adjustment_auto_applied",
                user_id=user_id[:8],
                day_override_id=day_override_id,
            )

            return updated_override.data[0]

        except Exception as e:
            logger.error(
                "auto_apply_adjustment_failed",
                user_id=user_id[:8] if user_id else None,
                day_override_id=day_override_id,
                error=str(e),
                exc_info=True,
            )
            raise


# Singleton instance
adjustment_approval_service = AdjustmentApprovalService()
