"""
Wearables API endpoints.

Connect wearable accounts and trigger sync jobs.
"""

from __future__ import annotations

from typing import Optional, Dict, Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field

from app.api.dependencies import get_current_user
from app.services.wearables.wearable_sync_service import wearable_sync_service
from app.core.celery_app import celery_app
from app.config import settings

logger = structlog.get_logger()

router = APIRouter()


class ConnectRequest(BaseModel):
    provider: str = Field(..., description="Provider key: garmin, strava, apple_health, fitbit, oura, polar")
    credentials: Dict[str, Any] = Field(default_factory=dict, description="Provider credentials payload")


@router.post(
    "/wearables/{provider}/connect",
    status_code=status.HTTP_200_OK,
    summary="Connect wearable account",
    description="Store encrypted credentials and mark provider as connected for the user",
)
async def connect_wearable_account(
    provider: str,
    body: ConnectRequest,
    current_user: dict = Depends(get_current_user),
):
    if provider != body.provider:
        raise HTTPException(status_code=400, detail="Provider mismatch")

    try:
        result = await wearable_sync_service.connect_account(UUID(current_user["id"]), provider, body.credentials)
        return {"status": "ok", "account": result}
    except Exception as e:
        logger.error("connect_wearable_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to connect wearable account")


@router.post(
    "/wearables/{provider}/sync",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger wearable sync",
    description="Enqueue a background sync job for the configured provider",
)
async def trigger_wearable_sync(
    provider: str,
    days: int = Query(7, ge=1, le=365, description="Days to backfill"),
    current_user: dict = Depends(get_current_user),
):
    try:
        # Enqueue background job by task name to avoid importing worker module in API process
        result = celery_app.send_task(
            "wearables.start_sync",
            args=[current_user["id"], provider, days],
        )
        return {"enqueued": True, "task_id": result.id}
    except Exception as e:
        logger.error("trigger_sync_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to trigger sync")


@router.get(
    "/wearables/status",
    status_code=status.HTTP_200_OK,
    summary="Get wearable connection status",
)
async def get_wearable_status(current_user: dict = Depends(get_current_user)):
    try:
        status_data = await wearable_sync_service.get_status(UUID(current_user["id"]))
        return status_data
    except Exception as e:
        logger.error("get_status_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get status")


@router.post(
    "/wearables/{provider}/sync-inline",
    status_code=status.HTTP_200_OK,
    summary="Trigger wearable sync inline (dev)",
    description="Runs sync synchronously for development/testing without Celery",
)
async def trigger_wearable_sync_inline(
    provider: str,
    days: int = Query(7, ge=1, le=365, description="Days to backfill"),
    current_user: dict = Depends(get_current_user),
):
    # Restrict to development or explicit flag
    if not (settings.is_development or settings.WEARABLES_INLINE_SYNC_ENABLED):
        raise HTTPException(status_code=403, detail="Inline sync disabled")

    try:
        result = await wearable_sync_service.start_sync(UUID(current_user["id"]), provider, days=days)
        return {"job": result, "mode": "inline"}
    except Exception as e:
        logger.error("trigger_sync_inline_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to run sync inline")
