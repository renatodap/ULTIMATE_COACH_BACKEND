"""
Wearables base interfaces and registry.

Defines provider-agnostic interfaces for wearable integrations
and a registry to manage multiple providers (garmin, strava, etc.).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID


class WearableProvider(ABC):
    """Abstract wearable provider interface."""

    name: str

    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Authenticate and persist provider session in-memory (or cache).

        Args:
            credentials: Provider-specific credentials payload

        Returns:
            (success, error_message)
        """

    @abstractmethod
    async def sync_range(
        self,
        user_id: UUID,
        start: date,
        end: date,
        metrics: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Sync data for a date range.

        Returns stats dict: { 'activities': n, 'metrics': {..} }
        """


class WearableRegistry:
    """Simple registry for wearable providers."""

    def __init__(self) -> None:
        self._providers: Dict[str, WearableProvider] = {}

    def register(self, provider: WearableProvider) -> None:
        self._providers[provider.name] = provider

    def get(self, name: str) -> Optional[WearableProvider]:
        return self._providers.get(name)

    def list(self) -> List[str]:
        return list(self._providers.keys())


# Global registry instance
wearable_registry = WearableRegistry()

