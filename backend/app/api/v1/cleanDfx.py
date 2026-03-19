"""Simple, clean API endpoints using dfxCommand service."""

from typing import Annotated, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.services.auth import AuthService
from app.services.dfxCommand import DfxCommand
from app.api.v1.wallet import get_current_user_id

router = APIRouter(prefix="/api/v1/clean", tags=["Clean DFX"])


@router.get("/status")
async def getStatus(
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Get comprehensive status using clean dfxCommand service."""
    try:
        user = await AuthService.get_user_by_id(session, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not user.dfx_identity_name:
            raise HTTPException(status_code=400, detail="No identity found")

        dfx = DfxCommand(network="ic")
        status = dfx.getUserStatus(user.dfx_identity_name)

        return {
            "userId": user_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/balances")
async def getBalances(
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Get all balances using clean dfxCommand service."""
    try:
        user = await AuthService.get_user_by_id(session, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not user.dfx_identity_name:
            raise HTTPException(status_code=400, detail="No identity found")

        dfx = DfxCommand(network="ic")

        # Get individual balance calls for detailed info
        icp = dfx.ledgerGetBalance(identity=user.dfx_identity_name)
        cycles = dfx.cyclesGetBalance(identity=user.dfx_identity_name)
        wallet = dfx.walletGetBalance(identity=user.dfx_identity_name)

        return {
            "userId": user_id,
            "identity": user.dfx_identity_name,
            "principalId": user.principal_id,
            "accountId": user.account_id,
            "balances": {"icp": icp, "cycles": cycles, "wallet": wallet},
            "summary": {
                "icpAmount": icp.get("balanceIcp", 0),
                "cyclesAmount": cycles.get("balanceCycles", 0),
                "hasIcp": icp.get("balanceE8s", 0) >= 2_000_000,
                "hasCycles": cycles.get("balanceCycles", 0) >= 20_000_000,
                "canConvert": icp.get("balanceE8s", 0) >= 2_000_000,
                "readyToDeploy": cycles.get("balanceCycles", 0) >= 20_000_000,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/convert")
async def convertIcp(
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
    amount: Optional[str] = None,
):
    """Convert ICP to cycles using clean dfxCommand service."""
    try:
        user = await AuthService.get_user_by_id(session, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not user.dfx_identity_name:
            raise HTTPException(status_code=400, detail="No identity found")

        dfx = DfxCommand(network="ic")

        if amount:
            # Convert specific amount
            result = dfx.cyclesConvert(amount, identity=user.dfx_identity_name)
        else:
            # Auto-convert available ICP
            result = dfx.autoConvertIcp(user.dfx_identity_name)

        if result["success"]:
            # Update user's cached balance
            newBalance = dfx.cyclesGetBalance(user.dfx_identity_name)
            if newBalance["success"]:
                user.wallet_cycles_balance = str(newBalance["balanceCycles"])
                await session.commit()

        return {
            "userId": user_id,
            "conversion": result,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/identities")
async def listIdentities():
    """List all dfx identities."""
    try:
        dfx = DfxCommand()
        identities = dfx.identityList()

        return {
            "identities": identities,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-icp")
async def sendIcp(
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
    toAddress: str,
    amount: str,
    memo: str = "12345",
):
    """Send ICP using clean dfxCommand service."""
    try:
        user = await AuthService.get_user_by_id(session, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not user.dfx_identity_name:
            raise HTTPException(status_code=400, detail="No identity found")

        dfx = DfxCommand(network="ic")
        result = dfx.ledgerSend(toAddress, amount, memo, identity=user.dfx_identity_name)

        return {
            "userId": user_id,
            "transfer": result,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-cycles")
async def sendCycles(
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
    toPrincipal: str,
    amount: str,
):
    """Send cycles using clean dfxCommand service."""
    try:
        user = await AuthService.get_user_by_id(session, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not user.dfx_identity_name:
            raise HTTPException(status_code=400, detail="No identity found")

        dfx = DfxCommand(network="ic")
        result = dfx.cyclesSend(toPrincipal, amount, identity=user.dfx_identity_name)

        return {
            "userId": user_id,
            "transfer": result,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-canister")
async def createCanister(
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
    name: Optional[str] = None,
    withCycles: Optional[str] = None,
):
    """Create canister using clean dfxCommand service."""
    try:
        user = await AuthService.get_user_by_id(session, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not user.dfx_identity_name:
            raise HTTPException(status_code=400, detail="No identity found")

        dfx = DfxCommand(network="ic")

        # Check cycles balance first
        balance = dfx.cyclesGetBalance(user.dfx_identity_name)
        if not balance["success"] or balance["balanceCycles"] < 100_000_000:
            raise HTTPException(
                status_code=400,
                detail="Insufficient cycles. Need at least 100M cycles for canister creation.",
            )

        result = dfx.canisterCreate(name, withCycles, identity=user.dfx_identity_name)

        return {
            "userId": user_id,
            "canister": result,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/canister/{canister_id}/status")
async def getCanisterStatus(
    canister_id: str,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Get canister status using clean dfxCommand service."""
    try:
        user = await AuthService.get_user_by_id(session, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not user.dfx_identity_name:
            raise HTTPException(status_code=400, detail="No identity found")

        dfx = DfxCommand(network="ic")
        result = dfx.canisterGetStatus(canister_id, identity=user.dfx_identity_name)

        return {
            "userId": user_id,
            "canisterId": canister_id,
            "status": result,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
