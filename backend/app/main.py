"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import (
    auth,
    projects,
    deployments,
    wallet,
    cleanDfx,
    dynamic_deployment,
    domain_management,
)
from app.config import settings


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="ICP-based hosting platform backend",
        debug=settings.debug,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Change in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "app_name": settings.app_name,
            "version": settings.app_version,
        }

    # API versioning
    @app.get("/api/v1", tags=["Info"])
    async def api_info():
        """API information endpoint."""
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
        }

    # Include routers
    app.include_router(auth.router)
    app.include_router(projects.router)
    app.include_router(deployments.router)
    app.include_router(wallet.router)
    app.include_router(cleanDfx.router)  # Clean, minimal dfx API
    app.include_router(dynamic_deployment.router)  # Dynamic deployment API
    app.include_router(domain_management.router)  # Domain management API

    return app


# Create the app instance for uvicorn
app = create_app()
