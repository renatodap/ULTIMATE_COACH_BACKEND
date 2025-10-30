"""
Check-In Service - Daily Accountability System

Handles:
- Daily check-in creation/retrieval/update
- Streak calculation (auto-updated via database trigger)
- Notification preferences management
"""

import structlog
from datetime import date, datetime
from typing import List, Optional
from app.services.supabase_service import SupabaseService
from app.models.check_in import (
    CreateCheckInRequest,
    UpdateCheckInRequest,
    CheckInResponse,
    UserStreakResponse,
    NotificationPreferencesResponse,
    UpdateNotificationPreferencesRequest,
)

logger = structlog.get_logger()


class CheckInService:
    """Service for daily check-ins and accountability features"""

    def __init__(self):
        self.db = SupabaseService()

    # ========================================================================
    # CHECK-IN OPERATIONS
    # ========================================================================

    async def create_check_in(
        self, user_id: str, data: CreateCheckInRequest
    ) -> CheckInResponse:
        """
        Create or update daily check-in.

        If check-in for this date already exists, updates it.
        Triggers automatic streak calculation.

        Args:
            user_id: User UUID
            data: Check-in data (energy, hunger, stress, sleep, motivation, notes)

        Returns:
            CheckInResponse with created/updated check-in data
        """
        logger.info(
            "creating_check_in",
            user_id=user_id,
            date=str(data.check_in_date),
            energy=data.energy_level,
        )

        try:
            # Validate check-in date
            today = date.today()
            one_year_ago = date(today.year - 1, today.month, today.day)

            if data.check_in_date > today:
                raise ValueError(
                    f"Cannot check in for future dates. Today is {today}, "
                    f"but you tried to check in for {data.check_in_date}"
                )

            if data.check_in_date < one_year_ago:
                raise ValueError(
                    f"Cannot check in for dates older than 1 year. "
                    f"Earliest allowed date is {one_year_ago}"
                )

            # Check if check-in already exists for this date
            existing = (
                self.db.client.table("daily_check_ins")
                .select("*")
                .eq("user_id", user_id)
                .eq("check_in_date", str(data.check_in_date))
                .execute()
            )

            if existing.data:
                # Update existing check-in
                check_in_id = existing.data[0]["id"]
                result = (
                    self.db.client.table("daily_check_ins")
                    .update(
                        {
                            "energy_level": data.energy_level,
                            "hunger_level": data.hunger_level,
                            "stress_level": data.stress_level,
                            "sleep_quality": data.sleep_quality,
                            "motivation": data.motivation,
                            "notes": data.notes,
                            "updated_at": datetime.utcnow().isoformat(),
                        }
                    )
                    .eq("id", check_in_id)
                    .execute()
                )

                logger.info("check_in_updated", user_id=user_id, check_in_id=check_in_id)
            else:
                # Create new check-in
                result = (
                    self.db.client.table("daily_check_ins")
                    .insert(
                        {
                            "user_id": user_id,
                            "check_in_date": str(data.check_in_date),
                            "energy_level": data.energy_level,
                            "hunger_level": data.hunger_level,
                            "stress_level": data.stress_level,
                            "sleep_quality": data.sleep_quality,
                            "motivation": data.motivation,
                            "notes": data.notes,
                        }
                    )
                    .execute()
                )

                logger.info("check_in_created", user_id=user_id, date=str(data.check_in_date))

            if not result.data:
                raise Exception("Failed to create/update check-in")

            return CheckInResponse(**result.data[0])

        except Exception as e:
            logger.error(
                "check_in_creation_failed",
                user_id=user_id,
                error=str(e),
                exc_info=True,
            )
            raise

    async def get_check_in(
        self, user_id: str, check_in_date: date
    ) -> Optional[CheckInResponse]:
        """
        Get check-in for specific date.

        Args:
            user_id: User UUID
            check_in_date: Date to retrieve

        Returns:
            CheckInResponse or None if not found
        """
        logger.info("fetching_check_in", user_id=user_id, date=str(check_in_date))

        try:
            result = (
                self.db.client.table("daily_check_ins")
                .select("*")
                .eq("user_id", user_id)
                .eq("check_in_date", str(check_in_date))
                .execute()
            )

            if not result.data:
                return None

            return CheckInResponse(**result.data[0])

        except Exception as e:
            logger.error(
                "check_in_fetch_failed",
                user_id=user_id,
                error=str(e),
                exc_info=True,
            )
            raise

    async def get_recent_check_ins(
        self, user_id: str, limit: int = 30
    ) -> List[CheckInResponse]:
        """
        Get recent check-ins (descending by date).

        Args:
            user_id: User UUID
            limit: Max number to return (default 30 days)

        Returns:
            List of CheckInResponse objects
        """
        logger.info("fetching_recent_check_ins", user_id=user_id, limit=limit)

        try:
            result = (
                self.db.client.table("daily_check_ins")
                .select("*")
                .eq("user_id", user_id)
                .order("check_in_date", desc=True)
                .limit(limit)
                .execute()
            )

            return [CheckInResponse(**item) for item in result.data]

        except Exception as e:
            logger.error(
                "recent_check_ins_fetch_failed",
                user_id=user_id,
                error=str(e),
                exc_info=True,
            )
            raise

    # ========================================================================
    # STREAK OPERATIONS
    # ========================================================================

    async def get_user_streak(self, user_id: str) -> Optional[UserStreakResponse]:
        """
        Get user's streak data.

        Streak is automatically calculated by database trigger when check-ins
        are created.

        Args:
            user_id: User UUID

        Returns:
            UserStreakResponse or None if no streaks yet
        """
        logger.info("fetching_user_streak", user_id=user_id)

        try:
            result = (
                self.db.client.table("user_streaks")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )

            if not result.data:
                return None

            return UserStreakResponse(**result.data[0])

        except Exception as e:
            logger.error(
                "streak_fetch_failed",
                user_id=user_id,
                error=str(e),
                exc_info=True,
            )
            raise

    # ========================================================================
    # NOTIFICATION PREFERENCES
    # ========================================================================

    async def get_notification_preferences(
        self, user_id: str
    ) -> NotificationPreferencesResponse:
        """
        Get user's notification preferences.

        Creates default preferences if they don't exist.

        Args:
            user_id: User UUID

        Returns:
            NotificationPreferencesResponse
        """
        logger.info("fetching_notification_preferences", user_id=user_id)

        try:
            result = (
                self.db.client.table("notification_preferences")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )

            if not result.data:
                # Create default preferences
                result = (
                    self.db.client.table("notification_preferences")
                    .insert({"user_id": user_id})
                    .execute()
                )

            return NotificationPreferencesResponse(**result.data[0])

        except Exception as e:
            logger.error(
                "notification_preferences_fetch_failed",
                user_id=user_id,
                error=str(e),
                exc_info=True,
            )
            raise

    async def update_notification_preferences(
        self, user_id: str, data: UpdateNotificationPreferencesRequest
    ) -> NotificationPreferencesResponse:
        """
        Update user's notification preferences.

        Args:
            user_id: User UUID
            data: Preferences to update (only provided fields are updated)

        Returns:
            Updated NotificationPreferencesResponse
        """
        logger.info("updating_notification_preferences", user_id=user_id)

        try:
            # Build update dict (only include non-None fields)
            update_data = {k: v for k, v in data.dict().items() if v is not None}
            update_data["updated_at"] = datetime.utcnow().isoformat()

            result = (
                self.db.client.table("notification_preferences")
                .update(update_data)
                .eq("user_id", user_id)
                .execute()
            )

            if not result.data:
                raise Exception("Failed to update notification preferences")

            return NotificationPreferencesResponse(**result.data[0])

        except Exception as e:
            logger.error(
                "notification_preferences_update_failed",
                user_id=user_id,
                error=str(e),
                exc_info=True,
            )
            raise


# Singleton instance
check_in_service = CheckInService()
