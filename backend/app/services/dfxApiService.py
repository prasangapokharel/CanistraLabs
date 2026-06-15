"""Service layer for unified dfx API — identity context, ownership, command dispatch."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.project import Project
from app.models.user import User
from app.services.auth import AuthService
from app.services.canisterFactory import CanisterFactory
from app.services.dfxCommand import DfxCommand
from app.services.icpIdentityManager import ICPIdentityManager
from app.services.deployment import DeploymentService
from app.utils.canisterNetwork import is_local_canister_id, network_for_canister
from app.utils.cycleRequirements import build_insufficient_cycles_error, deploy_ready
from app.utils.dfxErrors import http_error_detail, parse_dfx_error

logger = logging.getLogger(__name__)


def _serialize_deployment(deployment) -> dict:
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


def _enqueue_deploy_task(project_id: int, deployment_id: int, code_content: str) -> Optional[str]:
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
    deployment,
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
            "command": "dfx deploy (project assets via ICPService)",
        }

    return {
        "deployment_id": deployment.id,
        "project_id": project.id,
        "canister_id": result["canister_id"],
        "url": result["url"],
        "status": result["status"],
        "message": f"Successfully deployed to {result['url']}",
        "async": False,
        "command": "dfx deploy (project assets via ICPService)",
    }


class DfxApiService:
    """Dispatch dfx operations for authenticated users with ownership checks."""

    @staticmethod
    def _dfx(network: Optional[str] = None) -> DfxCommand:
        return DfxCommand(network=network or settings.effective_deploy_network)

    @staticmethod
    async def _user_with_identity(
        session: AsyncSession, user_id: int
    ) -> Tuple[User, str]:
        user = await AuthService.get_user_by_id(session, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if not user.dfx_identity_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No dfx identity — complete wallet setup first",
            )
        return user, user.dfx_identity_name

    @staticmethod
    async def _owned_project(
        session: AsyncSession, project_id: int, user_id: int
    ) -> Project:
        result = await session.execute(
            select(Project).where(Project.id == project_id, Project.user_id == user_id)
        )
        project = result.scalar_one_or_none()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
            )
        return project

    @staticmethod
    async def _verify_canister_owner(
        session: AsyncSession, canister_id: str, user_id: int
    ) -> Project:
        result = await session.execute(
            select(Project).where(
                Project.canister_id == canister_id, Project.user_id == user_id
            )
        )
        project = result.scalar_one_or_none()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Canister not found or not owned by you",
            )
        return project

    @staticmethod
    def _wrap(result: Dict[str, Any], command: str) -> Dict[str, Any]:
        payload = {"command": command, "result": result}
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=payload,
            )
        return payload

    @classmethod
    async def run_for_user_identity(
        cls,
        session: AsyncSession,
        user_id: int,
        command: str,
        runner,
    ) -> Dict[str, Any]:
        user, identity = await cls._user_with_identity(session, user_id)
        ICPIdentityManager.switch_to_user_identity(user)
        return cls._wrap(runner(identity), command)

    @classmethod
    async def canister_op(
        cls,
        session: AsyncSession,
        user_id: int,
        canister_id: str,
        command: str,
        runner,
    ) -> Dict[str, Any]:
        project = await cls._verify_canister_owner(session, canister_id, user_id)
        user, identity = await cls._user_with_identity(session, user_id)
        ICPIdentityManager.switch_to_user_identity(user)
        network = network_for_canister(canister_id)
        return cls._wrap(runner(identity, network, project), command)

    @classmethod
    async def deploy_project(
        cls,
        session: AsyncSession,
        user_id: int,
        project_id: int,
        code_content: Optional[str],
    ) -> Dict[str, Any]:
        """Official deploy: dfx asset canister via CanisterFactory (async Celery or sync)."""
        from app.models.deployment import Deployment, DeploymentStatus
        from app.services.auth import AuthService

        project = await cls._owned_project(session, project_id, user_id)
        code = (code_content or project.code_content or "").strip()
        if not code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No code content to deploy",
            )

        if code != (project.code_content or ""):
            project.code_content = code
            await session.flush()

        # Fast funding pre-check (avoid slow dfx when underfunded on mainnet)
        if not project.canister_id:
            user = await AuthService.get_user_by_id(session, user_id)
            if user:
                ctx = await ICPIdentityManager.get_user_identity_context(session, user)
                cycles_balance = int(ctx.get("cycles_balance") or 0)
                if not deploy_ready(cycles_balance):
                    err = build_insufficient_cycles_error(cycles_balance)
                    deployment = Deployment(
                        project_id=project_id,
                        status="pending_funding",
                        message=err["message"],
                    )
                    session.add(deployment)
                    await session.flush()
                    await session.commit()
                    return {
                        "deployment_id": deployment.id,
                        "project_id": project_id,
                        "canister_id": None,
                        "url": None,
                        "status": "pending_funding",
                        "message": err["message"],
                        "principal_id": ctx.get("principal_id"),
                        "cycles_balance": str(cycles_balance),
                        "funding_required": True,
                        "can_retry": True,
                        "async": False,
                        "error_code": err["error_code"],
                        "cycles_required": err["cycles_required"],
                        "cycles_shortfall": err["cycles_shortfall"],
                        "recommended_icp": err["recommended_icp"],
                        "action": err["action"],
                        "command": "dfx deploy (project assets via ICPService)",
                    }

        deployment = Deployment(
            project_id=project_id,
            status=DeploymentStatus.QUEUED.value,
            message="Queued for deployment…",
        )
        session.add(deployment)
        await session.flush()

        task_id = _enqueue_deploy_task(project_id, deployment.id, code)
        if task_id:
            deployment.task_id = task_id
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
                "command": "dfx deploy (project assets via ICPService)",
            }

        deployment.status = DeploymentStatus.PENDING.value
        deployment.message = "Creating individual canister…"
        await session.flush()
        return await _run_sync_deploy(session, project, deployment, code)

    @classmethod
    async def update_project(
        cls,
        session: AsyncSession,
        user_id: int,
        project_id: int,
        code_content: Optional[str],
    ) -> Dict[str, Any]:
        """Redeploy assets to existing canister (dfx deploy reinstall)."""
        project = await cls._owned_project(session, project_id, user_id)
        if not project.canister_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project has no deployed canister. Deploy first.",
            )
        code = (code_content or project.code_content or "").strip()
        if not code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No code content provided for update",
            )

        result = await CanisterFactory.update_project_canister(
            session=session,
            project=project,
            html_content=code,
        )
        await session.commit()
        return {
            "command": "dfx deploy (update assets)",
            "project_id": project_id,
            "canister_id": result["canister_id"],
            "url": result["url"],
            "status": result["status"],
            "message": "Canister updated successfully",
        }

    @classmethod
    async def get_deployment(
        cls,
        session: AsyncSession,
        user_id: int,
        project_id: int,
        deployment_id: int,
    ) -> Dict[str, Any]:
        await cls._owned_project(session, project_id, user_id)
        deployment = await DeploymentService.get_deployment_status(session, deployment_id)
        if not deployment or deployment.project_id != project_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found")
        return _serialize_deployment(deployment)

    @classmethod
    async def list_deployments(
        cls,
        session: AsyncSession,
        user_id: int,
        project_id: int,
        skip: int = 0,
        limit: int = 10,
    ) -> list:
        await cls._owned_project(session, project_id, user_id)
        deployments = await DeploymentService.get_project_deployments(
            session, project_id, limit=limit, skip=skip
        )
        return [_serialize_deployment(d) for d in deployments]

    @classmethod
    async def project_power(
        cls,
        session: AsyncSession,
        user_id: int,
        project_id: int,
        enabled: bool,
    ) -> Dict[str, Any]:
        project = await cls._owned_project(session, project_id, user_id)
        if not project.canister_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project has no deployed canister",
            )
        cmd = "dfx canister start" if enabled else "dfx canister stop"
        try:
            result = await CanisterFactory.set_canister_power(session, project, enabled)
            await session.commit()
            return {
                "command": cmd,
                "project_id": project_id,
                **result,
                "canister_network": network_for_canister(project.canister_id),
                "is_local_canister": is_local_canister_id(project.canister_id),
            }
        except Exception as e:
            await session.rollback()
            parsed = parse_dfx_error(str(e))
            code = status.HTTP_502_BAD_GATEWAY
            if parsed.get("error_code") == "canister_not_found":
                code = status.HTTP_404_NOT_FOUND
            elif parsed.get("error_code") == "network_unreachable":
                code = status.HTTP_503_SERVICE_UNAVAILABLE
            elif parsed.get("error_code") == "local_replica_down":
                code = status.HTTP_503_SERVICE_UNAVAILABLE
            raise HTTPException(
                status_code=code,
                detail=http_error_detail(
                    e, fallback="Failed to change canister power state", debug=settings.debug
                ),
            ) from e

    @classmethod
    async def delete_project_canister(
        cls,
        session: AsyncSession,
        user_id: int,
        project_id: int,
    ) -> Dict[str, Any]:
        project = await cls._owned_project(session, project_id, user_id)
        if not project.canister_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project has no deployed canister",
            )
        canister_id = project.canister_id
        await CanisterFactory.delete_project_canister(session, project)
        await session.commit()
        return {
            "command": "dfx canister delete --yes",
            "project_id": project_id,
            "canister_id": canister_id,
            "success": True,
        }
