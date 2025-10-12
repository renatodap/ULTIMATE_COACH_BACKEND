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

    yield

    # Shutdown
    logger.info("application_shutdown")


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

    if settings.is_development:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": str(exc),
                "type": type(exc).__name__,
            },
        )

    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error"},
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
from app.api.v1 import health, auth, users, onboarding, foods, meals

app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(onboarding.router, prefix="/api/v1/onboarding", tags=["Onboarding"])
app.include_router(foods.router, prefix="/api/v1", tags=["Nutrition - Foods"])
app.include_router(meals.router, prefix="/api/v1", tags=["Nutrition - Meals"])

# Future routers will be added here:
# from app.api.v1 import activities, coach
# app.include_router(activities.router, prefix="/api/v1", tags=["Activities"])
# app.include_router(coach.router, prefix="/api/v1", tags=["AI Coach"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_level=settings.LOG_LEVEL.lower(),
    )
