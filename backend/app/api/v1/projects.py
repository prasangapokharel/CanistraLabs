"""Projects API routes."""

from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.schemas.project import (
    ProjectCreate,
    ProjectDetailResponse,
    ProjectResponse,
    ProjectUpdate,
)
from app.services.auth import AuthService
from app.services.projects import ProjectService
from app.utils.security import verify_token

router = APIRouter(prefix="/api/v1/projects", tags=["Projects"])


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


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_create: ProjectCreate,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectResponse:
    """Create a new project."""
    project = await ProjectService.create_project(session, user_id, project_create)
    await session.commit()
    return ProjectResponse.model_validate(project)


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 10,
) -> List[ProjectResponse]:
    """List all projects for the current user."""
    projects = await ProjectService.get_user_projects(session, user_id, skip, limit)
    return [ProjectResponse.model_validate(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(
    project_id: int,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectDetailResponse:
    """Get a specific project with full details."""
    project = await ProjectService.get_project_by_id(session, project_id, user_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return ProjectDetailResponse.model_validate(project)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectResponse:
    """Update a project."""
    project = await ProjectService.get_project_by_id(session, project_id, user_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    updated_project = await ProjectService.update_project(session, project, project_update)
    await session.commit()
    return ProjectResponse.model_validate(updated_project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a project."""
    project = await ProjectService.get_project_by_id(session, project_id, user_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    await ProjectService.delete_project(session, project)
    await session.commit()
