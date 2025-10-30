"""
Check-In API Endpoints

Daily accountability system:
- POST /check-ins - Create/update daily check-in
- GET /check-ins - Get recent check-ins
- GET /check-ins/today - Get today's check-in
- GET /check-ins/streak - Get streak data
- GET /notifications/preferences - Get notification preferences
- PUT /notifications/preferences - Update notification preferences
"""

import structlog
from datetime import date
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.dependencies import get_current_user
from app.models.check_in import (
    CreateCheckInRequest,
    CheckInResponse,
    UserStreakResponse,
    NotificationPreferencesResponse,
    UpdateNotificationPreferencesRequest,
)
from app.services.check_in_service import check_in_service

logger = structlog.get_logger()

router = APIRouter(prefix="/check-ins", tags=["check-ins"])
limiter = Limiter(key_func=get_remote_address)


# ============================================================================
# CHECK-IN ENDPOINTS
# ============================================================================
# NOTE: Rate limiting is IP-based (30/hour per IP). This is intentional for MVP:
# - Per-user rate limiting requires middleware that runs after auth
# - IP-based limiting is simple and works for 95% of cases
# - 30/hour is generous enough that shared IPs (corporate, VPN) won't cause issues
# - Future: Implement custom middleware for true per-user rate limiting
# ============================================================================

@router.post("", response_model=CheckInResponse, status_code=201)
@limiter.limit("30/hour")  # IP-based rate limit (MVP approach)
async def create_check_in(
    request: Request,
    data: CreateCheckInRequest,
    current_user=Depends(get_current_user),
):
    """
    Create or update daily check-in.

    If a check-in already exists for the specified date, it will be updated.
    Creating a check-in automatically updates your streak.

    **Rate Limit:** 30 requests/hour per IP

    **Request Body:**
    - check_in_date: Date of check-in (YYYY-MM-DD)
    - energy_level: 1-10 scale
    - hunger_level: 1-10 scale
    - stress_level: 1-10 scale
    - sleep_quality: 1-10 scale
    - motivation: 1-10 scale
    - notes: Optional text notes

    **Response:**
    - Returns full check-in data including AI-calculated fields
    """
    user_id = current_user["id"]

    logger.info(
        "check_in_request",
        user_id=user_id,
        date=str(data.check_in_date),
        energy=data.energy_level,
    )

    try:
        check_in = await check_in_service.create_check_in(user_id, data)
        return check_in

    except ValueError as e:
        # Date validation errors (400 Bad Request)
        logger.warning(
            "check_in_validation_failed",
            user_id=user_id,
            error=str(e),
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(
            "check_in_creation_failed",
            user_id=user_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Failed to create check-in")


@router.get("", response_model=List[CheckInResponse])
async def get_recent_check_ins(
    limit: int = 30,
    current_user=Depends(get_current_user),
):
    """
    Get recent check-ins (up to 30 days).

    **Query Parameters:**
    - limit: Max number of check-ins to return (default 30)

    **Response:**
    - Array of check-ins, ordered by date (most recent first)
    """
    user_id = current_user["id"]

    logger.info("fetching_recent_check_ins", user_id=user_id, limit=limit)

    try:
        check_ins = await check_in_service.get_recent_check_ins(user_id, limit)
        return check_ins

    except Exception as e:
        logger.error(
            "check_ins_fetch_failed",
            user_id=user_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Failed to fetch check-ins")


@router.get("/today", response_model=CheckInResponse)
async def get_today_check_in(
    current_user=Depends(get_current_user),
):
    """
    Get today's check-in (if it exists).

    **Response:**
    - Today's check-in data, or 404 if not checked in yet
    """
    user_id = current_user["id"]
    today = date.today()

    logger.info("fetching_today_check_in", user_id=user_id, date=str(today))

    try:
        check_in = await check_in_service.get_check_in(user_id, today)

        if not check_in:
            raise HTTPException(status_code=404, detail="No check-in for today")

        return check_in

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "today_check_in_fetch_failed",
            user_id=user_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Failed to fetch today's check-in")


@router.get("/streak", response_model=UserStreakResponse)
async def get_user_streak(
    current_user=Depends(get_current_user),
):
    """
    Get user's check-in streak data.

    **Response:**
    - current_streak: Current consecutive days
    - longest_streak: Best streak ever
    - total_check_ins: Lifetime total
    - last_check_in_date: Last check-in date
    """
    user_id = current_user["id"]

    logger.info("fetching_user_streak", user_id=user_id)

    try:
        streak = await check_in_service.get_user_streak(user_id)

        if not streak:
            # Return zero streak if user never checked in
            from datetime import datetime

            return UserStreakResponse(
                user_id=user_id,
                current_streak=0,
                longest_streak=0,
                last_check_in_date=None,
                total_check_ins=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

        return streak

    except Exception as e:
        logger.error(
            "streak_fetch_failed",
            user_id=user_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Failed to fetch streak")


# ============================================================================
# NOTIFICATION PREFERENCES ENDPOINTS
# ============================================================================

@router.get("/notifications/preferences", response_model=NotificationPreferencesResponse)
async def get_notification_preferences(
    current_user=Depends(get_current_user),
):
    """
    Get user's notification preferences.

    Creates default preferences if they don't exist yet.

    **Response:**
    - Boolean flags for each notification type
    """
    user_id = current_user["id"]

    logger.info("fetching_notification_preferences", user_id=user_id)

    try:
        prefs = await check_in_service.get_notification_preferences(user_id)
        return prefs

    except Exception as e:
        logger.error(
            "notification_preferences_fetch_failed",
            user_id=user_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail="Failed to fetch notification preferences"
        )


@router.put("/notifications/preferences", response_model=NotificationPreferencesResponse)
@limiter.limit("10/hour")  # Reasonable limit for preference updates
async def update_notification_preferences(
    request: Request,
    data: UpdateNotificationPreferencesRequest,
    current_user=Depends(get_current_user),
):
    """
    Update user's notification preferences.

    **Rate Limit:** 10 requests/hour per IP

    **Request Body:**
    - Only include fields you want to update
    - All fields are optional booleans

    **Response:**
    - Updated notification preferences
    """
    user_id = current_user["id"]

    logger.info("updating_notification_preferences", user_id=user_id)

    try:
        prefs = await check_in_service.update_notification_preferences(user_id, data)
        return prefs

    except Exception as e:
        logger.error(
            "notification_preferences_update_failed",
            user_id=user_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail="Failed to update notification preferences"
        )
