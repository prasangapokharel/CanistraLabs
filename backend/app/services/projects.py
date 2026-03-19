"""Project service."""

import hashlib
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.project import Project, ProjectStatus
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    """Project management service."""

    @staticmethod
    def generate_project_url(user_id: int, project_id: int) -> str:
        """Generate auto-formatted project URL."""
        user_hash = hashlib.md5(str(user_id).encode()).hexdigest()[:8]
        return f"https://{user_hash}-{project_id}.ic0.app"

    @staticmethod
    async def create_project(
        session: AsyncSession, user_id: int, project_create: ProjectCreate
    ) -> Project:
        """Create a new project."""
        project = Project(
            user_id=user_id,
            name=project_create.name,
            description=project_create.description,
            language=project_create.language,
            code_content=project_create.code_content,
            status=ProjectStatus.PENDING,
        )
        session.add(project)
        await session.flush()

        # Generate URL after project ID is assigned
        project.url = ProjectService.generate_project_url(user_id, project.id)
        await session.flush()
        return project

    @staticmethod
    async def get_user_projects(
        session: AsyncSession, user_id: int, skip: int = 0, limit: int = 10
    ) -> List[Project]:
        """Get all projects for a user."""
        stmt = (
            select(Project)
            .where(Project.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(Project.created_at.desc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_project_by_id(
        session: AsyncSession, project_id: int, user_id: int
    ) -> Optional[Project]:
        """Get project by ID, verifying user ownership."""
        stmt = select(Project).where((Project.id == project_id) & (Project.user_id == user_id))
        result = await session.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def update_project(
        session: AsyncSession,
        project: Project,
        project_update: ProjectUpdate,
    ) -> Project:
        """Update a project."""
        if project_update.name is not None:
            project.name = project_update.name
        if project_update.description is not None:
            project.description = project_update.description
        if project_update.code_content is not None:
            project.code_content = project_update.code_content

        await session.flush()
        return project

    @staticmethod
    async def delete_project(session: AsyncSession, project: Project) -> None:
        """Delete a project."""
        await session.delete(project)
        await session.flush()

    @staticmethod
    async def get_project_by_canister_id(
        session: AsyncSession, canister_id: str
    ) -> Optional[Project]:
        """Get project by canister ID."""
        stmt = select(Project).where(Project.canister_id == canister_id)
        result = await session.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def update_project_status(
        session: AsyncSession, project: Project, status: str
    ) -> Project:
        """Update project status."""
        project.status = status
        await session.flush()
        return project
