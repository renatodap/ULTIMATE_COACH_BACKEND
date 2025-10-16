"""
ULTIMATE COACH Backend - FastAPI Application

Main application entry point with CORS, middleware, and routing configuration.
"""

import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi import HTTPException as FastAPIHTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# Get logger
logger = structlog.get_logger()

# Configure Python logging
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=getattr(logging, settings.LOG_LEVEL.upper()),
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI lifespan context manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info(
        "application_startup",
        environment=settings.ENVIRONMENT,
        debug=settings.DEBUG,
        log_level=settings.LOG_LEVEL,
    )

    # Validate Anthropic SDK installation
    from app.utils.sdk_validator import validate_anthropic_sdk

    sdk_error = validate_anthropic_sdk()
    if sdk_error:
        logger.error(
            "anthropic_sdk_validation_failed",
            error=sdk_error,
            environment=settings.ENVIRONMENT
        )
        logger.warning(
            "anthropic_features_degraded",
            message="AI Coach features may be unavailable or use fallback behavior"
        )
    else:
        logger.info("anthropic_sdk_validated", message="All AI features operational")

    # Initialize Sentry if configured (only in production)
    if settings.SENTRY_DSN and not settings.is_development:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            from sentry_sdk.integrations.starlette import StarletteIntegration

            sentry_sdk.init(
                dsn=settings.SENTRY_DSN,
                environment=settings.ENVIRONMENT,
                traces_sample_rate=0.1,

                # Enable FastAPI and Starlette integrations
                integrations=[
                    FastApiIntegration(transaction_style="url"),
                    StarletteIntegration(transaction_style="url"),
                ],

                # Send user data (IP, headers) for better debugging
                # See: https://docs.sentry.io/platforms/python/data-management/data-collected/
                send_default_pii=True,

                # Tag all events
                before_send=lambda event, hint: {
                    **event,
                    "tags": {**(event.get("tags") or {}), "app": "sharpened-backend"},
                },
            )
            logger.info("sentry_initialized", environment=settings.ENVIRONMENT)
        except Exception as e:
            logger.warning("sentry_initialization_failed", error=str(e))
            # Continue without Sentry - don't break the app

    # Start background jobs (daily adjustments, reassessments, etc.)
    # TODO: Re-enable when background_jobs module is committed
    # Only in production or if explicitly enabled
    # if not settings.is_development or settings.ENABLE_BACKGROUND_JOBS:
    #     try:
    #         from app.services.background_jobs import background_jobs_service
    #
    #         background_jobs_service.start()
    #         logger.info("background_jobs_started")
    #     except Exception as e:
    #         logger.error("background_jobs_startup_failed", error=str(e), exc_info=True)
    #         # Continue without background jobs - don't break the app
    # else:
    #     logger.info("background_jobs_disabled", reason="development mode")
    logger.info("background_jobs_disabled", reason="module not yet committed")

    yield

    # Shutdown
    logger.info("application_shutdown")

    # Shutdown background jobs
    # TODO: Re-enable when background_jobs module is committed
    # try:
    #     from app.services.background_jobs import background_jobs_service
    #     background_jobs_service.shutdown()
    #     logger.info("background_jobs_stopped")
    # except Exception as e:
    #     logger.warning("background_jobs_shutdown_failed", error=str(e))


# Create FastAPI app
app = FastAPI(
    title="ULTIMATE COACH API",
    description="AI-powered fitness and nutrition coaching platform",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# CORS middleware
# Log CORS configuration for debugging
logger.info(
    "cors_configuration",
    allow_all_origins=settings.ALLOW_ALL_ORIGINS,
    cors_origins=settings.cors_origins_list,
    environment=settings.ENVIRONMENT,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Add request logging middleware for debugging coach endpoint
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response
import json

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):
        # Only log coach endpoints for debugging
        if "/coach/message" in request.url.path and request.method == "POST":
            logger.info(
                "coach_request_headers",
                method=request.method,
                path=request.url.path,
                content_type=request.headers.get("content-type"),
                content_length=request.headers.get("content-length"),
                has_auth=bool(request.headers.get("authorization")),
                origin=request.headers.get("origin"),
                user_agent=request.headers.get("user-agent", "")[:100]
            )

        response = await call_next(request)
        return response

app.add_middleware(RequestLoggingMiddleware)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(
        "unhandled_exception",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
        method=request.method,
        exc_info=True,
    )

    # Get origin from request for CORS headers
    origin = request.headers.get("origin", "http://localhost:3000")

    # Add CORS headers to error response
    headers = {
        "Access-Control-Allow-Origin": origin if origin in settings.cors_origins_list else settings.cors_origins_list[0],
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Headers": "*",
    }

    if settings.is_development:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": str(exc),
                "type": type(exc).__name__,
            },
            headers=headers,
        )

    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error"},
        headers=headers,
    )


# Sanitize HTTPException details to ensure JSON serializable responses
@app.exception_handler(FastAPIHTTPException)
async def http_exception_handler(request, exc: FastAPIHTTPException):
    # Convert non-serializable details (e.g., ValueError, bytes) into safe JSON
    detail = exc.detail
    if isinstance(detail, (bytes, bytearray)):
        try:
            detail = detail.decode("utf-8", errors="replace")
        except Exception:
            detail = str(detail)
    elif not isinstance(detail, (str, dict, list, type(None))):
        # Any other object: coerce to string
        detail = str(detail)

    logger.error(
        "http_exception",
        status_code=exc.status_code,
        path=request.url.path,
        method=request.method,
        detail=detail,
    )

    origin = request.headers.get("origin", "http://localhost:3000")
    headers = {
        "Access-Control-Allow-Origin": origin if origin in settings.cors_origins_list else settings.cors_origins_list[0],
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Headers": "*",
    }

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": detail},
        headers=headers,
    )

