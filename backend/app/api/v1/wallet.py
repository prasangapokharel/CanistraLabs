"""ICP Wallet API routes for user identity and funding management."""

from typing import Annotated
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.database.db import get_db
from app.config import settings
from app.services.icpIdentityManager import ICPIdentityManager, ICPError
from app.services.autoFundingDetector import AutoFundingDetector, format_cycles
from app.services.auth import AuthService
from app.cache.wallet_cache import wallet_cache
from app.utils.http_errors import safe_error_detail

router = APIRouter(prefix="/api/v1/wallet", tags=["ICP Wallet"])


@router.get("/identity")
async def get_wallet_identity(
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Get the user's ICP identity information and wallet status with automated funding detection.

    Returns:
        - identity_name: User's dfx identity name
        - principal_id: ICP principal ID
        - cycles_balance: Current cycles balance
        - icp_balance: Current ICP token balance
        - funding_required: Whether funding is needed for deployments
        - auto_convert_available: Whether ICP can be auto-converted to cycles
        - status: Identity status (active, pending, etc.)
    """
    try:
        # Check cache first
        cached_data = wallet_cache.get(user_id)
        if cached_data:
            return cached_data

        user = await AuthService.get_user_by_id(session, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Get or create identity context
        identity_context = await ICPIdentityManager.get_user_identity_context(session, user)

        # Check funding status with Rosetta API
        funding_detector = AutoFundingDetector()
        funding_status = await funding_detector.check_user_funding_status(session, user)

        # Commit any changes (like new identity creation)
        await session.commit()

        result = {
            "identity_name": identity_context["identity_name"],
            "principal_id": identity_context["principal_id"],
            "account_id": user.account_id,  # Account ID for ICP funding
            "cycles_balance": funding_status["cycles_balance"],
            "icp_balance": funding_status["balance"],
            "formatted_icp": funding_status.get("formatted_icp", "0 ICP"),
            "formatted_cycles": funding_status.get("formatted_cycles", "0 cycles"),
            "funding_required": not funding_status["funded"],
            "auto_convert_available": funding_status.get("auto_convert_available", False),
            "has_pending_icp": funding_status.get("has_pending_icp", False),
            "status": identity_context["status"],
            "message": funding_status["message"],
            "funding_address": user.account_id,
            "token_symbol": funding_status.get("token_symbol", settings.token_symbol),
            "network": funding_status.get("network", settings.dfx_network),
            "deploy_network": settings.effective_deploy_network,
            "use_testicp": funding_status.get("use_testicp", settings.use_testicp),
            "deploy_ready": funding_status.get("deploy_ready", False),
            "requirements": funding_status.get("requirements"),
            "created_at": user.identity_created_at.isoformat()
            if user.identity_created_at
            else None,
        }

        # Cache the result
        wallet_cache.set(user_id, result)

        return result

    except ICPError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ICP identity error: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get wallet identity: {str(e)}",
        )


@router.post("/refresh-balance")
async def refresh_wallet_balance(
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Refresh the user's ICP and cycles balance from both Rosetta API and ICP network.

    Returns updated balance information with auto-conversion availability.
    """
    try:
        user = await AuthService.get_user_by_id(session, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if not user.dfx_identity_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No ICP identity found. Please contact support.",
            )

        # Ensure identity is available in dfx
        ICPIdentityManager._restore_identity_files(user)

        # Check funding status with both ICP and cycles
        funding_detector = AutoFundingDetector()
        funding_status = await funding_detector.check_user_funding_status(session, user)
        await session.commit()

        wallet_cache.invalidate(user_id)

        return {
            "cycles_balance": funding_status["cycles_balance"],
            "icp_balance": funding_status["balance"],
            "formatted_icp": funding_status.get("formatted_icp", "0 ICP"),
            "formatted_cycles": funding_status.get("formatted_cycles", "0 cycles"),
            "funding_required": not funding_status["funded"],
            "auto_convert_available": funding_status.get("auto_convert_available", False),
            "has_pending_icp": funding_status.get("has_pending_icp", False),
            "principal_id": user.principal_id,
            "requirements": funding_status.get("requirements"),
            "deploy_ready": funding_status.get("deploy_ready", False),
            "message": funding_status["message"],
        }

    except ICPError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check balance: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh balance: {str(e)}",
        )


@router.post("/convert-icp-to-cycles")
async def convert_icp_to_cycles(
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Automatically convert ICP tokens to cycles for the user.

    Returns conversion result.
    """
    try:
        user = await AuthService.get_user_by_id(session, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if not user.dfx_identity_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No ICP identity found",
            )

        # Perform automatic conversion
        funding_detector = AutoFundingDetector()
        conversion_result = await funding_detector.auto_convert_icp_to_cycles(session, user)
        await session.commit()

        if conversion_result["success"]:
            return {
                "success": True,
                "message": conversion_result["message"],
                "cycles_balance": conversion_result["cycles_balance"],
                "formatted_cycles": conversion_result["formatted_cycles"],
            }
        else:
            return {
                "success": False,
                "message": conversion_result["message"],
                "error": conversion_result.get("error"),
                "nns_url": conversion_result.get("nns_url"),
            }

    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Conversion failed: {str(e)}",
        )


@router.get("/funding-instructions")
async def get_detailed_funding_instructions(
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Get detailed, personalized funding instructions for the user.

    Returns step-by-step instructions with current status.
    """
    try:
        user = await AuthService.get_user_by_id(session, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Generate personalized instructions
        funding_detector = AutoFundingDetector()
        instructions = await funding_detector.get_funding_instructions(session, user)

        return instructions

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get funding instructions: {str(e)}",
        )


@router.get("/network-status")
async def get_network_status(
    user_id: Annotated[int, Depends(get_current_user_id)],
):
    """
    Get ICP network status via Rosetta API.

    Returns network health and token information.
    """
    try:
        funding_detector = AutoFundingDetector()
        network_info = funding_detector.get_network_info()

        return {
            "rosetta_healthy": network_info["healthy"],
            "network_info": network_info,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get network status: {str(e)}",
        )


@router.post("/recreate-identity")
async def recreate_identity(
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Recreate the user's ICP identity.

    WARNING: Any existing canisters tied to the old principal will be orphaned.
    """
    try:
        wallet_cache.invalidate(user_id)

        user = await AuthService.get_user_by_id(session, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Clear existing identity fields before creating a new one
        user.dfx_identity_name = None
        user.principal_id = None
        user.account_id = None
        user.encrypted_identity_key = None
        user.wallet_cycles_balance = "0"
        user.identity_created_at = None
        await session.flush()

        identity_result = await ICPIdentityManager.create_user_identity(session, user)
        await session.commit()

        funding_detector = AutoFundingDetector()
        funding_status = await funding_detector.check_user_funding_status(session, user)

        result = {
            "success": True,
            "message": identity_result.get("message", "New ICP identity created"),
            "identity_name": identity_result.get("identity_name"),
            "principal_id": identity_result.get("principal_id"),
            "account_id": identity_result.get("account_id"),
            "funding_address": identity_result.get("account_id"),
            "cycles_balance": funding_status["cycles_balance"],
            "icp_balance": funding_status["balance"],
            "formatted_icp": funding_status.get("formatted_icp", "0 ICP"),
            "formatted_cycles": funding_status.get("formatted_cycles", "0 cycles"),
            "funding_required": not funding_status["funded"],
            "auto_convert_available": funding_status.get("auto_convert_available", False),
        }

        wallet_cache.set(user_id, result)
        return result

    except ICPError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to recreate identity: {str(e)}",
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to recreate identity: {str(e)}",
        )
