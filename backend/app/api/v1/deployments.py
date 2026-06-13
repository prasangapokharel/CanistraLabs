"""Deployment API routes."""

import logging
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from app.api.deps import get_current_user_id
from app.config import settings
from app.database.db import get_db
from app.models.project import Project
from app.schemas.project import ProjectDeployRequest, CanisterPowerRequest
from app.services.deployment import DeploymentService
from app.services.projects import ProjectService
from app.services.canisterFactory import CanisterFactory
from app.models.deployment import Deployment, DeploymentStatus
from app.utils.http_errors import safe_error_detail
from app.utils.cycleRequirements import build_insufficient_cycles_error
from app.utils.dfxErrors import http_error_detail, parse_dfx_error
from app.utils.canisterNetwork import is_local_canister_id, network_for_canister

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/deployments", tags=["Deployments"])

TERMINAL_DEPLOY_STATUSES = {
    "success",
    "failed",
    "pending_funding",
    DeploymentStatus.SUCCESS.value,
    DeploymentStatus.FAILED.value,
}


def _serialize_deployment(deployment: Deployment) -> dict:
    return {
        "id": deployment.id,
        "deployment_id": deployment.id,
        "status": deployment.status,
        "message": deployment.message,
        "canister_id": deployment.canister_id,
        "url": deployment.deployment_url,
        "created_at": deployment.created_at.isoformat() if deployment.created_at else None,
        "started_at": deployment.started_at.isoformat() if deployment.started_at else None,
        "completed_at": deployment.completed_at.isoformat() if deployment.completed_at else None,
    }


def _enqueue_deploy_task(
    project_id: int,
    deployment_id: int,
    code_content: str,
) -> Optional[str]:
    if not settings.async_deploy_enabled:
        return None
    try:
        from app.tasks.deployment import run_project_deploy_task

        task = run_project_deploy_task.delay(project_id, deployment_id, code_content)
        return task.id
    except Exception as exc:
        logger.warning("Celery unavailable, falling back to sync deploy: %s", exc)
        return None


async def _run_sync_deploy(
    session: AsyncSession,
    project: Project,
    deployment: Deployment,
    code_content: str,
) -> dict:
    result = await CanisterFactory.create_project_canister(
        session=session,
        project=project,
        html_content=code_content,
        deployment=deployment,
    )
    await session.commit()

    if result.get("status") == "pending_funding":
        return {
            "deployment_id": deployment.id,
            "project_id": project.id,
            "canister_id": None,
            "url": None,
            "status": "pending_funding",
            "message": result.get("message", "Funding required"),
            "principal_id": result.get("principal_id"),
            "cycles_balance": result.get("cycles_balance", "0"),
            "funding_required": True,
            "can_retry": True,
            "async": False,
            "error_code": result.get("error_code", "insufficient_cycles"),
            "cycles_required": result.get("cycles_required"),
            "cycles_shortfall": result.get("cycles_shortfall"),
            "recommended_icp": result.get("recommended_icp"),
            "action": result.get("action"),
        }

    return {
        "deployment_id": deployment.id,
        "project_id": project.id,
        "canister_id": result["canister_id"],
        "url": result["url"],
        "status": result["status"],
        "message": f"Successfully deployed to {result['url']}",
        "async": False,
    }


