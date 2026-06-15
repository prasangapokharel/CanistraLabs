"""FastAPI application factory."""

import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import (
    auth,
    projects,
    wallet,
    domainManagement,
    metrics,
    cron,
    dfxApi,
)
from app.config import settings
from app.middleware.security import SecurityHeadersMiddleware
from app.utils.http_errors import safe_error_detail

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application startup — ensure local dfx replica when configured (non-blocking)."""

    def _start_dfx_background() -> None:
        from app.services.dfxLifecycle import ensure_local_replica

        try:
            status = ensure_local_replica()
            logger.info("dfx lifecycle: %s", status)
        except Exception as exc:
            logger.warning("dfx lifecycle failed: %s", exc)

    if settings.dfx_auto_start:
        threading.Thread(target=_start_dfx_background, daemon=True).start()
    yield


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Decentralized ICP hosting platform backend",
        debug=settings.debug,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        redirect_slashes=False,
        lifespan=lifespan,
    )

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Admin-Api-Key"],
    )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"detail": safe_error_detail(exc)},
        )

    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint."""
        from app.services.dfxLifecycle import is_local_replica_running

        return {
            "status": "healthy",
            "app_name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "network": settings.icp_network,
            "deploy_network": settings.effective_deploy_network,
            "dfx_local_replica": is_local_replica_running(),
            "dfx_auto_start": settings.dfx_auto_start,
        }

    @app.get("/api/v1", tags=["Info"])
    async def api_info():
        """API information endpoint."""
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "network": settings.icp_network,
        }

    app.include_router(auth.router)
    app.include_router(projects.router)
    app.include_router(wallet.router)
    app.include_router(domainManagement.router)
    app.include_router(metrics.router)
    app.include_router(cron.router)
    app.include_router(dfxApi.router)

    return app


app = create_app()
