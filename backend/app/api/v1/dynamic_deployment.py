"""
API endpoint for dynamic project deployment.
Integrates with the automatic funding detection system.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.database.db import get_db
from app.services.dynamic_deployment import DynamicDeploymentService, DeploymentConfig
from app.services.auth import AuthService
from app.models.project import Project
from sqlalchemy import select

router = APIRouter(prefix="/api/v1/deploy", tags=["Dynamic Deployment"])


@router.post("/project/{project_id}")
async def deploy_project_dynamically(
    project_id: int,
    user_id: int,  # This would come from authentication
    session: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Dynamically deploy a project to ICP with full automation.

    This endpoint:
    1. Gets project from database
    2. Verifies user ownership
    3. Gets user's dfx identity
    4. Automatically creates canister and deploys project
    5. Updates database with deployment results
    """
    try:
        # Get project and verify ownership
        result = await session.execute(
            select(Project).where(Project.id == project_id, Project.user_id == user_id)
        )
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if not project.code_content or not project.code_content.strip():
            raise HTTPException(status_code=400, detail="Project has no content to deploy")

        # Get user's dfx identity
        user = await AuthService.get_user_by_id(session, user_id)
        if not user or not user.dfx_identity_name:
            raise HTTPException(status_code=400, detail="User has no dfx identity configured")

        # Create deployment configuration
        config = DeploymentConfig(
            project_id=project.id,
            project_name=project.name,
            content=project.code_content,
            content_type=project.language or "html",
            identity=user.dfx_identity_name,
        )

        # Initialize deployment service
        deployment_service = DynamicDeploymentService(network="ic")

        # Deploy project
        deployment_result = await deployment_service.deploy_project(config)

        # Update database
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
        else:
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
        raise HTTPException(status_code=500, detail=f"Internal deployment error: {str(e)}")


@router.post("/auto-deploy-funded-projects")
async def auto_deploy_funded_projects(session: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Automatically deploy projects for users who have sufficient funding.
    This can be called by the funding detection system.
    """
    try:
        from app.services.dfxCommand import DfxCommand

        # Get all pending projects with users who have identities
        from app.models.user import User

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
        dfx = DfxCommand(network="ic")

        for project in projects:
            try:
                user = project.owner
                identity = user.dfx_identity_name

                # Check if user has sufficient cycles (at least 1 TC for deployment)
                status = dfx.getUserStatus(identity)
                cycles_balance = status.get("cycles", {}).get("balanceTc", 0)

                if cycles_balance >= 1.0:  # Has at least 1 TC
                    # Deploy this project
                    config = DeploymentConfig(
                        project_id=project.id,
                        project_name=project.name,
                        content=project.code_content,
                        content_type=project.language or "html",
                        identity=identity,
                    )

                    deployment_service = DynamicDeploymentService(network="ic")
                    deployment_result = await deployment_service.deploy_project(config)

                    if deployment_result["success"]:
                        await deployment_service.update_project_database(
                            session, project.id, deployment_result
                        )

                        deployment_results.append(
                            {
                                "project_id": project.id,
                                "project_name": project.name,
                                "user_id": user.id,
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
                                "user_id": user.id,
                                "status": "failed",
                                "error": deployment_result.get("error", "Unknown error"),
                            }
                        )
                else:
                    deployment_results.append(
                        {
                            "project_id": project.id,
                            "project_name": project.name,
                            "user_id": user.id,
                            "status": "insufficient_cycles",
                            "cycles_balance": cycles_balance,
                        }
                    )

            except Exception as e:
                deployment_results.append(
                    {
                        "project_id": project.id,
                        "project_name": project.name if project else "unknown",
                        "user_id": user.id if user else "unknown",
                        "status": "error",
                        "error": str(e),
                    }
                )

        return {
            "success": True,
            "message": f"Processed {len(projects)} pending projects",
            "deployments": deployment_results,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Auto-deployment error: {str(e)}")


# Add the router to the main FastAPI app
def setup_dynamic_deployment_routes(app):
    """Setup dynamic deployment routes in the main app."""
    app.include_router(router)
