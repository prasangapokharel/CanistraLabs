"""Factory for creating and managing individual project canisters."""

import logging
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.project import Project, ProjectStatus
from app.models.canister import Canister
from app.models.deployment import Deployment
from app.models.user import User
from app.utils.icpUtils import ICPService, ICPError, CanisterCreationException
from app.services.icpIdentityManager import ICPIdentityManager
from app.config import settings

logger = logging.getLogger(__name__)


class CanisterFactory:
    """Factory for creating individual canisters for each project."""

    @staticmethod
    async def create_project_canister(
        session: AsyncSession,
        project: Project,
        html_content: str,
        deployment: Optional[Deployment] = None,
    ) -> Dict[str, Any]:
        """
        Create a unique canister for a project using the user's ICP identity.

        This automatically switches to the user's identity and creates an individual canister.
        Each project gets its own unique canister on IC mainnet using the user's cycles.

        Args:
            session: Database session
            project: Project instance to create canister for
            html_content: HTML content to serve from the canister
            deployment: Optional Deployment record to update with status

        Returns:
            Dictionary with canister creation result containing:
            - canister_id: Unique canister identifier
            - url: Public URL for the canister
            - principal_id: Principal ID of the owner
            - status: Deployment status
            - funding_required: Whether user needs to fund wallet

        Raises:
            CanisterCreationException: If canister creation fails
            ICPError: If ICP communication fails
        """
        logger.info(f"Creating individual canister for project: {project.name} (ID: {project.id})")

        # Get the project owner
        stmt = select(User).where(User.id == project.user_id)
        result = await session.execute(stmt)
        user = result.scalars().first()

        if not user:
            raise CanisterCreationException("Project owner not found")

        # Get or create user's ICP identity
        identity_context = await ICPIdentityManager.get_user_identity_context(session, user)

        # Check if user has sufficient cycles
        if identity_context.get("funding_required", True):
            logger.warning(f"User {user.id} needs to fund wallet for deployment")
            if deployment:
                deployment.status = "pending_funding"
                deployment.message = (
                    f"Wallet funding required. Principal ID: {identity_context['principal_id']}"
                )
                await session.flush()

            return {
                "status": "pending_funding",
                "principal_id": identity_context["principal_id"],
                "funding_required": True,
                "cycles_balance": identity_context["cycles_balance"],
                "message": "Please fund your ICP wallet to continue deployment",
            }

        # Update deployment status if provided
        if deployment:
            deployment.status = "in_progress"
            deployment.message = (
                f"Creating canister with identity {identity_context['identity_name']}..."
            )
            await session.flush()

        try:
            # Switch to user's identity
            ICPIdentityManager.switch_to_user_identity(user)

            # Call the ICP service to create the individual canister
            result = ICPService.create_individual_canister(
                project_name=project.name,
                html_content=html_content,
            )

            canister_id = result["canister_id"]
            canister_url = result["url"]

            logger.info(f"Canister created successfully: {canister_id}")

            # Create or update the Canister model record
            stmt = select(Canister).where(Canister.canister_name == canister_id)
            db_result = await session.execute(stmt)
            canister_record = db_result.scalars().first()

            if not canister_record:
                canister_record = Canister(
                    project_id=project.id,
                    canister_name=canister_id,
                    principal_id=identity_context["principal_id"],
                    status="deployed",
                    cycles_balance=identity_context["cycles_balance"],
                )
                session.add(canister_record)
                logger.info(f"Created new Canister record for {canister_id}")
            else:
                canister_record.status = "deployed"
                canister_record.updated_at = datetime.utcnow()
                logger.info(f"Updated existing Canister record for {canister_id}")

            # Update the Project record with canister information
            project.canister_id = canister_id
            project.principal_id = identity_context["principal_id"]
            project.url = canister_url
            project.status = ProjectStatus.ACTIVE.value
            project.deployed_at = datetime.utcnow()

            # Update deployment record if provided
            if deployment:
                deployment.status = "success"
                deployment.message = f"Successfully deployed to {canister_url}"
                deployment.canister_id = canister_id
                deployment.deployment_url = canister_url
                deployment.completed_at = datetime.utcnow()

            await session.flush()

            # Update user's cached cycles balance
            new_balance = await ICPIdentityManager.check_wallet_balance(user)
            await session.flush()

            logger.info(f"Project {project.id} deployment complete: {canister_url}")

            return {
                "canister_id": canister_id,
                "url": canister_url,
                "principal_id": identity_context["principal_id"],
                "status": "deployed",
                "funding_required": False,
                "cycles_balance": new_balance,
                "html_size_bytes": result.get("html_size_bytes", 0),
                "network": result.get("network", "ic"),
            }

        except CanisterCreationException as e:
            logger.error(f"Canister creation failed: {str(e)}")

            # Update project and deployment with failure status
            project.status = ProjectStatus.FAILED.value
            if deployment:
                deployment.status = "failed"
                deployment.message = f"Canister creation failed: {str(e)}"
                deployment.error_details = str(e)
                deployment.completed_at = datetime.utcnow()

            await session.flush()
            raise

        except ICPError as e:
            logger.error(f"ICP error during canister creation: {str(e)}")

            project.status = ProjectStatus.FAILED.value
            if deployment:
                deployment.status = "failed"
                deployment.message = f"ICP error: {str(e)}"
                deployment.error_details = str(e)
                deployment.completed_at = datetime.utcnow()

            await session.flush()
            raise

        except Exception as e:
            logger.error(f"Unexpected error during canister creation: {str(e)}")

            project.status = ProjectStatus.FAILED.value
            if deployment:
                deployment.status = "failed"
                deployment.message = f"Unexpected error: {str(e)}"
                deployment.error_details = str(e)
                deployment.completed_at = datetime.utcnow()

            await session.flush()
            raise CanisterCreationException(f"Unexpected error: {str(e)}")

    @staticmethod
    async def get_or_create_canister(
        session: AsyncSession,
        project: Project,
    ) -> Optional[Dict[str, Any]]:
        """
        Get existing canister info or return None if not created.

        Args:
            session: Database session
            project: Project to check canister for

        Returns:
            Dictionary with canister info, or None if no canister exists

        Raises:
            ICPError: If ICP status check fails
        """
        if not project.canister_id:
            logger.debug(f"Project {project.id} has no canister yet")
            return None

        try:
            # Try to get status from ICP
            status = ICPService.get_canister_status(project.canister_id)

            return {
                "canister_id": project.canister_id,
                "url": project.url,
                "status": status.get("status", "deployed"),
                "cycles": status.get("cycles", 0),
            }

        except ICPError as e:
            logger.warning(f"Could not retrieve canister status from ICP: {e}")
            # Return cached info from database
            return {
                "canister_id": project.canister_id,
                "url": project.url,
                "status": project.status,
            }

    @staticmethod
    async def delete_project_canister(
        session: AsyncSession,
        project: Project,
    ) -> bool:
        """
        Delete a project's canister from IC.

        Args:
            session: Database session
            project: Project whose canister should be deleted

        Returns:
            True if deletion was successful, False otherwise

        Raises:
            ICPError: If deletion fails
        """
        if not project.canister_id:
            logger.warning(f"Project {project.id} has no canister to delete")
            return False

        try:
            logger.info(f"Deleting canister {project.canister_id} for project {project.id}")

            # Delete from IC
            ICPService.delete_canister(project.canister_id)

            # Update database records
            stmt = select(Canister).where(Canister.canister_name == project.canister_id)
            result = await session.execute(stmt)
            canister_record = result.scalars().first()

            if canister_record:
                canister_record.status = "deleted"
                canister_record.updated_at = datetime.utcnow()

            # Clear project's canister references
            project.canister_id = None
            project.principal_id = None
            project.url = None
            project.status = ProjectStatus.PENDING.value

            await session.flush()

            logger.info(f"Successfully deleted canister {project.canister_id}")
            return True

        except ICPError as e:
            logger.error(f"Failed to delete canister: {str(e)}")
            raise

    @staticmethod
    async def update_project_canister(
        session: AsyncSession,
        project: Project,
        html_content: str,
    ) -> Dict[str, Any]:
        """
        Update an existing project's canister with new HTML content.

        Args:
            session: Database session
            project: Project whose canister should be updated
            html_content: New HTML content to deploy

        Returns:
            Dictionary with update result

        Raises:
            CanisterCreationException: If project has no canister
            ICPError: If update fails
        """
        if not project.canister_id:
            raise CanisterCreationException(
                f"Project {project.id} has no canister to update. Create one first."
            )

        try:
            logger.info(f"Updating canister {project.canister_id} for project {project.id}")

            # Generate new Motoko code
            motoko_code = ICPService._generate_html_serving_motoko(html_content)

            # Update the canister with new code
            result = ICPService.update_canister(
                canister_id=project.canister_id,
                code_content=motoko_code,
            )

            # Update project's deployment timestamp
            project.deployed_at = datetime.utcnow()
            await session.flush()

            logger.info(f"Successfully updated canister {project.canister_id}")

            return {
                "canister_id": project.canister_id,
                "url": project.url,
                "status": result.get("status", "updated"),
                "updated_at": datetime.utcnow().isoformat(),
            }

        except ICPError as e:
            logger.error(f"Failed to update canister: {str(e)}")
            raise
