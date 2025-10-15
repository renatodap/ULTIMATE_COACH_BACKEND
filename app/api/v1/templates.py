"""
Activity Templates API endpoints.

Handles template CRUD operations, template creation from activities, and usage statistics.
"""

import structlog
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional
from uuid import UUID

from app.models.activity_templates import (
    CreateTemplateRequest,
    UpdateTemplateRequest,
    ActivityTemplate,
    TemplateStats,
    TemplateListResponse,
    CreateTemplateFromActivityRequest,
    SuccessResponse
)
from app.services.template_service import template_service
from app.services.template_matching_service import template_matching_service
from app.api.dependencies import get_current_user

logger = structlog.get_logger()

router = APIRouter()


@router.get(
    "/templates",
    response_model=TemplateListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user's activity templates",
    description="Retrieve templates for authenticated user with optional filtering"
)
async def get_templates(
    activity_type: Optional[str] = Query(None, description="Filter by activity type"),
    is_active: bool = Query(True, description="Show only active templates"),
    limit: int = Query(50, ge=1, le=100, description="Max templates to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get activity templates for the authenticated user.

    - **activity_type**: Filter by specific activity type (optional)
    - **is_active**: Show only active templates (default: true)
    - **limit**: Maximum number of templates to return (1-100)
    - **offset**: Number of templates to skip (for pagination)

    Returns templates sorted by use_count descending, then last_used_at descending.
    """
    try:
        logger.info(
            "fetching_templates",
            user_id=current_user["id"],
            activity_type=activity_type,
            is_active=is_active,
            limit=limit,
            offset=offset
        )

        templates, total = await template_service.list_templates(
            user_id=UUID(current_user["id"]),
            activity_type=activity_type,
            is_active=is_active,
            limit=limit,
            offset=offset
        )

        logger.info(
            "templates_fetched",
            user_id=current_user["id"],
            count=len(templates),
            total=total
        )

        return TemplateListResponse(
            templates=[ActivityTemplate(**template) for template in templates],
            total=total,
            limit=limit,
            offset=offset
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "fetch_templates_error",
            user_id=current_user["id"],
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch templates"
        )


@router.get(
    "/templates/{template_id}",
    response_model=ActivityTemplate,
    status_code=status.HTTP_200_OK,
    summary="Get template by ID",
    description="Retrieve a single template with full details"
)
async def get_template(
    template_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a single activity template by ID.

    Verifies that the template belongs to the authenticated user.
    """
    try:
        logger.info(
            "fetching_template",
            template_id=str(template_id),
            user_id=current_user["id"]
        )

        template = await template_service.get_template(
            template_id=template_id,
            user_id=UUID(current_user["id"])
        )

        logger.info(
            "template_fetched",
            template_id=str(template_id),
            user_id=current_user["id"]
        )

        return ActivityTemplate(**template)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "fetch_template_error",
            template_id=str(template_id),
            user_id=current_user["id"],
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch template"
        )


@router.post(
    "/templates",
    response_model=ActivityTemplate,
    status_code=status.HTTP_201_CREATED,
    summary="Create new activity template",
    description="Create a new template for recurring workouts"
)
async def create_template(
    request: CreateTemplateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new activity template.

    Required fields:
    - **template_name**: Name for the template (e.g., 'Morning 5K Route')
    - **activity_type**: Type of activity (running, cycling, strength_training, etc.)

    Optional fields:
    - **description**: Template description/notes
    - **icon**: Emoji icon (default: auto-assigned based on activity_type)
    - **expected_distance_m**: Expected distance in meters
    - **distance_tolerance_percent**: Distance matching tolerance (±%, default: 10)
    - **expected_duration_minutes**: Expected duration in minutes
    - **duration_tolerance_percent**: Duration matching tolerance (±%, default: 15)
    - **default_exercises**: Pre-filled exercises for strength training
    - **default_metrics**: Pre-filled metrics (distance, HR, etc.)
    - **default_notes**: Pre-filled notes
    - **auto_match_enabled**: Enable auto-matching (default: true)
    - **min_match_score**: Minimum confidence score to auto-suggest (0-100, default: 70)
    - **require_gps_match**: Require GPS route match (default: false)
    - **typical_start_time**: Typical start time for this activity
    - **time_window_hours**: Time window for matching (±hours, default: 2)
    - **preferred_days**: Preferred days of week (1=Monday, 7=Sunday)
    - **target_zone**: Target HR zone or effort level
    - **goal_notes**: Workout goal/purpose
    - **created_from_activity_id**: Activity ID this template was created from
    """
    try:
        logger.info(
            "creating_template",
            user_id=current_user["id"],
            template_name=request.template_name,
            activity_type=request.activity_type
        )

        template = await template_service.create_template(
            user_id=UUID(current_user["id"]),
            template_data=request.dict()
        )

        logger.info(
            "template_created",
            template_id=template["id"],
            user_id=current_user["id"]
        )

        return ActivityTemplate(**template)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "create_template_error",
            user_id=current_user["id"],
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create template"
        )


@router.post(
    "/templates/from-activity/{activity_id}",
    response_model=ActivityTemplate,
    status_code=status.HTTP_201_CREATED,
    summary="Create template from existing activity",
    description="Create a template using data from an existing activity"
)
async def create_template_from_activity(
    activity_id: UUID,
    request: CreateTemplateFromActivityRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a template from an existing activity.

    This will auto-populate template fields from the activity:
    - activity_type from activity
    - expected_distance_m from activity metrics
    - expected_duration_minutes from activity
    - default_exercises from activity (if strength training)
    - default_metrics from activity
    - typical_start_time from activity start time

    Required fields:
    - **template_name**: Name for the new template

    Optional fields:
    - **auto_match_enabled**: Enable auto-matching (default: true)
    - **require_gps_match**: Require GPS route match (default: false)

    Verifies that the activity belongs to the authenticated user.
    """
    try:
        logger.info(
            "creating_template_from_activity",
            user_id=current_user["id"],
            activity_id=str(activity_id),
            template_name=request.template_name
        )

        template = await template_service.create_from_activity(
            user_id=UUID(current_user["id"]),
            activity_id=activity_id,
            template_name=request.template_name,
            auto_match_enabled=request.auto_match_enabled,
            require_gps_match=request.require_gps_match
        )

        logger.info(
            "template_created_from_activity",
            template_id=template["id"],
            activity_id=str(activity_id),
            user_id=current_user["id"]
        )

        return ActivityTemplate(**template)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "create_template_from_activity_error",
            activity_id=str(activity_id),
            user_id=current_user["id"],
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create template from activity"
        )


@router.patch(
    "/templates/{template_id}",
    response_model=ActivityTemplate,
    status_code=status.HTTP_200_OK,
    summary="Update template",
    description="Update an existing template"
)
async def update_template(
    template_id: UUID,
    request: UpdateTemplateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update an existing activity template.

    All fields are optional - only provide the fields you want to update.

    Verifies that the template belongs to the authenticated user.
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
            "updating_template",
            template_id=str(template_id),
            user_id=current_user["id"],
            fields=list(updates.keys())
        )

        template = await template_service.update_template(
            template_id=template_id,
            user_id=UUID(current_user["id"]),
            updates=updates
        )

        logger.info(
            "template_updated",
            template_id=str(template_id),
            user_id=current_user["id"]
        )

        return ActivityTemplate(**template)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "update_template_error",
            template_id=str(template_id),
            user_id=current_user["id"],
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update template"
        )


