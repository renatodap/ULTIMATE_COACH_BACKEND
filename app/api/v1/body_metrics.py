"""
Body Metrics API endpoints.

Handles weight tracking, body composition, and trend analysis.
"""

import structlog
from fastapi import APIRouter, HTTPException, status, Depends, Query, Request
from typing import Optional
from uuid import UUID
from datetime import date

from app.models.body_metrics import (
    CreateBodyMetricRequest,
    UpdateBodyMetricRequest,
    BodyMetric,
    BodyMetricListResponse,
    WeightTrend,
    SuccessResponse
)
from app.services.body_metrics_service import body_metrics_service
from app.api.dependencies import get_current_user

logger = structlog.get_logger()

router = APIRouter()


@router.get(
    "/body-metrics",
    response_model=BodyMetricListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user's body metrics",
    description="Retrieve body metrics for authenticated user with optional date filtering"
)
async def get_body_metrics(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=100, description="Max metrics to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get body metrics for the authenticated user.

    - **start_date**: Filter metrics after this date (ISO format)
    - **end_date**: Filter metrics before this date (ISO format)
    - **limit**: Maximum number of metrics to return (1-100)
    - **offset**: Number of metrics to skip (for pagination)

    Returns metrics sorted by recorded_at descending (most recent first).
    """
    try:
        # Parse dates if provided
        start_date_obj = date.fromisoformat(start_date) if start_date else None
        end_date_obj = date.fromisoformat(end_date) if end_date else None

        logger.info(
            "fetching_body_metrics",
            user_id=current_user["id"],
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )

        metrics = await body_metrics_service.get_user_body_metrics(
            user_id=UUID(current_user["id"]),
            start_date=start_date_obj,
            end_date=end_date_obj,
            limit=limit,
            offset=offset
        )

        logger.info(
            "body_metrics_fetched",
            user_id=current_user["id"],
            count=len(metrics)
        )

        return BodyMetricListResponse(
            metrics=[BodyMetric(**metric) for metric in metrics],
            total=len(metrics),
            limit=limit,
            offset=offset
        )

    except ValueError as e:
        logger.warning(
            "invalid_date_format",
            user_id=current_user["id"],
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        logger.error(
            "fetch_body_metrics_error",
            user_id=current_user["id"],
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch body metrics"
        )


@router.get(
    "/body-metrics/latest",
    response_model=BodyMetric,
    status_code=status.HTTP_200_OK,
    summary="Get latest body metric",
    description="Get the most recent body metric entry"
)
async def get_latest_body_metric(
    current_user: dict = Depends(get_current_user)
):
    """
    Get the most recent body metric for the authenticated user.

    Returns:
    - Latest weight measurement
    - Body fat percentage (if tracked)
    - Recording timestamp
    - Notes
    """
    try:
        logger.info(
            "fetching_latest_body_metric",
            user_id=current_user["id"]
        )

        metric = await body_metrics_service.get_latest_body_metric(
            user_id=UUID(current_user["id"])
        )

        if not metric:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No body metrics found"
            )

        logger.info(
            "latest_body_metric_fetched",
            user_id=current_user["id"],
            weight_kg=metric.get("weight_kg")
        )

        return BodyMetric(**metric)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "fetch_latest_body_metric_error",
            user_id=current_user["id"],
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch latest body metric"
        )


@router.get(
    "/body-metrics/trend",
    response_model=WeightTrend,
    status_code=status.HTTP_200_OK,
    summary="Get weight trend analysis",
    description="Calculate weight trend over a specified period"
)
async def get_weight_trend(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    current_user: dict = Depends(get_current_user)
):
    """
    Calculate weight trend analysis.

    - **days**: Number of days to analyze (default: 7, max: 90)

    Returns:
    - current_weight: Most recent weight (kg)
    - previous_weight: Weight N days ago (kg)
    - change_kg: Weight change (positive = gain, negative = loss)
    - change_percentage: Percentage change
    - trend_direction: "up", "down", or "stable"
    - days_between: Actual days between measurements
    - avg_change_per_week: Average kg change per week
    """
    try:
        logger.info(
            "calculating_weight_trend",
            user_id=current_user["id"],
            days=days
        )

        trend = await body_metrics_service.calculate_weight_trend(
            user_id=UUID(current_user["id"]),
            days=days
        )

        logger.info(
            "weight_trend_calculated",
            user_id=current_user["id"],
            trend_direction=trend.get("trend_direction"),
            change_kg=trend.get("change_kg")
        )

        return WeightTrend(**trend)

    except Exception as e:
        logger.error(
            "calculate_weight_trend_error",
            user_id=current_user["id"],
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate weight trend"
        )


@router.get(
    "/body-metrics/{metric_id}",
    response_model=BodyMetric,
    status_code=status.HTTP_200_OK,
    summary="Get body metric by ID",
    description="Retrieve a single body metric with full details"
)
async def get_body_metric(
    metric_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a single body metric by ID.

    Verifies that the metric belongs to the authenticated user.
    """
    try:
        logger.info(
            "fetching_body_metric",
            metric_id=str(metric_id),
            user_id=current_user["id"]
        )

        metric = await body_metrics_service.get_body_metric(
            metric_id=metric_id,
            user_id=UUID(current_user["id"])
        )

        logger.info(
            "body_metric_fetched",
            metric_id=str(metric_id),
            user_id=current_user["id"]
        )

        return BodyMetric(**metric)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "fetch_body_metric_error",
            metric_id=str(metric_id),
            user_id=current_user["id"],
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch body metric"
        )


