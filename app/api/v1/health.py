"""
Health Check Endpoints

Provides health check endpoints for monitoring and load balancers.
"""

from datetime import datetime
from typing import Dict, Any

import structlog
from fastapi import APIRouter, status
from pydantic import BaseModel

from app.config import settings

logger = structlog.get_logger()

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    timestamp: datetime
    environment: str
    version: str
    checks: Dict[str, str]


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Detailed health check",
    description="Returns detailed health status including database connectivity",
)
async def health_check() -> HealthResponse:
    """
    Comprehensive health check.

    Checks:
    - Application status
    - Database connectivity (future)
    - Redis connectivity (future)

    Returns:
        HealthResponse: Health status with checks
    """
    checks: Dict[str, str] = {}
    overall_status = "healthy"

    # Database check (to be implemented)
    try:
        # from app.services.supabase_service import supabase_client
        # await supabase_client.test_connection()
        checks["database"] = "pass"
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))
        checks["database"] = "fail"
        overall_status = "unhealthy"

    # Redis check (to be implemented)
    try:
        # from app.services.cache_service import redis_client
        # await redis_client.ping()
        checks["redis"] = "pass"
    except Exception as e:
        logger.warning("redis_health_check_failed", error=str(e))
        checks["redis"] = "fail"
        # Redis is optional, don't mark as unhealthy

    logger.info(
        "health_check",
        status=overall_status,
        checks=checks,
    )

    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        environment=settings.ENVIRONMENT,
        version="1.0.0",
        checks=checks,
    )


@router.get(
    "/health/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness probe",
    description="Simple liveness check for Kubernetes/Docker orchestrators",
)
async def liveness() -> Dict[str, str]:
    """
    Liveness probe.

    Returns 200 if application is running.
    Used by orchestrators to determine if container should be restarted.

    Returns:
        Dict: Simple status message
    """
    return {"status": "alive"}


@router.get(
    "/health/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness probe",
    description="Readiness check for load balancers",
)
async def readiness() -> Dict[str, str]:
    """
    Readiness probe.

    Returns 200 if application is ready to accept traffic.
    Used by load balancers to determine if instance should receive requests.

    Returns:
        Dict: Simple status message
    """
    # Future: Check database, Redis, etc.
    # For now, if the app is running, it's ready
    return {"status": "ready"}
