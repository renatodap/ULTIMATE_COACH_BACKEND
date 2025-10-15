"""
Cache Service - Smart Caching for Performance

Uses in-memory dict cache (Redis-compatible interface).
For production, swap to Redis with same interface.

Caches:
- User profiles (5min TTL)
- Daily summaries (1min TTL)
- Food database (30min TTL)
- User language (5min TTL)
"""

import logging
from typing import Any, Optional
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)


class CacheService:
    """
    Simple in-memory cache with TTL support.

    For production: Replace with Redis using same interface.
    """

    def __init__(self):
        self._cache: dict[str, tuple[Any, datetime]] = {}
        self._lock = threading.Lock()
        logger.info("[Cache] ✅ Initialized (in-memory mode)")

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            if key not in self._cache:
                return None

            value, expires_at = self._cache[key]

            # Check expiration
            if datetime.utcnow() > expires_at:
                # Expired - remove from cache
                del self._cache[key]
                logger.debug(f"[Cache] ❌ Expired: {key}")
                return None

            logger.debug(f"[Cache] ✅ Hit: {key}")
            return value

    def set(
        self,
        key: str,
        value: Any,
        ttl: int = 300  # 5 minutes default
    ) -> bool:
        """
        Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds

        Returns:
            True if successful
        """
        with self._lock:
            expires_at = datetime.utcnow() + timedelta(seconds=ttl)
            self._cache[key] = (value, expires_at)
            logger.debug(f"[Cache] 💾 Set: {key} (TTL: {ttl}s)")
            return True

    def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key

        Returns:
            True if key existed
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"[Cache] 🗑️ Deleted: {key}")
                return True
            return False

    def clear(self) -> int:
        """
        Clear all cache entries.

        Returns:
            Number of entries cleared
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"[Cache] 🧹 Cleared {count} entries")
            return count

    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.

        Returns:
            Number of entries removed
        """
        with self._lock:
            now = datetime.utcnow()
            expired_keys = [
                key for key, (_, expires_at) in self._cache.items()
                if now > expires_at
            ]

            for key in expired_keys:
                del self._cache[key]

            if expired_keys:
                logger.info(f"[Cache] 🧹 Cleaned up {len(expired_keys)} expired entries")

            return len(expired_keys)

    def stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with cache stats
        """
        with self._lock:
            now = datetime.utcnow()
            expired_count = sum(
                1 for _, expires_at in self._cache.values()
                if now > expires_at
            )

            return {
                "total_entries": len(self._cache),
                "expired_entries": expired_count,
                "active_entries": len(self._cache) - expired_count
            }


# Singleton
_cache_service: Optional[CacheService] = None

def get_cache_service() -> CacheService:
    """Get singleton CacheService instance."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