@router.post(
    "/body-metrics",
    response_model=BodyMetric,
    status_code=status.HTTP_201_CREATED,
    summary="Create new body metric",
    description="Log a new weight or body composition measurement"
)
async def create_body_metric(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new body metric entry.

    Required fields:
    - **recorded_at**: When the measurement was taken (ISO 8601)
    - **weight_kg**: Weight in kilograms (30-300 kg)

    Optional fields:
    - **body_fat_percentage**: Body fat percentage (3-60%)
    - **notes**: User notes about this measurement
    """
    try:
        # Defensive parsing to handle proxies sending bytes or wrong content-type
        try:
            payload = await request.json()
        except Exception:
            raw = await request.body()
            try:
                import json as _json
                decoded = raw.decode("utf-8", errors="replace")
                payload = _json.loads(decoded)
            except Exception as parse_err:
                logger.error(
                    "body_metrics_payload_parse_error",
                    user_id=current_user["id"],
                    error=str(parse_err),
                )
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid JSON body")

        # Validate
        try:
            req = CreateBodyMetricRequest.model_validate(payload)
        except Exception as ve:
            # Let global 422 handler format errors; also log summary here
            try:
                errors = ve.errors()  # type: ignore[attr-defined]
            except Exception:
                errors = str(ve)
            logger.error(
                "body_metrics_validation_error",
                user_id=current_user["id"],
                errors=errors,
            )
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=errors)

        logger.info(
            "creating_body_metric",
            user_id=current_user["id"],
            weight_kg=req.weight_kg,
        )

        metric = await body_metrics_service.create_body_metric(
            user_id=UUID(current_user["id"]),
            recorded_at=req.recorded_at,
            weight_kg=req.weight_kg,
            body_fat_percentage=req.body_fat_percentage,
            height_cm=getattr(req, 'height_cm', None),
            notes=req.notes,
        )

        logger.info(
            "body_metric_created",
            metric_id=metric["id"],
            user_id=current_user["id"]
        )

        return BodyMetric(**metric)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "create_body_metric_error",
            user_id=current_user["id"],
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create body metric"
        )


@router.patch(
    "/body-metrics/{metric_id}",
    response_model=BodyMetric,
    status_code=status.HTTP_200_OK,
    summary="Update body metric",
    description="Update an existing body metric"
)
async def update_body_metric(
    metric_id: UUID,
    request: UpdateBodyMetricRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update an existing body metric.

    All fields are optional - only provide the fields you want to update.

    Verifies that the metric belongs to the authenticated user.
    """
    try:
        # Build updates dict (exclude None values)
        updates = request.dict(exclude_unset=True)

        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )

        logger.info(
            "updating_body_metric",
            metric_id=str(metric_id),
            user_id=current_user["id"],
            fields=list(updates.keys())
        )

        metric = await body_metrics_service.update_body_metric(
            metric_id=metric_id,
            user_id=UUID(current_user["id"]),
            updates=updates
        )

        logger.info(
            "body_metric_updated",
            metric_id=str(metric_id),
            user_id=current_user["id"]
        )

        return BodyMetric(**metric)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "update_body_metric_error",
            metric_id=str(metric_id),
            user_id=current_user["id"],
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update body metric"
        )


@router.delete(
    "/body-metrics/{metric_id}",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete body metric",
    description="Delete a body metric entry"
)
async def delete_body_metric(
    metric_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a body metric.

    Verifies that the metric belongs to the authenticated user.
    """
    try:
        logger.info(
            "deleting_body_metric",
            metric_id=str(metric_id),
            user_id=current_user["id"]
        )

        success = await body_metrics_service.delete_body_metric(
            metric_id=metric_id,
            user_id=UUID(current_user["id"])
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete body metric"
            )

        logger.info(
            "body_metric_deleted",
            metric_id=str(metric_id),
            user_id=current_user["id"]
        )

        return SuccessResponse(
            success=True,
            message="Body metric deleted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "delete_body_metric_error",
            metric_id=str(metric_id),
            user_id=current_user["id"],
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete body metric"
        )
