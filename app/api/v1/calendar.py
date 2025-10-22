"""
Calendar API endpoints

Provides calendar views and progress tracking for user programs.
"""

import structlog
from datetime import date, timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.dependencies import get_current_user, get_supabase_client
from typing import List, Optional

router = APIRouter()
logger = structlog.get_logger()


@router.get("/calendar/full")
async def get_calendar_full(
    user_id: str = Query(..., description="User ID"),
    date: str = Query(..., description="ISO date (YYYY-MM-DD)"),
    range: str = Query("week", description="Range: 'day' or 'week'"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get full calendar events for a specific date or week.

    Returns enriched calendar events with plan details.
    Frontend: app/plan/calendar/page.tsx

    Response:
    {
        "events": [
            {
                "id": "uuid",
                "date": "2025-10-22",
                "event_type": "training",
                "ref_table": "session_instances",
                "ref_id": "uuid",
                "title": "Upper Body Strength",
                "details": {...},
                "status": "completed"
            }
        ]
    }
    """
    try:
        client = get_supabase_client()

        # Verify user authorization
        if user_id != current_user['id']:
            raise HTTPException(status_code=403, detail="Cannot access other users' calendars")

        # Parse target date
        try:
            target_date = datetime.fromisoformat(date).date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

        # Calculate date range
        if range == "week":
            # Week starts on Monday
            start_date = target_date - timedelta(days=target_date.weekday())
            end_date = start_date + timedelta(days=6)
        else:  # day
            start_date = target_date
            end_date = target_date

        logger.info(
            "fetching_calendar",
            user_id=user_id,
            start_date=str(start_date),
            end_date=str(end_date),
            range=range
        )

        # Fetch calendar events
        result = (
            client.table("calendar_events")
            .select("*")
            .eq("user_id", user_id)
            .gte("date", str(start_date))
            .lte("date", str(end_date))
            .order("date", desc=False)
            .order("created_at", desc=False)
            .execute()
        )

        events = result.data if result.data else []

        logger.info(
            "calendar_fetched",
            user_id=user_id,
            event_count=len(events),
            date_range=f"{start_date} to {end_date}"
        )

        return {"events": events}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_calendar_full_failed", error=str(e), user_id=user_id, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch calendar: {e}")


@router.get("/calendar/summary")
async def get_calendar_summary(
    user_id: str = Query(..., description="User ID"),
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get calendar summary with adherence counts for a date range.

    Frontend: app/plan/progress/page.tsx

    Response:
    {
        "summary": [
            {
                "date": "2025-10-22",
                "counts": {
                    "completed": 3,
                    "similar": 1,
                    "skipped": 0,
                    "planned": 2,
                    "modified": 0
                }
            }
        ]
    }
    """
    try:
        client = get_supabase_client()

        # Verify user authorization
        if user_id != current_user['id']:
            raise HTTPException(status_code=403, detail="Cannot access other users' data")

        # Parse dates
        try:
            start = datetime.fromisoformat(start_date).date()
            end = datetime.fromisoformat(end_date).date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

        logger.info(
            "fetching_calendar_summary",
            user_id=user_id,
            start_date=str(start),
            end_date=str(end)
        )

        # Fetch all events in range
        result = (
            client.table("calendar_events")
            .select("date, status")
            .eq("user_id", user_id)
            .gte("date", str(start))
            .lte("date", str(end))
            .execute()
        )

        events = result.data if result.data else []

        # Aggregate counts by date
        summary_map = {}
        current_date = start

        # Initialize all dates in range
        while current_date <= end:
            summary_map[str(current_date)] = {
                "completed": 0,
                "similar": 0,
                "skipped": 0,
                "planned": 0,
                "modified": 0
            }
            current_date += timedelta(days=1)

        # Count events by status
        for event in events:
            event_date = event['date']
            status = event.get('status', 'planned')

            if event_date in summary_map:
                summary_map[event_date][status] = summary_map[event_date].get(status, 0) + 1

        # Build summary array
        summary = [
            {
                "date": date_str,
                "counts": counts
            }
            for date_str, counts in sorted(summary_map.items())
        ]

        logger.info(
            "calendar_summary_generated",
            user_id=user_id,
            day_count=len(summary),
            total_events=len(events)
        )

        return {"summary": summary}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_calendar_summary_failed", error=str(e), user_id=user_id, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate calendar summary: {e}")
