"""Deployment service for managing canister deployments."""

from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.canister import Canister
from app.models.deployment import Deployment
from app.models.project import Project
from app.schemas.project import ProjectDeployRequest
from app.utils.icpUtils import ICPService, ICPError
from app.config import settings


class DeploymentService:
    """Service for managing project deployments to shared ICP canister."""

    # Shared canister ID for all projects (use the portfolio canister from the user's repo)
    SHARED_CANISTER_ID = "uxrrr-q7777-77774-qaaaq-cai"  # Local portfolio canister from dfx deploy

    @staticmethod
    async def deploy_project(
        session: AsyncSession,
        project: Project,
        code_content: str,
    ) -> Deployment:
        """
        Deploy a project to the shared canister.

        All projects are deployed under the shared canister with path-based routing.
        URL format: https://SHARED_CANISTER_ID.ic0.app/project-{project_id}/

        Args:
            session: Database session
            project: Project to deploy
            code_content: Code to deploy (HTML/CSS/JS or Motoko)

        Returns:
            Deployment record

        Raises:
            Exception: If deployment fails
        """
        deployment = Deployment(
            project_id=project.id,
            status="pending",
            message="Starting deployment to shared canister...",
        )
        session.add(deployment)
        await session.flush()

        try:
            # Create deployment path using project name (cleaner URLs)
            project_path = project.name.lower().replace(" ", "-")

            deployment.message = (
                f"Deploying to shared canister {DeploymentService.SHARED_CANISTER_ID}..."
            )
            deployment.canister_id = DeploymentService.SHARED_CANISTER_ID
            deployment.project_path = project_path
            await session.flush()

            # Deploy to shared canister with project-specific path
            ICPService.deploy_to_shared_canister(
                canister_id=DeploymentService.SHARED_CANISTER_ID,
                project_path=project_path,
                code_content=code_content,
            )

            # Get or create canister record
            stmt = select(Canister).where(
                Canister.canister_name == DeploymentService.SHARED_CANISTER_ID
            )
            result = await session.execute(stmt)
            canister = result.scalars().first()

            if not canister:
                canister = Canister(
                    project_id=project.id,
                    canister_name=DeploymentService.SHARED_CANISTER_ID,
                    principal_id=settings.wallet_principal_id,
                    status="deployed",
                )
                session.add(canister)
            else:
                canister.status = "deployed"
                canister.updated_at = datetime.utcnow()

            # Update project with deployment info
            project.canister_id = DeploymentService.SHARED_CANISTER_ID
            project.principal_id = settings.wallet_principal_id
            project.status = "deployed"
            project.deployed_at = datetime.utcnow()

            # Generate public URL using project name
            public_url = f"https://{DeploymentService.SHARED_CANISTER_ID}.ic0.app/{project_path}/"

            # Update deployment status
            deployment.status = "success"
            deployment.message = f"Successfully deployed to {public_url}"
            deployment.deployment_url = public_url
            deployment.completed_at = datetime.utcnow()

            await session.flush()
            return deployment

        except ICPError as e:
            deployment.status = "failed"
            deployment.message = f"Deployment failed: {str(e)}"
            deployment.error_details = str(e)
            deployment.completed_at = datetime.utcnow()

            project.status = "deployment_failed"

            await session.flush()
            raise

        except Exception as e:
            deployment.status = "failed"
            deployment.message = f"Unexpected error during deployment: {str(e)}"
            deployment.error_details = str(e)
            deployment.completed_at = datetime.utcnow()

            project.status = "error"

            await session.flush()
            raise

    @staticmethod
    async def get_deployment_status(
        session: AsyncSession,
        deployment_id: int,
    ) -> Optional[Deployment]:
        """
        Get the status of a deployment.

        Args:
            session: Database session
            deployment_id: Deployment ID

        Returns:
            Deployment record or None if not found
        """
        stmt = select(Deployment).where(Deployment.id == deployment_id)
        result = await session.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def get_project_deployments(
        session: AsyncSession,
        project_id: int,
        limit: int = 10,
        skip: int = 0,
    ) -> list[Deployment]:
        """
        Get deployment history for a project.

        Args:
            session: Database session
            project_id: Project ID
            limit: Maximum number of deployments to return
            skip: Number of deployments to skip

        Returns:
            List of deployment records
        """
        stmt = (
            select(Deployment)
            .where(Deployment.project_id == project_id)
            .order_by(Deployment.created_at.desc())
            .limit(limit)
            .offset(skip)
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_canister_status(
        session: AsyncSession,
        canister_id: Optional[str] = None,
    ) -> dict:
        """
        Get the current status of the shared canister from ICP.

        Args:
            session: Database session
            canister_id: Canister ID (defaults to shared canister)

        Returns:
            Dictionary with canister status

        Raises:
            ICPError: If status check fails
        """
        canister_id = canister_id or DeploymentService.SHARED_CANISTER_ID

        try:
            status = ICPService.get_canister_status(canister_id)
            return status
        except ICPError:
            # Return cached status from database if ICP check fails
            stmt = select(Canister).where(Canister.canister_name == canister_id)
            result = await session.execute(stmt)
            canister = result.scalars().first()

            if canister:
                return {
                    "canister_id": canister.canister_name,
                    "status": canister.status,
                    "cycles": canister.cycles_balance,
                }

            raise
