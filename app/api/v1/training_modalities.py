"""
Training Modalities API endpoints.

Provides access to the master list of training modalities for onboarding.
"""

import structlog
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from typing import List, Dict, Any

from app.services.supabase_service import supabase_service

logger = structlog.get_logger()

router = APIRouter()


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Get all training modalities",
    description="Get the complete list of available training modalities",
)
async def get_training_modalities() -> JSONResponse:
    """
    Get all training modalities.

    Returns the master list of training modalities available for selection
    during onboarding. This is a public endpoint (no authentication required)
    as the data is used in the onboarding flow.

    Returns:
        List of training modalities with metadata
    """
    try:
        # Fetch from training_modalities table
        # Order by display_order for consistent UI presentation
        result = supabase_service.client.table('training_modalities') \
            .select('id, name, description, typical_frequency_per_week, equipment_required, icon, display_order') \
            .order('display_order') \
            .execute()

        if not result.data:
            logger.warning("no_training_modalities_found")
            return JSONResponse(content=[])

        logger.info(
            "training_modalities_fetched",
            count=len(result.data)
        )

        return JSONResponse(content=result.data)

    except Exception as e:
        logger.error(
            "training_modalities_fetch_error",
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch training modalities"
        )
