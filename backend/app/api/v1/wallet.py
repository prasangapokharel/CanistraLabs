"""ICP Wallet API routes for user identity and funding management."""

from typing import Annotated, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.services.icpIdentityManager import ICPIdentityManager, ICPError
from app.services.autoFundingDetector import AutoFundingDetector, format_cycles
from app.services.auth import AuthService
from app.utils.security import verify_token
from app.cache.wallet_cache import wallet_cache

router = APIRouter(prefix="/api/v1/wallet", tags=["ICP Wallet"])


async def get_bearer_token(authorization: Annotated[Optional[str], Header()] = None) -> str:
    """Extract bearer token from Authorization header."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
        )

    return parts[1]


async def get_current_user_id(
    authorization: Annotated[str, Depends(get_bearer_token)],
) -> int:
    """Get current user ID from token."""
    token_data = verify_token(authorization, token_type="access")
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    return int(token_data.sub)


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
            "funding_address": user.account_id,  # For clarity - this is where to send ICP
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

        return {
            "cycles_balance": funding_status["cycles_balance"],
            "icp_balance": funding_status["balance"],
            "formatted_icp": funding_status.get("formatted_icp", "0 ICP"),
            "formatted_cycles": funding_status.get("formatted_cycles", "0 cycles"),
            "funding_required": not funding_status["funded"],
            "auto_convert_available": funding_status.get("auto_convert_available", False),
            "has_pending_icp": funding_status.get("has_pending_icp", False),
            "principal_id": user.principal_id,
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
        instructions = await funding_detector.get_funding_instructions(user)

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
    Recreate the user's ICP identity if something went wrong.

    This will create a new identity and principal ID.
    WARNING: Any existing canisters will be orphaned.
    """
    try:
        # Invalidate cache for this user
        wallet_cache.invalidate(user_id)

        user = await AuthService.get_user_by_id(session, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Ensure identity is available in dfx
        ICPIdentityManager._restore_identity_files(user)

        # Check funding status with both ICP and cycles
        funding_detector = AutoFundingDetector()
        funding_status = await funding_detector.check_user_funding_status(session, user)
        await session.commit()

        result = {
            "cycles_balance": funding_status["cycles_balance"],
            "icp_balance": funding_status["balance"],
            "formatted_icp": funding_status.get("formatted_icp", "0 ICP"),
            "formatted_cycles": funding_status.get("formatted_cycles", "0 cycles"),
            "funding_required": not funding_status["funded"],
            "auto_convert_available": funding_status.get("auto_convert_available", False),
            "has_pending_icp": funding_status.get("has_pending_icp", False),
            "principal_id": user.principal_id,
            "message": funding_status["message"],
        }

        # Update cache with fresh data
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
