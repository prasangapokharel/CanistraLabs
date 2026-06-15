"""Unified dfx command API — maps official dfx CLI operations to HTTP endpoints."""

from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.config import settings
from app.database.db import get_db
from app.schemas.dfx import (
    DfxCanisterCreateRequest,
    DfxCanisterPowerRequest,
    DfxConvertRequest,
    DfxCyclesTopUpRequest,
    DfxDeployRequest,
    DfxDepositCyclesRequest,
    DfxProjectDeployRequest,
)
from app.services.dfxApiService import DfxApiService
from app.services.dfxCommand import DfxCommand
from app.services.dfxRegistry import registry_summary

router = APIRouter(prefix="/api/v1/dfx", tags=["DFX Commands"])


def _ts() -> str:
    return datetime.utcnow().isoformat()


# ---------------------------------------------------------------------------
# Catalog & meta
# ---------------------------------------------------------------------------


@router.get("/commands")
async def list_dfx_commands():
    """Catalog of dfx commands mapped to this API (implemented vs pending)."""
    summary = registry_summary()
    return {**summary, "dfx_version": DfxCommand().dfxPath, "timestamp": _ts()}


@router.get("/version")
async def dfx_version():
    """dfx --version"""
    dfx = DfxCommand()
    rc, out, err = dfx._runCommand(["--version"])
    return {
        "command": "dfx --version",
        "success": rc == 0,
        "version": out.strip() or err.strip(),
        "timestamp": _ts(),
    }


@router.get("/ping")
async def dfx_ping(network: str = "ic"):
    """dfx ping [network]"""
    result = DfxCommand().ping(network)
    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=result)
    return {"command": f"dfx ping {network}", "result": result, "timestamp": _ts()}


@router.get("/info/{subcommand}")
async def dfx_info(subcommand: str):
    """dfx info <subcommand> (read-only, no auth)."""
    allowed = {
        "replica-rev",
        "webserver-port",
        "networks-json-path",
        "config-json-path",
        "candid-ui-url",
        "security-policy",
        "default-effective-canister-id",
        "pocketic-config-port",
        "telemetry-log-path",
    }
    if subcommand not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported info subcommand. Allowed: {sorted(allowed)}",
        )
    result = DfxCommand().infoCommand(subcommand)
    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=result)
    return {"command": f"dfx info {subcommand}", "result": result, "timestamp": _ts()}


# ---------------------------------------------------------------------------
# Identity / ledger / cycles / wallet
# ---------------------------------------------------------------------------


