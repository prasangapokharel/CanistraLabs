"""
API endpoint for dynamic project deployment.
Integrates with the automatic funding detection system.
"""

from typing import Annotated, Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.config import settings
from app.database.db import get_db
from app.models.project import Project
from app.models.user import User
from app.api.deps import get_current_user_id
from app.services.auth import AuthService
from app.services.dynamicDeployment import DeploymentConfig, DynamicDeploymentService
from app.utils.http_errors import safe_error_detail

router = APIRouter(prefix="/api/v1/deploy", tags=["Dynamic Deployment"])


@router.post("/project/{project_id}")
async def deploy_project_dynamically(
    project_id: int,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> Dict[str, Any]:
    """Deploy a project to ICP using the authenticated user's identity."""
    try:
        result = await session.execute(
            select(Project).where(Project.id == project_id, Project.user_id == user.id)
        )
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if not project.code_content or not project.code_content.strip():
            raise HTTPException(status_code=400, detail="Project has no content to deploy")

        if not user.dfx_identity_name:
            raise HTTPException(status_code=400, detail="User has no dfx identity configured")

        config = DeploymentConfig(
            project_id=project.id,
            project_name=project.name,
            content=project.code_content,
            content_type=project.language or "html",
            identity=user.dfx_identity_name,
        )

        deployment_service = DynamicDeploymentService(network=settings.dfx_network)
        deployment_result = await deployment_service.deploy_project(config)
        db_updated = await deployment_service.update_project_database(
            session, project_id, deployment_result
        )

        if deployment_result["success"] and db_updated:
            return {
                "success": True,
                "message": "Project deployed successfully",
                "project_id": project_id,
                "canister_id": deployment_result["canister_id"],
                "url": deployment_result["url"],
                "deployment_details": deployment_result,
            }

        return {
            "success": False,
            "message": "Deployment failed",
            "project_id": project_id,
            "error": deployment_result.get("error", "Unknown error"),
            "stage": deployment_result.get("stage", "unknown"),
            "deployment_details": deployment_result,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=safe_error_detail(e, fallback="Internal deployment error"),
        )


@router.post("/auto-deploy-funded-projects", dependencies=[Depends(require_admin)])
async def auto_deploy_funded_projects(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> Dict[str, Any]:
    """Automatically deploy pending projects for funded users (admin/internal only)."""
    try:
        from app.services.dfxCommand import DfxCommand

        result = await session.execute(
            select(Project)
            .join(User)
            .where(
                Project.status == "pending",
                Project.code_content.isnot(None),
                User.dfx_identity_name.isnot(None),
            )
        )
        projects = result.scalars().all()

        deployment_results = []
        dfx = DfxCommand(network=settings.dfx_network)

        for project in projects:
            try:
                owner = project.owner
                identity = owner.dfx_identity_name
                status_data = dfx.getUserStatus(identity)
                cycles_balance = status_data.get("cycles", {}).get("balanceTc", 0)

                if cycles_balance >= 1.0:
                    config = DeploymentConfig(
                        project_id=project.id,
                        project_name=project.name,
                        content=project.code_content,
                        content_type=project.language or "html",
                        identity=identity,
                    )
                    deployment_service = DynamicDeploymentService(network=settings.dfx_network)
                    deployment_result = await deployment_service.deploy_project(config)

                    if deployment_result["success"]:
                        await deployment_service.update_project_database(
                            session, project.id, deployment_result
                        )
                        deployment_results.append(
                            {
                                "project_id": project.id,
                                "project_name": project.name,
                                "user_id": owner.id,
                                "status": "deployed",
                                "canister_id": deployment_result["canister_id"],
                                "url": deployment_result["url"],
                            }
                        )
                    else:
                        deployment_results.append(
                            {
                                "project_id": project.id,
                                "project_name": project.name,
                                "user_id": owner.id,
                                "status": "failed",
                                "error": deployment_result.get("error", "Unknown error"),
                            }
                        )
                else:
                    deployment_results.append(
                        {
                            "project_id": project.id,
                            "project_name": project.name,
                            "user_id": owner.id,
                            "status": "insufficient_cycles",
                            "cycles_balance": cycles_balance,
                        }
                    )
            except Exception as e:
                deployment_results.append(
                    {
                        "project_id": project.id,
                        "project_name": getattr(project, "name", "unknown"),
                        "user_id": getattr(owner, "id", "unknown"),
                        "status": "error",
                        "error": safe_error_detail(e),
                    }
                )

        return {
            "success": True,
            "message": f"Processed {len(projects)} pending projects",
            "deployments": deployment_results,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=safe_error_detail(e, fallback="Auto-deployment error"),
        )
