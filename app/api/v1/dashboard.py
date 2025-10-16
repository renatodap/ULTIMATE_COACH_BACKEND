"""
Dashboard API endpoint.

Provides unified dashboard summary aggregating nutrition, activities, and body metrics.
"""

import structlog
from fastapi import APIRouter, Depends, status
from uuid import UUID

from app.models.dashboard import DashboardSummary
from app.services.dashboard_service import dashboard_service
from app.api.dependencies import get_current_user

logger = structlog.get_logger()

router = APIRouter()


@router.get(
    "/dashboard/summary",
    response_model=DashboardSummary,
    status_code=status.HTTP_200_OK,
    summary="Get complete dashboard summary",
    description="Aggregate nutrition, activities, and body metrics for dashboard view"
)
async def get_dashboard_summary(
    current_user: dict = Depends(get_current_user)
):
    """
    Get unified dashboard summary for today.

    Aggregates:
    - Today's nutrition (calories, macros, meals)
    - Today's activities (calories burned, workouts)
    - Weight progress (current, trend, goal)
    - Weekly stats (consistency, averages)

    This single endpoint replaces 6+ separate API calls for better mobile performance.
    """
    user_id = UUID(current_user["id"])

    logger.info(
        "dashboard_summary_request",
        user_id=str(user_id)
    )

    return await dashboard_service.get_dashboard_summary(user_id)
