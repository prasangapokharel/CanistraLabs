"""
API endpoints for managing the ICP-to-Cycles cron service.
Protected by admin API key — intended for internal schedulers only.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import require_admin
from app.services.cron.cron import cron_service
from app.utils.http_errors import safe_error_detail

router = APIRouter(prefix="/api/v1/cron", tags=["Cron Service"])


@router.get("/status", dependencies=[Depends(require_admin)])
async def get_cron_status() -> Dict[str, Any]:
    """Get the current status and statistics of the cron service."""
    try:
        return await cron_service.get_service_status()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=safe_error_detail(e, fallback="Failed to get cron status"),
        )


@router.post("/start", dependencies=[Depends(require_admin)])
async def start_cron_service() -> Dict[str, Any]:
    """Start the cron service."""
    try:
        return await cron_service.start_service()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=safe_error_detail(e, fallback="Failed to start cron service"),
        )


@router.post("/stop", dependencies=[Depends(require_admin)])
async def stop_cron_service() -> Dict[str, Any]:
    """Stop the cron service."""
    try:
        return await cron_service.stop_service()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=safe_error_detail(e, fallback="Failed to stop cron service"),
        )


@router.post("/trigger", dependencies=[Depends(require_admin)])
async def trigger_manual_conversion(user_id: Optional[int] = None) -> Dict[str, Any]:
    """Manually trigger ICP to cycles conversion for a specific user or all users."""
    try:
        return await cron_service.trigger_manual_conversion(user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=safe_error_detail(e, fallback="Failed to trigger manual conversion"),
        )
