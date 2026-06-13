"""Deployment-related Celery tasks."""

import asyncio
import logging
from datetime import datetime

from sqlalchemy import select

from app.database.db import async_session_maker
from app.models.deployment import Deployment, DeploymentStatus
from app.models.project import Project
from app.services.canisterFactory import CanisterFactory
from app.tasks.celeryApp import celery_app

logger = logging.getLogger(__name__)

TERMINAL_STATUSES = {
    DeploymentStatus.SUCCESS.value,
    DeploymentStatus.FAILED.value,
    "success",
    "failed",
    "pending_funding",
}


def _run_async(coro):
    return asyncio.run(coro)


async def _execute_project_deploy(
    project_id: int,
    deployment_id: int,
    code_content: str,
) -> dict:
    async with async_session_maker() as session:
        stmt = select(Deployment).where(Deployment.id == deployment_id)
        result = await session.execute(stmt)
        deployment = result.scalars().first()
        if not deployment:
            return {"status": "failed", "error": "Deployment not found"}

        stmt = select(Project).where(Project.id == project_id)
        result = await session.execute(stmt)
        project = result.scalars().first()
        if not project:
            deployment.status = DeploymentStatus.FAILED.value
            deployment.message = "Project not found"
            deployment.completed_at = datetime.utcnow()
            await session.commit()
            return {"status": "failed", "error": "Project not found"}

        deployment.status = DeploymentStatus.RUNNING.value
        deployment.started_at = datetime.utcnow()
        deployment.message = "Deploying to ICP…"
        await session.flush()

        if code_content.strip():
            project.code_content = code_content
            await session.flush()

        try:
            result = await CanisterFactory.create_project_canister(
                session=session,
                project=project,
                html_content=code_content,
                deployment=deployment,
            )

            if result.get("status") == "pending_funding":
                deployment.status = "pending_funding"
                deployment.message = result.get(
                    "message", "Wallet funding required before deploy"
                )
                deployment.completed_at = datetime.utcnow()
                await session.commit()
                return {
                    "status": "pending_funding",
                    "deployment_id": deployment_id,
                    "project_id": project_id,
                }

            await session.commit()
            return {
                "status": deployment.status,
                "deployment_id": deployment_id,
                "project_id": project_id,
                "canister_id": result.get("canister_id"),
                "url": result.get("url"),
            }

        except Exception as exc:
            logger.exception("Async deploy failed for project %s: %s", project_id, exc)
            await session.rollback()
            async with async_session_maker() as err_session:
                stmt = select(Deployment).where(Deployment.id == deployment_id)
                result = await err_session.execute(stmt)
                deployment = result.scalars().first()
                if deployment:
                    deployment.status = DeploymentStatus.FAILED.value
                    deployment.message = f"Deployment failed: {exc}"
                    deployment.error_message = str(exc)
                    deployment.completed_at = datetime.utcnow()
                    await err_session.commit()
            raise


@celery_app.task(bind=True, name="tasks.run_project_deploy", max_retries=0)
def run_project_deploy_task(
    self,
    project_id: int,
    deployment_id: int,
    code_content: str,
) -> dict:
    """Run project canister deploy in a background worker."""
    return _run_async(_execute_project_deploy(project_id, deployment_id, code_content))


@celery_app.task(bind=True, name="tasks.deploy_project")
def deploy_project_task(self, project_id: int, deployment_id: int) -> dict:
    """Legacy task name — loads code from project record."""
    async def _load_and_deploy() -> dict:
        async with async_session_maker() as session:
            stmt = select(Project).where(Project.id == project_id)
            result = await session.execute(stmt)
            project = result.scalars().first()
            code = project.code_content if project else ""
        return await _execute_project_deploy(project_id, deployment_id, code or "")

    return _run_async(_load_and_deploy())


@celery_app.task(name="tasks.check_canister_status")
def check_canister_status_task(project_id: int) -> dict:
    """Check canister status for a project."""
    from app.services.canisterMetrics import fetch_canister_metrics

    async def _check() -> dict:
        async with async_session_maker() as session:
            stmt = select(Project).where(Project.id == project_id)
            result = await session.execute(stmt)
            project = result.scalars().first()
            if not project or not project.canister_id:
                return {"status": "not_deployed"}
            metrics = fetch_canister_metrics(project.canister_id, project.url)
            return {"status": metrics.get("status"), "metrics": metrics}

    return _run_async(_check())
