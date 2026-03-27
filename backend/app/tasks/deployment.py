"""Deployment-related Celery tasks."""

from sqlalchemy import select

from app.database.db import async_session_maker
from app.models.deployment import Deployment, DeploymentStatus
from app.models.project import Project, ProjectStatus
from app.tasks.celeryApp import celery_app


@celery_app.task(bind=True, name="tasks.deploy_project")
async def deploy_project_task(self, project_id: int, deployment_id: int) -> dict:
    """Deploy a project to ICP canister."""
    async with async_session_maker() as session:
        try:
            # Get deployment record
            stmt = select(Deployment).where(Deployment.id == deployment_id)
            result = await session.execute(stmt)
            deployment = result.scalars().first()

            if not deployment:
                return {"status": "failed", "error": "Deployment not found"}

            # Update status to running
            deployment.status = DeploymentStatus.RUNNING
            await session.flush()

            # Get project
            stmt = select(Project).where(Project.id == project_id)
            result = await session.execute(stmt)
            project = result.scalars().first()

            if not project:
                return {"status": "failed", "error": "Project not found"}

            # TODO: Implement actual ICP deployment logic
            # For now, mark as success
            deployment.status = DeploymentStatus.SUCCESS
            project.status = ProjectStatus.ACTIVE
            await session.commit()

            return {
                "status": "success",
                "project_id": project_id,
                "deployment_id": deployment_id,
            }

        except Exception as e:
            deployment.status = DeploymentStatus.FAILED
            deployment.error_message = str(e)
            await session.commit()
            raise


@celery_app.task(name="tasks.check_canister_status")
async def check_canister_status_task(project_id: int) -> dict:
    """Check the status of a deployed canister."""
    async with async_session_maker() as session:
        try:
            stmt = select(Project).where(Project.id == project_id)
            result = await session.execute(stmt)
            project = result.scalars().first()

            if not project:
                return {"status": "failed", "error": "Project not found"}

            # TODO: Implement actual canister status check
            return {"status": "active", "cycles": "1000000"}

        except Exception as e:
            return {"status": "error", "error": str(e)}