@router.get("/identity/whoami")
async def identity_whoami(
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    return await DfxApiService.run_for_user_identity(
        session,
        user_id,
        "dfx identity whoami",
        lambda identity: DfxCommand().identityWhoami(),
    )


@router.get("/identity/principal")
async def identity_principal(
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    return await DfxApiService.run_for_user_identity(
        session,
        user_id,
        "dfx identity get-principal",
        lambda identity: DfxCommand().identityGetPrincipal(identity),
    )


@router.get("/ledger/account-id")
async def ledger_account_id(
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    dfx = DfxCommand.from_settings()
    return await DfxApiService.run_for_user_identity(
        session,
        user_id,
        "dfx ledger account-id",
        lambda identity: dfx.ledgerGetAccountId(identity),
    )


@router.get("/ledger/balance")
async def ledger_balance(
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    dfx = DfxCommand.from_settings()
    return await DfxApiService.run_for_user_identity(
        session,
        user_id,
        "dfx ledger balance",
        lambda identity: dfx.ledgerGetBalance(identity=identity),
    )


@router.get("/cycles/balance")
async def cycles_balance(
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    dfx = DfxCommand.from_settings()
    return await DfxApiService.run_for_user_identity(
        session,
        user_id,
        "dfx cycles balance",
        lambda identity: dfx.cyclesGetBalance(identity),
    )


@router.post("/cycles/convert")
async def cycles_convert(
    body: DfxConvertRequest,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    dfx = DfxCommand.from_settings()

    async def _run(session, user_id, command, runner):
        return await DfxApiService.run_for_user_identity(session, user_id, command, runner)

    if body.amount:
        return await _run(
            session,
            user_id,
            f"dfx cycles convert --amount {body.amount}",
            lambda identity: dfx.cyclesConvert(body.amount, identity),
        )

    from app.services.auth import AuthService

    user = await AuthService.get_user_by_id(session, user_id)
    return await _run(
        session,
        user_id,
        "dfx cycles convert (auto)",
        lambda identity: dfx.autoConvertIcp(user.dfx_identity_name),
    )


@router.post("/cycles/top-up")
async def cycles_top_up(
    body: DfxCyclesTopUpRequest,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    await DfxApiService._verify_canister_owner(session, body.canister_id, user_id)
    dfx = DfxCommand.from_settings()
    return await DfxApiService.run_for_user_identity(
        session,
        user_id,
        f"dfx cycles top-up {body.canister_id} {body.amount}",
        lambda identity: dfx.cyclesTopUp(body.canister_id, body.amount, identity),
    )


@router.get("/wallet/balance")
async def wallet_balance(
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    dfx = DfxCommand.from_settings()
    return await DfxApiService.run_for_user_identity(
        session,
        user_id,
        "dfx wallet balance",
        lambda identity: dfx.walletGetBalance(identity),
    )


# ---------------------------------------------------------------------------
# Canister lifecycle (by canister ID — ownership required)
# ---------------------------------------------------------------------------


@router.post("/canister/create")
async def canister_create(
    body: DfxCanisterCreateRequest,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    dfx = DfxCommand(network=body.network or settings.effective_deploy_network)
    return await DfxApiService.run_for_user_identity(
        session,
        user_id,
        "dfx canister create",
        lambda identity: dfx.canisterCreate(
            body.name, body.with_cycles, identity, body.network
        ),
    )


@router.post("/deploy")
async def dfx_deploy(
    body: DfxDeployRequest,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    dfx = DfxCommand(network=body.network or settings.effective_deploy_network)
    return await DfxApiService.run_for_user_identity(
        session,
        user_id,
        "dfx deploy",
        lambda identity: dfx.canisterDeploy(
            body.name, identity, body.network, body.with_cycles
        ),
    )


@router.get("/canister/{canister_id}/status")
async def canister_status(
    canister_id: str,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    dfx = DfxCommand()
    return await DfxApiService.canister_op(
        session,
        user_id,
        canister_id,
        "dfx canister status",
        lambda identity, network, project: dfx.canisterGetStatus(
            canister_id, identity, network
        ),
    )


@router.get("/canister/{canister_id}/info")
async def canister_info(
    canister_id: str,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    dfx = DfxCommand()
    return await DfxApiService.canister_op(
        session,
        user_id,
        canister_id,
        "dfx canister info",
        lambda identity, network, project: dfx.canisterInfo(
            canister_id, identity, network
        ),
    )


@router.get("/canister/{canister_id}/url")
async def canister_url(
    canister_id: str,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    dfx = DfxCommand()
    return await DfxApiService.canister_op(
        session,
        user_id,
        canister_id,
        "dfx canister url",
        lambda identity, network, project: dfx.canisterUrl(
            canister_id, identity, network
        ),
    )


@router.post("/canister/{canister_id}/start")
async def canister_start(
    canister_id: str,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    dfx = DfxCommand()
    return await DfxApiService.canister_op(
        session,
        user_id,
        canister_id,
        "dfx canister start",
        lambda identity, network, project: dfx.canisterStart(
            canister_id, identity, network
        ),
    )


@router.post("/canister/{canister_id}/stop")
async def canister_stop(
    canister_id: str,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    dfx = DfxCommand()
    return await DfxApiService.canister_op(
        session,
        user_id,
        canister_id,
        "dfx canister stop",
        lambda identity, network, project: dfx.canisterStop(
            canister_id, identity, network
        ),
    )


@router.delete("/canister/{canister_id}")
async def canister_delete(
    canister_id: str,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    project = await DfxApiService._verify_canister_owner(session, canister_id, user_id)
    from app.services.canisterFactory import CanisterFactory

    await CanisterFactory.delete_project_canister(session, project)
    await session.commit()
    return {
        "command": "dfx canister delete --yes",
        "canister_id": canister_id,
        "project_id": project.id,
        "success": True,
        "timestamp": _ts(),
    }


@router.post("/canister/{canister_id}/deposit-cycles")
async def canister_deposit_cycles(
    canister_id: str,
    body: DfxDepositCyclesRequest,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    dfx = DfxCommand()
    return await DfxApiService.canister_op(
        session,
        user_id,
        canister_id,
        "dfx canister deposit-cycles",
        lambda identity, network, project: dfx.canisterDepositCycles(
            canister_id, body.amount, identity, network
        ),
    )


# ---------------------------------------------------------------------------
# Project-scoped (official deploy path)
# ---------------------------------------------------------------------------


@router.post("/projects/{project_id}/deploy", status_code=status.HTTP_202_ACCEPTED)
async def project_deploy(
    project_id: int,
    body: DfxProjectDeployRequest,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Deploy project assets to ICP using the official CanisterFactory path
    (dfx deploy asset canister via ICPService). Supports async Celery queue.
    """
    from app.utils.cycleRequirements import build_insufficient_cycles_error
    from app.utils.http_errors import safe_error_detail

    try:
        return await DfxApiService.deploy_project(
            session, user_id, project_id, body.code_content
        )
    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        err_text = safe_error_detail(e, fallback="Deployment failed")
        if "insufficient cycles" in err_text.lower() or "not enough cycles" in err_text.lower():
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=build_insufficient_cycles_error(0, err_text),
            ) from e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deployment failed: {err_text}",
        ) from e


@router.post("/projects/{project_id}/update-canister")
async def project_update_canister(
    project_id: int,
    body: DfxProjectDeployRequest,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Update an existing project canister with new content (dfx deploy reinstall)."""
    try:
        return await DfxApiService.update_project(
            session, user_id, project_id, body.code_content
        )
    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        from app.utils.http_errors import safe_error_detail

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Canister update failed: {safe_error_detail(e, fallback='Canister update failed')}",
        ) from e


@router.get("/projects/{project_id}/deployments")
async def list_project_deployments(
    project_id: int,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 10,
):
    """Deployment history for a project."""
    return await DfxApiService.list_deployments(
        session, user_id, project_id, skip=skip, limit=limit
    )


@router.get("/projects/{project_id}/deployments/{deployment_id}")
async def get_project_deployment(
    project_id: int,
    deployment_id: int,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Poll status of a specific deployment."""
    return await DfxApiService.get_deployment(
        session, user_id, project_id, deployment_id
    )


@router.post("/projects/{project_id}/power")
async def project_power(
    project_id: int,
    body: DfxCanisterPowerRequest,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Start or stop a project canister (dfx canister start/stop)."""
    return await DfxApiService.project_power(session, user_id, project_id, body.enabled)


@router.delete("/projects/{project_id}/canister")
async def project_delete_canister(
    project_id: int,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete project canister from ICP (dfx canister delete --yes)."""
    return await DfxApiService.delete_project_canister(session, user_id, project_id)
