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
from app.services.autoFundingDetector import AutoFundingDetector
from app.config import settings
from app.utils.cycleRequirements import (
    build_insufficient_cycles_error,
    deploy_ready,
    min_cycles_for_deploy,
)

logger = logging.getLogger(__name__)


class CanisterFactory:
    """Factory for creating individual canisters for each project."""

    @staticmethod
    async def _ensure_cycles_for_deploy(session: AsyncSession, user: User) -> None:
        """Auto-convert ICP/TESTICP balance to cycles when user has tokens but low cycles."""
        detector = AutoFundingDetector()
        funding = await detector.check_user_funding_status(session, user)
        if funding.get("auto_convert_available"):
            logger.info(f"Auto-converting token balance to cycles for user {user.id}")
            await detector.auto_convert_icp_to_cycles(session, user)
            await ICPIdentityManager.check_wallet_balance(user)

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

        # Auto-convert deposited ICP to cycles before checking funding (production UX)
        await CanisterFactory._ensure_cycles_for_deploy(session, user)
        identity_context = await ICPIdentityManager.get_user_identity_context(session, user)

        # Check if user has sufficient cycles for deploy (mainnet needs ~600B+)
        cycles_balance = int(identity_context.get("cycles_balance") or 0)
        if not deploy_ready(cycles_balance):
            err = build_insufficient_cycles_error(cycles_balance)
            logger.warning(
                "User %s underfunded for %s deploy: %s cycles (need %s)",
                user.id,
                settings.effective_deploy_network,
                cycles_balance,
                min_cycles_for_deploy(),
            )
            if deployment:
                deployment.status = "pending_funding"
                deployment.message = err["message"]
                await session.flush()

            return {
                "status": "pending_funding",
                "principal_id": identity_context["principal_id"],
                "funding_required": True,
                "cycles_balance": str(cycles_balance),
                "message": err["message"],
                "error_code": err["error_code"],
                "cycles_required": err["cycles_required"],
                "cycles_shortfall": err["cycles_shortfall"],
                "recommended_icp": err["recommended_icp"],
                "action": err["action"],
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
                available_cycles=cycles_balance,
            )

            canister_id = result["canister_id"]
            canister_url = result["url"]

            logger.info(f"Canister created successfully: {canister_id}")

            # One canister row per project; principal_id is shared across a user's canisters
            stmt = select(Canister).where(Canister.project_id == project.id)
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
                logger.info(f"Created new Canister record for project {project.id}")
            else:
                canister_record.canister_name = canister_id
                canister_record.principal_id = identity_context["principal_id"]
                canister_record.status = "deployed"
                canister_record.cycles_balance = identity_context["cycles_balance"]
                canister_record.updated_at = datetime.utcnow()
                logger.info(f"Updated Canister record for project {project.id}")

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
            raise

        except ICPError as e:
            logger.error(f"ICP error during canister creation: {str(e)}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error during canister creation: {str(e)}")
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

        canister_id = project.canister_id

        try:
            logger.info(f"Deleting canister {canister_id} for project {project.id}")

            stmt = select(User).where(User.id == project.user_id)
            result = await session.execute(stmt)
            user = result.scalars().first()
            if user and user.dfx_identity_name:
                ICPIdentityManager.switch_to_user_identity(user)

            ICPService.delete_canister(canister_id)

            stmt = select(Canister).where(Canister.project_id == project.id)
            db_result = await session.execute(stmt)
            canister_record = db_result.scalars().first()

            if canister_record:
                await session.delete(canister_record)

            project.canister_id = None
            project.url = None
            project.status = ProjectStatus.PENDING.value
            project.deployed_at = None

            await session.flush()

            logger.info(f"Successfully deleted canister {canister_id}")
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

        stmt = select(User).where(User.id == project.user_id)
        result = await session.execute(stmt)
        user = result.scalars().first()
        if not user:
            raise CanisterCreationException("Project owner not found")

        try:
            logger.info(f"Updating canister {project.canister_id} for project {project.id}")

            ICPIdentityManager.switch_to_user_identity(user)
            await CanisterFactory._ensure_cycles_for_deploy(session, user)

            old_canister_id = project.canister_id
            result = ICPService.update_canister(
                canister_id=project.canister_id,
                code_content=html_content,
            )

            new_canister_id = result.get("canister_id")
            replaced_stale = bool(
                new_canister_id and new_canister_id != old_canister_id
            )
            if replaced_stale:
                logger.info(
                    "Replacing stale canister %s with %s for project %s",
                    old_canister_id,
                    new_canister_id,
                    project.id,
                )
                project.canister_id = new_canister_id

            if result.get("url"):
                project.url = result["url"]

            # Update project's deployment timestamp
            project.deployed_at = datetime.utcnow()
            await session.flush()

            logger.info(f"Successfully updated canister {project.canister_id}")

            return {
                "canister_id": project.canister_id,
                "url": project.url,
                "status": result.get("status", "updated"),
                "updated_at": datetime.utcnow().isoformat(),
                "replaced_stale_canister": replaced_stale,
            }

        except ICPError as e:
            logger.error(f"Failed to update canister: {str(e)}")
            raise

    @staticmethod
    async def set_canister_power(
        session: AsyncSession,
        project: Project,
        enabled: bool,
    ) -> Dict[str, Any]:
        """Start or stop the project's canister on ICP."""
        if not project.canister_id:
            raise CanisterCreationException("Project has no deployed canister")

        stmt = select(User).where(User.id == project.user_id)
        result = await session.execute(stmt)
        user = result.scalars().first()
        if user and user.dfx_identity_name:
            ICPIdentityManager.switch_to_user_identity(user)

        try:
            if enabled:
                ICPService.start_canister(project.canister_id)
                project.status = ProjectStatus.ACTIVE.value
                icp_status = "running"
            else:
                ICPService.stop_canister(project.canister_id)
                project.status = ProjectStatus.PAUSED.value
                icp_status = "stopped"
        except ICPError as e:
            from app.utils.dfxErrors import parse_dfx_error

            parsed = parse_dfx_error(str(e))
            raise ICPError(parsed.get("message", str(e))) from e

        stmt = select(Canister).where(Canister.project_id == project.id)
        db_result = await session.execute(stmt)
        canister_record = db_result.scalars().first()
        if canister_record:
            canister_record.status = "active" if enabled else "stopped"
            canister_record.updated_at = datetime.utcnow()

        await session.flush()

        return {
            "project_id": project.id,
            "canister_id": project.canister_id,
            "enabled": enabled,
            "status": project.status,
            "canister_status": icp_status,
        }
