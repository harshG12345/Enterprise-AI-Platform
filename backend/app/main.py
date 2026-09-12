"""Enterprise AI Data Science & MLOps Platform - FastAPI Application Entrypoint."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.auth import router as auth_router
from app.api.v1.datasets import router as datasets_router
from app.api.v1.eda import router as eda_router
from app.api.v1.experiments import router as experiments_router
from app.api.v1.health import router as health_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.models import router as models_router
from app.api.v1.monitoring import router as monitoring_router
from app.api.v1.predictions import router as predictions_router
from app.api.v1.preprocessor import router as preprocessor_router
from app.api.v1.projects import router as projects_router
from app.api.v1.training import router as training_router
from app.api.v1.users import router as users_router
from app.config.settings import get_settings
from app.core.exceptions import AppException
from app.core.logger import logger
from app.core.middleware import RequestTracingMiddleware
from app.core.rate_limiter import RateLimitMiddleware
from app.core.responses import APIErrorResponse, ErrorDetail

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    logger.info(f"Initializing {settings.APP_NAME} in {settings.APP_ENV} mode...")

    # Ensure storage directories exist
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.MODEL_DIR, exist_ok=True)

    yield

    logger.info(f"Shutting down {settings.APP_NAME}...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Production-grade Enterprise AI Data Science & MLOps Platform REST API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

# Core Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestTracingMiddleware)


# Global Exception Handlers
@app.exception_handler(AppException)
async def handle_app_exception(request: Request, exc: AppException):
    """Handle custom application domain exceptions."""
    request_id = getattr(request.state, "request_id", None)
    logger.warning(f"AppException: code={exc.code} message={exc.message}", extra={"request_id": request_id})
    return JSONResponse(
        status_code=exc.status_code,
        content=APIErrorResponse(
            success=False,
            error=ErrorDetail(code=exc.code, message=exc.message, details=exc.details),
            request_id=request_id,
        ).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError):
    """Handle Pydantic request validation errors."""
    request_id = getattr(request.state, "request_id", None)
    formatted_errors = {}
    for err in exc.errors():
        loc = ".".join(str(l) for l in err.get("loc", []))
        formatted_errors[loc] = err.get("msg", "Invalid value")

    logger.warning(f"Validation error: {formatted_errors}", extra={"request_id": request_id})
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=APIErrorResponse(
            success=False,
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message="Request data validation failed",
                details=formatted_errors,
            ),
            request_id=request_id,
        ).model_dump(),
    )


@app.exception_handler(StarletteHTTPException)
async def handle_http_exception(request: Request, exc: StarletteHTTPException):
    """Handle standard HTTP exceptions."""
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=exc.status_code,
        content=APIErrorResponse(
            success=False,
            error=ErrorDetail(code="HTTP_ERROR", message=str(exc.detail)),
            request_id=request_id,
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def handle_generic_exception(request: Request, exc: Exception):
    """Handle unexpected internal exceptions safely without leaking tracebacks."""
    request_id = getattr(request.state, "request_id", None)
    logger.exception(f"Unhandled Exception: {str(exc)}", extra={"request_id": request_id})
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=APIErrorResponse(
            success=False,
            error=ErrorDetail(
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected server error occurred. Please reference the request ID when reporting.",
            ),
            request_id=request_id,
        ).model_dump(),
    )


# API v1 Routers
app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(datasets_router, prefix="/api/v1")
app.include_router(eda_router, prefix="/api/v1")
app.include_router(preprocessor_router, prefix="/api/v1")
app.include_router(training_router, prefix="/api/v1")
app.include_router(jobs_router, prefix="/api/v1")
app.include_router(experiments_router, prefix="/api/v1")
app.include_router(models_router, prefix="/api/v1")
app.include_router(predictions_router, prefix="/api/v1")
app.include_router(monitoring_router, prefix="/api/v1")


@app.get("/metrics", tags=["Observability & Metrics"], summary="Prometheus Metrics Scraping Endpoint")
@app.get("/api/v1/metrics", tags=["Observability & Metrics"], summary="Prometheus Metrics Scraping Endpoint")
async def get_metrics():
    """Expose Prometheus formatted telemetry metrics for cluster scrapers."""
    from app.monitoring.metrics import get_prometheus_metrics_response

    return get_prometheus_metrics_response()


@app.get("/openapi.json", include_in_schema=False)
async def openapi_alias():
    """Alias for /api/v1/openapi.json to support standard tooling."""
    return app.openapi()


@app.get("/", tags=["Root"])
async def root():
    """Root landing endpoint."""
    return {
        "app": settings.APP_NAME,
        "status": "online",
        "docs": "/docs",
        "metrics": "/metrics",
        "api_v1": "/api/v1/health",
    }
