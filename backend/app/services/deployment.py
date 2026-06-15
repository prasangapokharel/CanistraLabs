"""Deployment record queries (DB only). Deploy/update/delete run via DfxApiService + CanisterFactory."""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.canister import Canister
from app.models.deployment import Deployment
from app.utils.icpUtils import ICPService, ICPError


class DeploymentService:
    """Read deployment history and canister status from DB / ICP."""

    @staticmethod
    async def get_deployment_status(
        session: AsyncSession,
        deployment_id: int,
    ) -> Optional[Deployment]:
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
        canister_id: str,
    ) -> dict:
        try:
            return ICPService.get_canister_status(canister_id)
        except ICPError:
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
