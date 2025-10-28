"""
Background Jobs Service

Automated jobs for adaptive coaching system:
- Daily adjustment analysis (runs every morning at 6am)
- Bi-weekly reassessment checks (runs daily at 8am)
- Grace period auto-apply (runs hourly)
- Skipped item detection (runs daily at 11:59pm)
- Notification cleanup (runs weekly on Sunday at 2am)
- Weekly system prompt updates (runs weekly on Sunday at 3am)

Uses APScheduler for scheduling and execution.
"""

import structlog
from datetime import datetime, date, timedelta
from typing import List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.services.supabase_service import SupabaseService
from app.services.daily_adjustment_service import daily_adjustment_service
from app.services.reassessment_service import reassessment_service
from app.services.adjustment_approval_service import adjustment_approval_service
from app.services.meal_matching_service import meal_matching_service
from app.services.activity_matching_service import activity_matching_service
from app.services.behavioral_tracker import get_behavioral_tracker
from app.services.system_prompt_generator import get_system_prompt_generator
from app.config.personalized_coaching import config as coaching_config

logger = structlog.get_logger()


class BackgroundJobsService:
    """
    Background job orchestration service.

    Manages all automated jobs for the adaptive coaching system.
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.db = SupabaseService()

    async def get_active_users(self) -> List[str]:
        """
        Get list of active users (onboarding complete, not deactivated).

        Returns:
            List of user IDs
        """
        try:
            result = (
                self.db.client.table("profiles")
                .select("id")
                .eq("onboarding_completed", True)
                .is_("deactivated_at", "null")
                .execute()
            )

            user_ids = [row["id"] for row in result.data]

            logger.info(
                "active_users_fetched",
                count=len(user_ids)
            )

            return user_ids

        except Exception as e:
            logger.error(
                "fetch_active_users_failed",
                error=str(e),
                exc_info=True
            )
            return []

    # ============================================================================
    # Job 1: Daily Adjustment Analysis (6am daily)
    # ============================================================================

    async def run_daily_adjustments(self):
        """
        Analyze user context and create daily adjustments.

        Flow:
        1. Get all active users
        2. For each user, check if daily adjustments enabled
        3. Run analyze_and_adjust for today
        4. Log results
        """
        try:
            logger.info("daily_adjustments_job_started")

            users = await self.get_active_users()

            success_count = 0
            error_count = 0
            adjusted_count = 0

            for user_id in users:
                try:
                    # Check if user has daily adjustments enabled
                    prefs = await adjustment_approval_service.get_user_preferences(user_id)

                    if not prefs.daily_adjustments_enabled:
                        logger.debug(
                            "daily_adjustments_disabled",
                            user_id=user_id[:8]
                        )
                        continue

                    # Run daily adjustment
                    override = await daily_adjustment_service.analyze_and_adjust(
                        user_id=user_id,
                        target_date=date.today(),
                        context=None,  # Auto-fetch context from DB
                    )

                    if override:
                        adjusted_count += 1
                        logger.info(
                            "daily_adjustment_created",
                            user_id=user_id[:8],
                            override_id=override.get("id"),
                            reason_code=override.get("reason_code")
                        )

                    success_count += 1

                except Exception as e:
                    error_count += 1
                    logger.error(
                        "daily_adjustment_failed_for_user",
                        user_id=user_id[:8],
                        error=str(e)
                    )

            logger.info(
                "daily_adjustments_job_completed",
                total_users=len(users),
                success=success_count,
                errors=error_count,
                adjustments_created=adjusted_count
            )

        except Exception as e:
            logger.error(
                "daily_adjustments_job_failed",
                error=str(e),
                exc_info=True
            )

    # ============================================================================
    # Job 2: Bi-weekly Reassessment Check (8am daily)
    # ============================================================================

    async def run_reassessment_checks(self):
        """
        Check if any users are due for reassessment and run it.

        Flow:
        1. Get all active users
        2. For each user, check if reassessment is due
        3. If due, run reassessment
        4. Log results
        """
        try:
            logger.info("reassessment_checks_job_started")

            users = await self.get_active_users()

            success_count = 0
            error_count = 0
            reassessed_count = 0

            for user_id in users:
                try:
                    # Check if reassessment is due
                    is_due, next_date = await reassessment_service.check_reassessment_due(user_id)

                    if not is_due:
                        continue

                    logger.info(
                        "reassessment_due",
                        user_id=user_id[:8],
                        next_reassessment_date=next_date.isoformat() if next_date else None
                    )

                    # Run reassessment
                    result = await reassessment_service.run_reassessment(
                        user_id=user_id,
                        force=False,
                    )

                    if result:
                        reassessed_count += 1
                        logger.info(
                            "reassessment_completed",
                            user_id=user_id[:8],
                            needs_new_program=result.get("needs_new_program"),
                            adjustments=result.get("adjustments")
                        )

                    success_count += 1

                except Exception as e:
                    error_count += 1
                    logger.error(
                        "reassessment_failed_for_user",
                        user_id=user_id[:8],
                        error=str(e)
                    )

            logger.info(
                "reassessment_checks_job_completed",
                total_users=len(users),
                success=success_count,
                errors=error_count,
                reassessments_run=reassessed_count
            )

        except Exception as e:
            logger.error(
                "reassessment_checks_job_failed",
                error=str(e),
                exc_info=True
            )

    # ============================================================================
    # Job 3: Grace Period Auto-Apply (hourly)
    # ============================================================================

    async def run_grace_period_auto_apply(self):
        """
        Auto-apply pending adjustments with expired grace periods.

        Flow:
        1. Find all pending adjustments with expired grace periods
        2. Auto-apply each one
        3. Log results
        """
        try:
            logger.info("grace_period_auto_apply_job_started")

            # Find expired pending adjustments
            now = datetime.utcnow()
            result = (
                self.db.client.table("day_overrides")
                .select("*")
                .eq("status", "pending")
                .not_.is_("grace_period_expires_at", "null")
                .lte("grace_period_expires_at", now.isoformat())
                .execute()
            )

            expired_adjustments = result.data

            logger.info(
                "expired_adjustments_found",
                count=len(expired_adjustments)
            )

            success_count = 0
            error_count = 0

            for override in expired_adjustments:
                try:
                    # Auto-apply
                    updated = await adjustment_approval_service.auto_apply_adjustment(
                        day_override_id=override["id"],
                        user_id=override["user_id"]
                    )

                    success_count += 1
                    logger.info(
                        "adjustment_auto_applied",
                        override_id=override["id"],
                        user_id=override["user_id"][:8]
                    )

                except Exception as e:
                    error_count += 1
                    logger.error(
                        "auto_apply_failed",
                        override_id=override["id"],
                        error=str(e)
                    )

            logger.info(
                "grace_period_auto_apply_job_completed",
                total_expired=len(expired_adjustments),
                success=success_count,
                errors=error_count
            )

        except Exception as e:
            logger.error(
                "grace_period_auto_apply_job_failed",
                error=str(e),
                exc_info=True
            )

    # ============================================================================
    # Job 4: Skipped Item Detection (11:59pm daily)
    # ============================================================================

    async def run_skipped_item_detection(self):
        """
        Detect skipped meals and training sessions from yesterday.

        Flow:
        1. Get all active users
        2. For each user, check skipped meals
        3. For each user, check skipped sessions
        4. Log results
        """
        try:
            logger.info("skipped_item_detection_job_started")

            users = await self.get_active_users()
            yesterday = date.today() - timedelta(days=1)

            success_count = 0
            error_count = 0
            skipped_meals_count = 0
            skipped_sessions_count = 0

            for user_id in users:
                try:
                    # Detect skipped meals
                    skipped_meals = await meal_matching_service.match_skipped_meals(
                        user_id=user_id,
                        target_date=yesterday
                    )

                    skipped_meals_count += len(skipped_meals)

                    # Detect skipped sessions
                    skipped_sessions = await activity_matching_service.match_skipped_sessions(
                        user_id=user_id,
                        target_date=yesterday
                    )

                    skipped_sessions_count += len(skipped_sessions)

                    if skipped_meals or skipped_sessions:
                        logger.info(
                            "skipped_items_detected",
                            user_id=user_id[:8],
                            date=yesterday.isoformat(),
                            skipped_meals=len(skipped_meals),
                            skipped_sessions=len(skipped_sessions)
                        )

                    success_count += 1

                except Exception as e:
                    error_count += 1
                    logger.error(
                        "skipped_detection_failed_for_user",
                        user_id=user_id[:8],
                        error=str(e)
                    )

            logger.info(
                "skipped_item_detection_job_completed",
                total_users=len(users),
                success=success_count,
                errors=error_count,
                total_skipped_meals=skipped_meals_count,
                total_skipped_sessions=skipped_sessions_count
            )

        except Exception as e:
            logger.error(
                "skipped_item_detection_job_failed",
                error=str(e),
                exc_info=True
            )

    # ============================================================================
    # Job 5: Notification Cleanup (2am Sunday)
    # ============================================================================

    async def run_notification_cleanup(self):
        """
        Clean up old notifications.

        Flow:
        1. Delete dismissed notifications older than 30 days
        2. Auto-dismiss expired notifications
        3. Log results
        """
        try:
            logger.info("notification_cleanup_job_started")

            thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()

            # Delete old dismissed notifications
            delete_result = (
                self.db.client.table("notifications")
                .delete()
                .not_.is_("dismissed_at", "null")
                .lt("dismissed_at", thirty_days_ago)
                .execute()
            )

            deleted_count = len(delete_result.data) if delete_result.data else 0

            # Auto-dismiss expired notifications
            now = datetime.utcnow().isoformat()
            dismiss_result = (
                self.db.client.table("notifications")
                .update({"dismissed_at": now})
                .lt("expires_at", now)
                .is_("dismissed_at", "null")
                .execute()
            )

            dismissed_count = len(dismiss_result.data) if dismiss_result.data else 0

            logger.info(
                "notification_cleanup_job_completed",
                deleted=deleted_count,
                auto_dismissed=dismissed_count
            )

        except Exception as e:
            logger.error(
                "notification_cleanup_job_failed",
                error=str(e),
                exc_info=True
            )

    # ============================================================================
    # Job 6: Weekly System Prompt Updates (3am Sunday)
    # ============================================================================

    async def run_weekly_prompt_updates(self):
        """
        Update personalized system prompts based on behavioral changes.

        Flow:
        1. Get all users with personalized prompts where last_prompt_update > 7 days ago
        2. For each user:
           - Calculate behavioral metrics (30-day window)
           - Regenerate system prompt with updated behavioral data
           - Increment prompt version
           - Update last_prompt_update timestamp
        3. Log results

        This ensures coaching personas evolve with actual user behavior, not just
        initial consultation data.
        """
        try:
            logger.info("weekly_prompt_updates_job_started")

            # Get users who need prompt updates (configurable days)
            days_threshold = coaching_config.MIN_DAYS_BETWEEN_UPDATES
            threshold_date = (datetime.utcnow() - timedelta(days=days_threshold)).isoformat()

            result = (
                self.db.client.table("profiles")
                .select("id, conversational_profile, behavioral_data, system_prompt_version")
                .not_.is_("coaching_system_prompt", "null")  # Only users with personalized prompts
                .lt("last_prompt_update", threshold_date)
                .eq("onboarding_completed", True)
                .is_("deactivated_at", "null")
                .execute()
            )

            users_needing_update = result.data

            logger.info(
                "users_needing_prompt_update",
                count=len(users_needing_update)
            )

            success_count = 0
            error_count = 0
            updated_count = 0

            # Get singleton services (initialized at startup)
            behavioral_tracker = get_behavioral_tracker()
            prompt_generator = get_system_prompt_generator()

            for user in users_needing_update:
                user_id = user["id"]

                try:
                    # Calculate behavioral metrics (configurable analysis window)
                    behavioral_metrics = await behavioral_tracker.calculate_metrics(
                        user_id=user_id,
                        days=coaching_config.BEHAVIORAL_ANALYSIS_DAYS
                    )

                    # Check if behavior has changed significantly from stored data
                    stored_behavioral_data = user.get("behavioral_data", {})
                    conversational_profile = user.get("conversational_profile")

                    # If no conversational profile, skip (user didn't complete consultation)
                    if not conversational_profile:
                        logger.debug(
                            "skipping_prompt_update_no_consultation",
                            user_id=user_id[:8]
                        )
                        continue

                    # COST OPTIMIZATION: Only update if behavior changed significantly
                    # All thresholds configurable via environment variables
                    old_adherence = stored_behavioral_data.get("adherence_rate_last_30_days", 0)
                    new_adherence = behavioral_metrics.get("adherence_rate_last_30_days", 0)

                    old_logging_rate = stored_behavioral_data.get("logging_rate", 0)
                    new_logging_rate = behavioral_metrics.get("logging_rate", 0)

                    old_streak = stored_behavioral_data.get("meal_logging_streak_days", 0)
                    new_streak = behavioral_metrics.get("meal_logging_streak_days", 0)

                    # Calculate changes
                    adherence_change = abs(new_adherence - old_adherence)
                    logging_change = abs(new_logging_rate - old_logging_rate)
                    streak_change = new_streak - old_streak

                    # Use config helper to determine if update needed
                    should_update = coaching_config.should_update_prompt(
                        adherence_change=adherence_change,
                        logging_change=logging_change,
                        streak_change=streak_change
                    )

                    if not should_update:
                        logger.info(
                            "skipping_prompt_update_no_significant_change",
                            user_id=user_id[:8],
                            adherence_change=f"{adherence_change:.2%}",
                            logging_change=f"{logging_change:.2%}",
                            streak_change=new_streak - old_streak
                        )

                        # Update behavioral_data without regenerating prompt (save $0.05)
                        self.db.client.table("profiles")\
                            .update({
                                "behavioral_data": behavioral_metrics,
                                "last_prompt_update": datetime.utcnow().isoformat()
                            })\
                            .eq("id", user_id)\
                            .execute()

                        success_count += 1
                        continue

                    # Behavior changed significantly - regenerate prompt
                    logger.info(
                        "significant_behavior_change_detected",
                        user_id=user_id[:8],
                        adherence_change=f"{adherence_change:.2%}",
                        logging_change=f"{logging_change:.2%}",
                        streak_change=new_streak - old_streak
                    )

                    # Regenerate system prompt with updated behavioral data
                    updated_prompt = await prompt_generator.update_prompt_from_behavior(
                        user_id=user_id,
                        conversational_profile=conversational_profile,
                        current_behavioral_data=behavioral_metrics,
                        previous_behavioral_data=stored_behavioral_data
                    )

                    # Update database with new prompt, incremented version, and timestamp
                    current_version = user.get("system_prompt_version", 1)
                    new_version = current_version + 1

                    update_result = (
                        self.db.client.table("profiles")
                        .update({
                            "coaching_system_prompt": updated_prompt,
                            "behavioral_data": behavioral_metrics,
                            "system_prompt_version": new_version,
                            "last_prompt_update": datetime.utcnow().isoformat()
                        })
                        .eq("id", user_id)
                        .execute()
                    )

                    updated_count += 1
                    logger.info(
                        "system_prompt_updated",
                        user_id=user_id[:8],
                        new_version=new_version,
                        adherence_rate=behavioral_metrics.get("adherence_rate_last_30_days"),
                        logging_streak=behavioral_metrics.get("meal_logging_streak_days")
                    )

                    success_count += 1

                except Exception as e:
                    error_count += 1
                    logger.error(
                        "prompt_update_failed_for_user",
                        user_id=user_id[:8],
                        error=str(e),
                        exc_info=True
                    )

            logger.info(
                "weekly_prompt_updates_job_completed",
                total_users=len(users_needing_update),
                success=success_count,
                errors=error_count,
                prompts_updated=updated_count
            )

        except Exception as e:
            logger.error(
                "weekly_prompt_updates_job_failed",
                error=str(e),
                exc_info=True
            )

    # ============================================================================
    # Scheduler Control
    # ============================================================================

    def start(self):
        """Start the background job scheduler."""
        logger.info("background_jobs_starting")

        # Job 1: Daily Adjustments - 6am daily
        self.scheduler.add_job(
            self.run_daily_adjustments,
            CronTrigger(hour=6, minute=0),
            id="daily_adjustments",
            name="Daily Adjustment Analysis",
            replace_existing=True
        )

        # Job 2: Reassessment Checks - 8am daily
        self.scheduler.add_job(
            self.run_reassessment_checks,
            CronTrigger(hour=8, minute=0),
            id="reassessment_checks",
            name="Bi-weekly Reassessment Check",
            replace_existing=True
        )

        # Job 3: Grace Period Auto-Apply - hourly
        self.scheduler.add_job(
            self.run_grace_period_auto_apply,
            CronTrigger(minute=0),
            id="grace_period_auto_apply",
            name="Grace Period Auto-Apply",
            replace_existing=True
        )

        # Job 4: Skipped Item Detection - 11:59pm daily
        self.scheduler.add_job(
            self.run_skipped_item_detection,
            CronTrigger(hour=23, minute=59),
            id="skipped_item_detection",
            name="Skipped Item Detection",
            replace_existing=True
        )

        # Job 5: Notification Cleanup - 2am Sunday
        self.scheduler.add_job(
            self.run_notification_cleanup,
            CronTrigger(day_of_week="sun", hour=2, minute=0),
            id="notification_cleanup",
            name="Notification Cleanup",
            replace_existing=True
        )

        # Job 6: Weekly System Prompt Updates - Configurable schedule
        schedule = coaching_config.get_prompt_update_schedule()
        self.scheduler.add_job(
            self.run_weekly_prompt_updates,
            CronTrigger(
                day_of_week=schedule["day_of_week"],
                hour=schedule["hour"],
                minute=schedule["minute"]
            ),
            id="weekly_prompt_updates",
            name="Weekly System Prompt Updates",
            replace_existing=True
        )

        self.scheduler.start()

        logger.info(
            "background_jobs_started",
            jobs=[
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None
                }
                for job in self.scheduler.get_jobs()
            ]
        )

    def shutdown(self):
        """Shutdown the scheduler gracefully."""
        logger.info("background_jobs_shutting_down")
        self.scheduler.shutdown(wait=True)
        logger.info("background_jobs_stopped")


# Global singleton instance
background_jobs_service = BackgroundJobsService()
