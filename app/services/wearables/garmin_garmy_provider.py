"""
Garmin provider via Garmy.

Feature-flagged; acts as a stub if Garmy is unavailable or disabled.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import structlog

from app.config import settings
from app.services.wearables.base import WearableProvider

logger = structlog.get_logger()


class GarminGarmyProvider(WearableProvider):
    name = "garmin"

    def __init__(self) -> None:
        self._enabled = settings.GARMIN_ENABLED
        self._available = False
        self._client = None
        if self._enabled:
            try:
                from garmy import AuthClient, APIClient  # type: ignore

                self._AuthClient = AuthClient
                self._APIClient = APIClient
                self._available = True
            except Exception as e:  # ImportError or others
                logger.warning("garmy_import_failed", error=str(e))
                self._available = False

    async def authenticate(self, credentials: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        if not self._enabled:
            return False, "Garmin provider disabled"
        if not self._available:
            return False, "Garmy library not available"

        try:
            email = credentials.get("email")
            password = credentials.get("password")
            if not email or not password:
                return False, "Missing email/password"

            auth_client = self._AuthClient()
            api_client = self._APIClient(auth_client=auth_client)
            auth_client.login(email, password)
            self._client = api_client
            return True, None
        except Exception as e:
            logger.error("garmin_auth_failed", error=str(e))
            return False, str(e)

    async def sync_range(
        self, user_id: UUID, start: date, end: date, metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        # Minimal stub: in a follow-up, map activities and metrics and persist
        if not (self._enabled and self._available and self._client):
            logger.info("garmin_sync_skipped", enabled=self._enabled, available=self._available)
            return {"activities": 0, "metrics": {}}

        # TODO: Implement actual calls to self._client.metrics and insert via SupabaseService
        logger.info("garmin_sync_range", user_id=str(user_id), start=str(start), end=str(end))
        return {"activities": 0, "metrics": {}}


provider = GarminGarmyProvider()
