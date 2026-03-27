"""
API endpoints for managing the ICP-to-Cycles cron service
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any, Optional
from app.services.cron.cron import cron_service

router = APIRouter(prefix="/api/v1/cron", tags=["Cron Service"])


@router.get("/status")
async def get_cron_status() -> Dict[str, Any]:
    """Get the current status and statistics of the cron service."""
    try:
        return await cron_service.get_service_status()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cron status: {str(e)}",
        )


@router.post("/start")
async def start_cron_service() -> Dict[str, Any]:
    """Start the cron service."""
    try:
        return await cron_service.start_service()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start cron service: {str(e)}",
        )


@router.post("/stop")
async def stop_cron_service() -> Dict[str, Any]:
    """Stop the cron service."""
    try:
        return await cron_service.stop_service()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop cron service: {str(e)}",
        )


@router.post("/trigger")
async def trigger_manual_conversion(user_id: Optional[int] = None) -> Dict[str, Any]:
    """Manually trigger ICP to cycles conversion for a specific user or all users."""
    try:
        return await cron_service.trigger_manual_conversion(user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger manual conversion: {str(e)}",
        )