@router.delete(
    "/templates/{template_id}",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete template",
    description="Delete a template (soft delete)"
)
async def delete_template(
    template_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete an activity template (soft delete).

    The template is marked as inactive but not removed from the database.
    Verifies that the template belongs to the authenticated user.
    """
    try:
        logger.info(
            "deleting_template",
            template_id=str(template_id),
            user_id=current_user["id"]
        )

        success = await template_service.delete_template(
            template_id=template_id,
            user_id=UUID(current_user["id"])
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete template"
            )

        logger.info(
            "template_deleted",
            template_id=str(template_id),
            user_id=current_user["id"]
        )

        return SuccessResponse(
            success=True,
            message="Template deleted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "delete_template_error",
            template_id=str(template_id),
            user_id=current_user["id"],
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete template"
        )


@router.get(
    "/templates/{template_id}/stats",
    response_model=TemplateStats,
    status_code=status.HTTP_200_OK,
    summary="Get template usage statistics",
    description="Get detailed usage analytics for a template"
)
async def get_template_stats(
    template_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Get usage statistics and analytics for an activity template.

    Returns:
    - **total_uses**: Total times this template was used
    - **avg_duration_minutes**: Average activity duration
    - **avg_distance_m**: Average distance (if applicable)
    - **avg_calories**: Average calories burned
    - **trend_pace_percent**: Pace trend (negative = getting faster)
    - **trend_consistency_score**: Consistency score 0-100 (how often user does this)
    - **best_activity_id**: Activity ID with best performance
    - **best_performance_date**: Date of best performance
    - **best_performance_metric**: What made it best (e.g., 'Fastest pace: 5:45/km')
    - **first_used**: First time template was used
    - **last_used**: Last time template was used
    - **days_since_last_use**: Days since last use

    Verifies that the template belongs to the authenticated user.
    """
    try:
        logger.info(
            "fetching_template_stats",
            template_id=str(template_id),
            user_id=current_user["id"]
        )

        stats = await template_service.get_template_stats(
            template_id=template_id,
            user_id=UUID(current_user["id"])
        )

        logger.info(
            "template_stats_fetched",
            template_id=str(template_id),
            user_id=current_user["id"],
            total_uses=stats["total_uses"]
        )

        return TemplateStats(**stats)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "fetch_template_stats_error",
            template_id=str(template_id),
            user_id=current_user["id"],
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch template stats"
        )


