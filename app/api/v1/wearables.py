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
    description="Starts a sync job (synchronous MVP) for the configured provider",
)
async def trigger_wearable_sync(
    provider: str,
    days: int = Query(7, ge=1, le=365, description="Days to backfill"),
    current_user: dict = Depends(get_current_user),
):
    try:
        job = await wearable_sync_service.start_sync(UUID(current_user["id"]), provider, days=days)
        return {"job": job}
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

