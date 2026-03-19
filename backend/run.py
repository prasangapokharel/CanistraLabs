"""FastAPI application entry point."""

from fastapi import FastAPI

from app.api.v1 import auth, projects
from app.main import create_app

# Create FastAPI application
app: FastAPI = create_app()

# Include routers
app.include_router(auth.router)
app.include_router(projects.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "run:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
