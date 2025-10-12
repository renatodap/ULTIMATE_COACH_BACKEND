"""
Database module for direct PostgreSQL access.

Provides async connection pooling via asyncpg for complex queries,
transactions, and operations that go beyond Supabase client capabilities.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import asyncpg
from app.config import settings

logger = logging.getLogger(__name__)

# Global connection pool
_pool: asyncpg.Pool = None


async def init_db_pool() -> None:
    """
    Initialize the database connection pool.

    Should be called on application startup.
    """
    global _pool

    if _pool is not None:
        logger.warning("Database pool already initialized")
        return

    try:
        # Get DATABASE_URL, or construct from SUPABASE_URL
        database_url = settings.DATABASE_URL

        if not database_url:
            # Construct from Supabase URL
            # Supabase format: https://[PROJECT_REF].supabase.co
            # Database format: postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:5432/postgres
            logger.warning(
                "DATABASE_URL not set. Using Supabase client instead. "
                "For nutrition features, set DATABASE_URL in environment."
            )
            # For now, we'll skip pool initialization and rely on Supabase client
            return

        logger.info("Initializing database connection pool")
        _pool = await asyncpg.create_pool(
            database_url,
            min_size=5,
            max_size=20,
            command_timeout=60,
        )
        logger.info("Database pool initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize database pool: {e}")
        raise


async def close_db_pool() -> None:
    """
    Close the database connection pool.

    Should be called on application shutdown.
    """
    global _pool

    if _pool is None:
        return

    try:
        logger.info("Closing database connection pool")
        await _pool.close()
        _pool = None
        logger.info("Database pool closed successfully")
    except Exception as e:
        logger.error(f"Failed to close database pool: {e}")


@asynccontextmanager
async def get_db() -> AsyncGenerator[asyncpg.Connection, None]:
    """
    Get a database connection from the pool.

    Usage:
        async with get_db() as conn:
            result = await conn.fetchval("SELECT 1")
    """
    global _pool

    if _pool is None:
        raise RuntimeError(
            "Database pool not initialized. "
            "Call init_db_pool() on application startup."
        )

    async with _pool.acquire() as connection:
        yield connection


async def health_check() -> bool:
    """
    Check database connectivity.

    Returns:
        True if database is accessible
    """
    try:
        async with get_db() as conn:
            result = await conn.fetchval("SELECT 1")
            return result == 1
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