# 422 validation errors (e.g., request body invalid)
@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(request, exc: RequestValidationError):
    # Sanitize errors for JSON serialization (bytes -> decoded string, truncated)
    raw_errors = exc.errors()
    sanitized_errors = []
    for err in raw_errors:
        e = dict(err)
        val = e.get("input")
        if isinstance(val, (bytes, bytearray)):
            try:
                decoded = val.decode("utf-8", errors="replace")
            except Exception:
                decoded = str(val)
            # Truncate to avoid log bloat
            if len(decoded) > 500:
                decoded = decoded[:500] + "…"
            e["input"] = decoded
        sanitized_errors.append(e)

    logger.error(
        "request_validation_error",
        path=str(request.url.path),
        method=request.method,
        content_type=request.headers.get("content-type"),
        content_length=request.headers.get("content-length"),
        authorization_present=bool(request.headers.get("authorization")),
        errors=sanitized_errors,
        error_details=[{"loc": e.get("loc"), "msg": e.get("msg"), "type": e.get("type")} for e in sanitized_errors]
    )

    origin = request.headers.get("origin", "http://localhost:3000")
    headers = {
        "Access-Control-Allow-Origin": origin if origin in settings.cors_origins_list else settings.cors_origins_list[0],
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Headers": "*",
    }

    return JSONResponse(
        status_code=422,
        content={"detail": sanitized_errors},
        headers=headers,
    )

# Nutrition-specific error handler
from app.models.errors import NutritionError


@app.exception_handler(NutritionError)
async def nutrition_error_handler(request, exc: NutritionError):
    """
    Handler for nutrition-related errors with i18n error codes.

    Returns structured error response with:
    - error: Error code for frontend translation (e.g., "NUTRITION_101")
    - message: English message for debugging
    - details: Additional context (food_id, serving_id, etc.)
    """
    logger.warning(
        "nutrition_error",
        error_code=exc.code,
        message=exc.message,
        details=exc.details,
        path=request.url.path,
        method=request.method,
    )

    # Get origin from request for CORS headers
    origin = request.headers.get("origin", "http://localhost:3000")

    # Add CORS headers to error response
    headers = {
        "Access-Control-Allow-Origin": origin if origin in settings.cors_origins_list else settings.cors_origins_list[0],
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Headers": "*",
    }

    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
        headers=headers,
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "name": "ULTIMATE COACH API",
        "version": "1.0.0",
        "status": "operational",
        "environment": settings.ENVIRONMENT,
        "docs": "/docs" if settings.DEBUG else None,
    }


# Import and include routers
from app.api.v1 import health, auth, users, onboarding, foods, meals, activities, quick_meals, templates, body_metrics, dashboard, exercise_sets, coach, wearables, planning  # consultation disabled for MVP
from app.api.v1.planlogs import router as planlogs_router

app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(onboarding.router, prefix="/api/v1/onboarding", tags=["Onboarding"])

# ========================================================================
# CONSULTATION AI - DISABLED FOR MVP
# ========================================================================
# The Consultation AI is a premium onboarding feature with 15 tools for
# structured data collection (training modalities, exercises, meal timing,
# goals, challenges, etc.). It's currently disabled because:
#   - Frontend UI is incomplete (placeholder only)
#   - Premium feature (requires consultation keys)
#   - Not part of core MVP (activities + nutrition tracking)
#   - Reduces tool complexity from 27 → 12 tools (56% reduction)
#
# To re-enable:
#   1. Uncomment the import above (consultation)
#   2. Uncomment the router include below
#   3. Complete frontend UI at /dashboard/consultation
#   4. Test consultation key redemption flow
#
# app.include_router(consultation.router, prefix="/api/v1", tags=["Consultation"])
# ========================================================================
app.include_router(dashboard.router, prefix="/api/v1", tags=["Dashboard"])
app.include_router(foods.router, prefix="/api/v1", tags=["Nutrition - Foods"])
app.include_router(meals.router, prefix="/api/v1", tags=["Nutrition - Meals"])
app.include_router(quick_meals.router, prefix="/api/v1", tags=["Nutrition - Quick Meals"])
app.include_router(activities.router, prefix="/api/v1", tags=["Activities"])
app.include_router(templates.router, prefix="/api/v1", tags=["Activity Templates"])
app.include_router(body_metrics.router, prefix="/api/v1", tags=["Body Metrics"])
app.include_router(exercise_sets.router, prefix="/api/v1", tags=["Exercise Sets"])
app.include_router(coach.router, prefix="/api/v1", tags=["AI Coach"])
app.include_router(wearables.router, prefix="/api/v1", tags=["Wearables"])
app.include_router(planning.router, prefix="/api/v1", tags=["Planning & Adaptive"])
app.include_router(planlogs_router, prefix="/api/v1/planlogs", tags=["Plan Logs"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_level=settings.LOG_LEVEL.lower(),
    )
