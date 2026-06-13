"""Projects API routes."""

from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.database.db import get_db
from app.schemas.project import (
    ProjectCreate,
    ProjectDetailResponse,
    ProjectResponse,
    ProjectUpdate,
)
from app.services.projects import ProjectService
from app.utils.http_errors import safe_error_detail

router = APIRouter(prefix="/api/v1/projects", tags=["Projects"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
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


@router.get("", response_model=List[ProjectResponse], include_in_schema=False)
@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 100,
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
    return await _update_project(project_id, project_update, user_id, session)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def patch_project(
    project_id: int,
    project_update: ProjectUpdate,
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectResponse:
    """Partially update a project (alias for PUT)."""
    return await _update_project(project_id, project_update, user_id, session)


async def _update_project(
    project_id: int,
    project_update: ProjectUpdate,
    user_id: int,
    session: AsyncSession,
) -> ProjectResponse:
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
    """Delete a project, its canister on ICP, and all related records."""
    project = await ProjectService.get_project_by_id(session, project_id, user_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    try:
        await ProjectService.delete_project(session, project)
        await session.commit()
    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete project: {safe_error_detail(e, fallback='Delete failed')}",
        )