@router.post("/projects/{project_id}/deploy", status_code=status.HTTP_202_ACCEPTED)
async def deploy_project(
    project_id: int,
    deploy_request: ProjectDeployRequest,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Deploy a project to a unique individual ICP canister.

    When Celery is available, returns immediately with ``status: queued`` and
    runs deploy in a background worker. Poll ``GET .../deployments/{id}`` for progress.
    """
    project = await ProjectService.get_project_by_id(session, project_id, user_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    try:
        code_content = deploy_request.code_content or project.code_content or ""

        if not code_content.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No code content provided for deployment",
            )

        if code_content.strip() and code_content != (project.code_content or ""):
            project.code_content = code_content
            await session.flush()

        deployment = Deployment(
            project_id=project_id,
            status=DeploymentStatus.QUEUED.value,
            message="Queued for deployment…",
        )
        session.add(deployment)
        await session.flush()

        task_id = _enqueue_deploy_task(project_id, deployment.id, code_content)
        if task_id:
            deployment.task_id = task_id
            deployment.status = DeploymentStatus.QUEUED.value
            deployment.message = "Deploy queued — processing in background"
            await session.commit()
            return {
                "deployment_id": deployment.id,
                "project_id": project_id,
                "canister_id": None,
                "url": None,
                "status": "queued",
                "message": deployment.message,
                "async": True,
            }

        deployment.status = DeploymentStatus.PENDING.value
        deployment.message = "Creating individual canister…"
        await session.flush()
        return await _run_sync_deploy(session, project, deployment, code_content)

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
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deployment failed: {err_text}",
        )


@router.get("/projects/{project_id}/deployments/{deployment_id}")
async def get_deployment_status(
    project_id: int,
    deployment_id: int,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Get the status of a specific deployment."""
    # Verify project ownership
    project = await ProjectService.get_project_by_id(session, project_id, user_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Get deployment
    deployment = await DeploymentService.get_deployment_status(session, deployment_id)

    if not deployment or deployment.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deployment not found",
        )

    return {
        "deployment_id": deployment.id,
        "project_id": deployment.project_id,
        "status": deployment.status,
        "message": deployment.message,
        "canister_id": deployment.canister_id,
        "url": deployment.deployment_url,
        "started_at": deployment.started_at.isoformat() if deployment.started_at else None,
        "completed_at": deployment.completed_at.isoformat() if deployment.completed_at else None,
        "created_at": deployment.created_at.isoformat() if deployment.created_at else None,
    }


@router.get("/projects/{project_id}/deployments")
async def list_deployments(
    project_id: int,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 10,
):
    """Get deployment history for a project."""
    # Verify project ownership
    project = await ProjectService.get_project_by_id(session, project_id, user_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Get deployments
    deployments = await DeploymentService.get_project_deployments(
        session, project_id, limit=limit, skip=skip
    )

    return [_serialize_deployment(d) for d in deployments]


@router.get("/canisters/{canister_id}/status")
async def get_canister_status(
    canister_id: str,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Get canister status for a canister owned by the authenticated user."""
    ownership = await session.execute(
        select(Project).where(Project.canister_id == canister_id, Project.user_id == user_id)
    )
    if not ownership.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Canister not found",
        )

    try:
        status_info = await DeploymentService.get_canister_status(session, canister_id)
        cycles = status_info.get("cycles_balance", status_info.get("cycles", 0))
        memory = status_info.get("memory_size", status_info.get("memory_usage", 0))
        return {
            **status_info,
            "canister_id": canister_id,
            "cycles_balance": cycles,
            "memory_size": memory,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=safe_error_detail(e, fallback="Failed to get canister status"),
        )


@router.post("/projects/{project_id}/canister/power")
async def set_canister_power(
    project_id: int,
    body: CanisterPowerRequest,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Start or stop a project's canister (toggle hosting on/off)."""
    project = await ProjectService.get_project_by_id(session, project_id, user_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if not project.canister_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project has no deployed canister",
        )

    try:
        result = await CanisterFactory.set_canister_power(session, project, body.enabled)
        await session.commit()
        return {
            **result,
            "canister_network": network_for_canister(project.canister_id),
            "is_local_canister": is_local_canister_id(project.canister_id),
        }
    except Exception as e:
        await session.rollback()
        parsed = parse_dfx_error(str(e))
        status_code = status.HTTP_502_BAD_GATEWAY
        if parsed.get("error_code") == "canister_not_found":
            status_code = status.HTTP_404_NOT_FOUND
        elif parsed.get("error_code") == "network_unreachable":
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        raise HTTPException(
            status_code=status_code,
            detail=http_error_detail(e, fallback="Failed to change canister power state", debug=settings.debug),
        )


@router.post("/projects/{project_id}/update-canister")
async def update_canister(
    project_id: int,
    deploy_request: ProjectDeployRequest,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Update an existing project's canister with new content.

    Only works if the project already has a deployed canister.
    """
    # Get project and verify ownership
    project = await ProjectService.get_project_by_id(session, project_id, user_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if not project.canister_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project has no deployed canister. Deploy first.",
        )

    try:
        # Use provided code or existing project code
        code_content = deploy_request.code_content or project.code_content or ""

        if not code_content.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No code content provided for update",
            )

        # Update the canister
        result = await CanisterFactory.update_project_canister(
            session=session,
            project=project,
            html_content=code_content,
        )

        await session.commit()

        return {
            "canister_id": result["canister_id"],
            "url": result["url"],
            "status": result["status"],
            "message": "Canister updated successfully",
        }

    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Canister update failed: {safe_error_detail(e, fallback='Canister update failed')}",
        )


@router.delete("/projects/{project_id}/canister")
async def delete_canister(
    project_id: int,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Delete a project's canister from ICP.

    This removes the canister from the blockchain and clears the project's
    canister references.
    """
    # Get project and verify ownership
    project = await ProjectService.get_project_by_id(session, project_id, user_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if not project.canister_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project has no deployed canister",
        )

    try:
        # Delete the canister
        await CanisterFactory.delete_project_canister(
            session=session,
            project=project,
        )

        await session.commit()

        return {
            "message": f"Canister {project.canister_id} deleted successfully",
            "project_id": project_id,
        }

    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Canister deletion failed: {str(e)}",
        )
