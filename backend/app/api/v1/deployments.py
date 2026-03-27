"""Deployment API routes."""

from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.schemas.project import ProjectDeployRequest
from app.services.deployment import DeploymentService
from app.services.projects import ProjectService
from app.services.canisterFactory import CanisterFactory
from app.models.deployment import Deployment
from app.utils.security import verify_token

router = APIRouter(prefix="/api/v1/deployments", tags=["Deployments"])


async def get_bearer_token(authorization: Annotated[Optional[str], Header()] = None) -> str:
    """Extract bearer token from Authorization header."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
        )

    return parts[1]


async def get_current_user_id(
    authorization: Annotated[str, Depends(get_bearer_token)],
) -> int:
    """Get current user ID from token."""
    token_data = verify_token(authorization, token_type="access")
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    return int(token_data.sub)


@router.post("/projects/{project_id}/deploy", status_code=status.HTTP_202_ACCEPTED)
async def deploy_project(
    project_id: int,
    deploy_request: ProjectDeployRequest,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Deploy a project to a unique individual ICP canister.

    This creates a new canister for each project with a unique canister ID
    and returns the unique URL for accessing the deployed project.

    Returns 202 Accepted with deployment details including:
    - deployment_id: Deployment record ID
    - canister_id: Unique canister ID for this project
    - url: Public URL to access the deployed project
    - status: Current deployment status
    """
    # Get project and verify ownership
    project = await ProjectService.get_project_by_id(session, project_id, user_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    try:
        # Use project code if deploy request doesn't specify code
        code_content = deploy_request.code_content or project.code_content or ""

        if not code_content.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No code content provided for deployment",
            )

        # Create deployment record
        deployment = Deployment(
            project_id=project_id,
            status="pending",
            message="Creating individual canister...",
        )
        session.add(deployment)
        await session.flush()

        # Create the individual canister using CanisterFactory
        result = await CanisterFactory.create_project_canister(
            session=session,
            project=project,
            html_content=code_content,
            deployment=deployment,
        )

        await session.commit()

        # Handle funding required case
        if result.get("status") == "pending_funding":
            return {
                "deployment_id": deployment.id,
                "project_id": project_id,
                "canister_id": None,
                "url": None,
                "status": "pending_funding",
                "message": result.get("message", "Funding required"),
                "principal_id": result.get("principal_id"),
                "cycles_balance": result.get("cycles_balance", "0"),
                "funding_required": True,
            }

        return {
            "deployment_id": deployment.id,
            "project_id": project_id,
            "canister_id": result["canister_id"],
            "url": result["url"],
            "status": result["status"],
            "message": f"Successfully deployed to {result['url']}",
        }

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deployment failed: {str(e)}",
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
        "started_at": deployment.started_at,
        "completed_at": deployment.completed_at,
        "created_at": deployment.created_at,
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

    return [
        {
            "deployment_id": d.id,
            "status": d.status,
            "message": d.message,
            "created_at": d.created_at,
            "completed_at": d.completed_at,
        }
        for d in deployments
    ]


@router.get("/canisters/{canister_id}/status")
async def get_canister_status(
    canister_id: str,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Get the current status of a canister."""
    try:
        status_info = await DeploymentService.get_canister_status(session, canister_id)
        return status_info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get canister status: {str(e)}",
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
            detail=f"Canister update failed: {str(e)}",
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