@router.get(
    "/templates/{template_id}/activities",
    response_model=list[dict],
    status_code=status.HTTP_200_OK,
    summary="Get activities using template",
    description="Get all activities that used this template"
)
async def get_template_activities(
    template_id: UUID,
    limit: int = Query(20, ge=1, le=100, description="Max activities to return"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all activities that used this template.

    - **limit**: Maximum number of activities to return (1-100)

    Returns activities sorted by start_time descending (most recent first).
    Verifies that the template belongs to the authenticated user.
    """
    try:
        logger.info(
            "fetching_template_activities",
            template_id=str(template_id),
            user_id=current_user["id"],
            limit=limit
        )

        activities = await template_service.get_template_activities(
            template_id=template_id,
            user_id=UUID(current_user["id"]),
            limit=limit
        )

        logger.info(
            "template_activities_fetched",
            template_id=str(template_id),
            user_id=current_user["id"],
            count=len(activities)
        )

        return activities

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "fetch_template_activities_error",
            template_id=str(template_id),
            user_id=current_user["id"],
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch template activities"
        )


# ===== TEMPLATE MATCHING ENDPOINTS =====


@router.post(
    "/templates/match",
    status_code=status.HTTP_200_OK,
    summary="Get template match suggestions",
    description="Find matching templates for activity data"
)
async def get_template_matches(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Get template match suggestions for activity data.

    Request body should contain activity data:
    - **activity_type**: Activity type (required)
    - **distance_km**: Distance in kilometers (optional)
    - **duration_minutes**: Duration in minutes (optional)
    - **start_time**: Start time ISO 8601 (optional)

    Returns grouped match suggestions:
    - **excellent**: Matches with 90-100 score
    - **good**: Matches with 70-89 score
    - **fair**: Matches with 50-69 score

    Each match includes:
    - template_id, template_name, match_score
    - breakdown of score components
    - full template data
    """
    try:
        logger.info(
            "getting_template_matches",
            user_id=current_user["id"],
            activity_type=request.get("activity_type")
        )

        # Get match suggestions
        suggestions = await template_matching_service.get_match_suggestions(
            user_id=UUID(current_user["id"]),
            activity_data=request
        )

        logger.info(
            "template_matches_found",
            user_id=current_user["id"],
            excellent_count=len(suggestions.excellent),
            good_count=len(suggestions.good),
            fair_count=len(suggestions.fair)
        )

        return suggestions.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "get_template_matches_error",
            user_id=current_user["id"],
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to find template matches"
        )


@router.post(
    "/templates/{template_id}/apply/{activity_id}",
    status_code=status.HTTP_200_OK,
    summary="Apply template to activity",
    description="Apply a template to an existing activity"
)
async def apply_template_to_activity(
    template_id: UUID,
    activity_id: UUID,
    match_score: Optional[int] = Query(None, description="Match score (if auto-matched)"),
    match_method: str = Query("manual", description="Match method: manual or auto"),
    current_user: dict = Depends(get_current_user)
):
    """
    Apply a template to an activity.

    This will:
    - Update activity with template_id, template_match_score, template_applied_at
    - Copy default_metrics if activity metrics is empty
    - Copy default_notes if activity notes is empty
    - Increment template use_count and update last_used_at
    - Record match decision in activity_template_matches table

    Args:
    - **template_id**: Template to apply
    - **activity_id**: Activity to update
    - **match_score**: Match score (optional, for auto-matches)
    - **match_method**: 'manual' or 'auto'

    Returns updated activity data.
    """
    try:
        logger.info(
            "applying_template_to_activity",
            user_id=current_user["id"],
            template_id=str(template_id),
            activity_id=str(activity_id),
            match_method=match_method
        )

        # Apply template
        updated_activity = await template_matching_service.apply_template_to_activity(
            user_id=UUID(current_user["id"]),
            template_id=template_id,
            activity_id=activity_id,
            match_score=match_score,
            match_method=match_method
        )

        logger.info(
            "template_applied_to_activity",
            user_id=current_user["id"],
            template_id=str(template_id),
            activity_id=str(activity_id)
        )

        return updated_activity

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "apply_template_error",
            user_id=current_user["id"],
            template_id=str(template_id),
            activity_id=str(activity_id),
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to apply template to activity"
        )


