"""FastAPI application entry point."""

import os

import uvicorn

from app.main import app

__all__ = ["app"]

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "run:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("ENVIRONMENT", "development").lower() != "production",
    )
