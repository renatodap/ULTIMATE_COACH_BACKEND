"""
Scheduled Tasks for Adaptive Program Reassessments

Drop-in file for: ULTIMATE_COACH_BACKEND/app/tasks/scheduled_tasks.py

Uses APScheduler to run automatic bi-weekly reassessments.

Integration with main.py:
```python
from app.tasks import init_scheduler, shutdown_scheduler

@app.on_event("startup")
async def startup():
    init_scheduler()

@app.on_event("shutdown")
async def shutdown():
    shutdown_scheduler()
```
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta, date
from typing import List, Optional
import os
import asyncio

# Import Supabase client (assumes it's initialized in main app)
from supabase import create_client, Client

# Import reassessment orchestrator
import sys
from pathlib import Path

# Add ultimate_ai_consultation to path
ultimate_ai_consultation_path = os.getenv(
    "ULTIMATE_AI_CONSULTATION_PATH",
    str(Path(__file__).parent.parent.parent.parent.parent / "ultimate_ai_consultation")
)
sys.path.insert(0, ultimate_ai_consultation_path)

from ultimate_ai_consultation.services.adaptive import ReassessmentOrchestrator


# =============================================================================
# Configuration
# =============================================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Service role for cron jobs

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Scheduler instance (initialized on startup)
scheduler: Optional[AsyncIOScheduler] = None


# =============================================================================
# Scheduler Initialization
# =============================================================================


def init_scheduler():
    """
    Initialize APScheduler on application startup.

    Schedules:
    - Daily check at 2 AM UTC for due reassessments
    - Optional: Hourly check for high-priority users
    """
    global scheduler

    if scheduler is not None:
        print("Scheduler already initialized")
        return

    scheduler = AsyncIOScheduler(timezone="UTC")

    # Schedule daily reassessment check at 2 AM UTC
    scheduler.add_job(
        func=trigger_daily_reassessment_check,
        trigger=CronTrigger(hour=2, minute=0),
        id="daily_reassessment_check",
        name="Check for users due for bi-weekly reassessment",
        replace_existing=True,
    )

    # Optional: Hourly check for manual triggers
    scheduler.add_job(
        func=process_manual_reassessment_queue,
        trigger=CronTrigger(minute=0),  # Every hour
        id="manual_reassessment_queue",
        name="Process manually triggered reassessments",
        replace_existing=True,
    )

    scheduler.start()
    print("✅ Scheduler initialized - automatic reassessments enabled")


def shutdown_scheduler():
    """Shutdown scheduler gracefully"""
    global scheduler

    if scheduler is not None:
        scheduler.shutdown(wait=True)
        scheduler = None
        print("✅ Scheduler shutdown complete")


# =============================================================================
# Main Reassessment Check
# =============================================================================


async def trigger_daily_reassessment_check():
    """
    Run daily to check which users are due for bi-weekly reassessment.

    Called automatically at 2 AM UTC by APScheduler.

    Logic:
    1. Query all active plans
    2. Check if 14 days have passed since last version
    3. Run reassessment for due users
    4. Send notification via coach
    """

    print(f"[{datetime.utcnow()}] Starting daily reassessment check...")

    try:
        # Get all users with active plans
        users_due = await get_users_due_for_reassessment()

        print(f"Found {len(users_due)} users due for reassessment")

        # Process each user
        for user_data in users_due:
            try:
                await run_reassessment_for_user(
                    user_id=user_data["user_id"],
                    plan_id=user_data["plan_id"],
                    plan_version=user_data["version"],
                )
            except Exception as e:
                print(f"Error reassessing user {user_data['user_id']}: {e}")
                # Continue with other users even if one fails

        print(f"[{datetime.utcnow()}] Daily reassessment check complete")

    except Exception as e:
        print(f"Error in daily reassessment check: {e}")


async def get_users_due_for_reassessment() -> List[dict]:
    """
    Query database for users whose plans are due for reassessment.

    Returns list of:
    [
        {
            "user_id": "uuid",
            "plan_id": "uuid",
            "version": 1,
            "valid_from": "2024-01-01",
            "days_since_creation": 14
        },
        ...
    ]
    """

    try:
        # Query active plans created >= 14 days ago
        fourteen_days_ago = (datetime.utcnow() - timedelta(days=14)).date()

        result = supabase.table("plan_versions") \
            .select("id, user_id, version, valid_from") \
            .eq("status", "active") \
            .lte("valid_from", fourteen_days_ago.isoformat()) \
            .execute()

        users_due = []

        for plan in result.data:
            valid_from = datetime.fromisoformat(plan["valid_from"]).date()
            days_since = (date.today() - valid_from).days

            # Check if it's a 14-day interval (14, 28, 42, etc.)
            if days_since % 14 == 0:
                users_due.append({
                    "user_id": plan["user_id"],
                    "plan_id": plan["id"],
                    "version": plan["version"],
                    "valid_from": plan["valid_from"],
                    "days_since_creation": days_since,
                })

        return users_due

    except Exception as e:
        print(f"Error querying users due for reassessment: {e}")
        return []


# =============================================================================
# Run Reassessment for Single User
# =============================================================================


async def run_reassessment_for_user(
    user_id: str,
    plan_id: str,
    plan_version: int,
    manual_trigger: bool = False,
) -> bool:
    """
    Run complete reassessment workflow for a single user.

    Returns True if successful, False if failed.
    """

    print(f"Running reassessment for user {user_id}, plan v{plan_version}")

    try:
        # Initialize orchestrator
        orchestrator = ReassessmentOrchestrator(supabase_client=supabase)

        # Run reassessment
        result = await orchestrator.run_reassessment(
            user_id=user_id,
            plan_version=plan_version,
            manual_trigger=manual_trigger,
        )

        if result.success:
            print(f"✅ Reassessment complete for user {user_id}")
            print(f"   New version: v{result.new_version}")
            print(f"   Adjustments: {len(result.adjustments_made)}")

            # Send notification to user via coach
            await send_reassessment_notification(
                user_id=user_id,
                result=result,
            )

            return True

        else:
            print(f"❌ Reassessment failed for user {user_id}: {result.error_message}")
            return False

    except Exception as e:
        print(f"❌ Error running reassessment for user {user_id}: {e}")
        return False


async def send_reassessment_notification(
    user_id: str,
    result: Any,  # ReassessmentResult object
):
    """
    Send reassessment summary to user via coach conversation.

    Adds a system message to the coach chat with the update.
    """

    try:
        # Build notification message
        message = result.user_message  # Pre-generated by orchestrator

        # Insert as system message in coach conversation
        supabase.table("coach_messages").insert({
            "user_id": user_id,
            "role": "assistant",
            "content": message,
            "timestamp": datetime.utcnow().isoformat(),
            "message_type": "reassessment_notification",
        }).execute()

        print(f"Sent reassessment notification to user {user_id}")

    except Exception as e:
        print(f"Error sending reassessment notification: {e}")


# =============================================================================
# Manual Reassessment Queue
# =============================================================================


async def process_manual_reassessment_queue():
    """
    Process manually triggered reassessments from queue.

    Users can request manual reassessment via API.
    These are queued and processed hourly to avoid overload.
    """

    try:
        # Check for pending manual reassessments
        result = supabase.table("reassessment_queue") \
            .select("*") \
            .eq("status", "pending") \
            .order("created_at", desc=False) \
            .limit(10) \
            .execute()

        if not result.data:
            return

        print(f"Processing {len(result.data)} manual reassessments from queue")

        for item in result.data:
            try:
                # Mark as processing
                supabase.table("reassessment_queue") \
                    .update({"status": "processing"}) \
                    .eq("id", item["id"]) \
                    .execute()

                # Run reassessment
                success = await run_reassessment_for_user(
                    user_id=item["user_id"],
                    plan_id=item["plan_id"],
                    plan_version=item["plan_version"],
                    manual_trigger=True,
                )

                # Update queue status
                new_status = "completed" if success else "failed"
                supabase.table("reassessment_queue") \
                    .update({
                        "status": new_status,
                        "completed_at": datetime.utcnow().isoformat(),
                    }) \
                    .eq("id", item["id"]) \
                    .execute()

            except Exception as e:
                print(f"Error processing manual reassessment {item['id']}: {e}")

                # Mark as failed
                supabase.table("reassessment_queue") \
                    .update({
                        "status": "failed",
                        "error_message": str(e),
                    }) \
                    .eq("id", item["id"]) \
                    .execute()

    except Exception as e:
        print(f"Error processing manual reassessment queue: {e}")


# =============================================================================
# Helper: Queue Manual Reassessment
# =============================================================================


async def queue_manual_reassessment(
    user_id: str,
    plan_id: str,
    plan_version: int,
    requested_by: str = "user",
) -> str:
    """
    Add manual reassessment request to queue.

    Called from API endpoint when user requests reassessment.

    Returns queue_id.
    """

    try:
        result = supabase.table("reassessment_queue").insert({
            "user_id": user_id,
            "plan_id": plan_id,
            "plan_version": plan_version,
            "requested_by": requested_by,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
        }).execute()

        queue_id = result.data[0]["id"]
        print(f"Queued manual reassessment: {queue_id}")

        return queue_id

    except Exception as e:
        print(f"Error queuing manual reassessment: {e}")
        raise


# =============================================================================
# Migration Helper: Create reassessment_queue Table
# =============================================================================

"""
SQL to create reassessment_queue table:

CREATE TABLE IF NOT EXISTS reassessment_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    plan_id UUID NOT NULL REFERENCES plan_versions(id),
    plan_version INTEGER NOT NULL,

    requested_by TEXT NOT NULL DEFAULT 'user',
    status TEXT NOT NULL DEFAULT 'pending',
    -- Status: pending, processing, completed, failed

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,

    error_message TEXT,

    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE
);

CREATE INDEX idx_reassessment_queue_status ON reassessment_queue(status);
CREATE INDEX idx_reassessment_queue_user ON reassessment_queue(user_id);
"""