@router.post(
    "/templates/match/decision",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Record match decision",
    description="Record user's decision on a template match suggestion"
)
async def record_match_decision(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Record a match decision for analytics.

    Request body:
    - **activity_id**: Activity ID (required)
    - **template_id**: Template ID (required)
    - **match_score**: Match score (required)
    - **match_method**: 'manual' or 'auto' (required)
    - **user_decision**: 'accepted', 'rejected', or 'ignored' (required)

    Use cases:
    - User dismisses a suggestion: decision='rejected'
    - User ignores a suggestion: decision='ignored'
    - User applies template: decision='accepted' (auto-recorded by apply endpoint)

    This data is used to improve matching algorithm over time.
    """
    try:
        # Validate required fields
        required_fields = ["activity_id", "template_id", "match_score", "match_method", "user_decision"]
        for field in required_fields:
            if field not in request:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )

        logger.info(
            "recording_match_decision",
            user_id=current_user["id"],
            activity_id=request["activity_id"],
            template_id=request["template_id"],
            decision=request["user_decision"]
        )

        # Record decision
        await template_matching_service.record_match_decision(
            user_id=UUID(current_user["id"]),
            activity_id=UUID(request["activity_id"]),
            template_id=UUID(request["template_id"]),
            match_score=request["match_score"],
            match_method=request["match_method"],
            user_decision=request["user_decision"]
        )

        logger.info(
            "match_decision_recorded",
            user_id=current_user["id"],
            activity_id=request["activity_id"],
            template_id=request["template_id"],
            decision=request["user_decision"]
        )

        return SuccessResponse(
            success=True,
            message="Match decision recorded successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "record_match_decision_error",
            user_id=current_user["id"],
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record match decision"
        )
