#!/usr/bin/env python3
"""Check users and their projects in the database."""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.database.db import async_session_maker
from app.models.user import User
from app.models.project import Project
from sqlalchemy import select, func


async def check_users_and_projects():
    """Check all users and their projects."""
    async with async_session_maker() as session:
        print("=== ALL USERS IN DATABASE ===")

        # Get all users
        users_result = await session.execute(select(User))
        users = users_result.scalars().all()

        for user in users:
            print(f"User: {user.email} (ID: {user.id})")

            # Get projects for this user
            projects_result = await session.execute(
                select(Project).where(Project.user_id == user.id)
            )
            projects = projects_result.scalars().all()

            print(f"  Projects ({len(projects)}):")
            for project in projects:
                print(
                    f"    - {project.name} (ID: {project.id}) - Created: {project.created_at}"
                )
            print()

        # Get totals
        total_users_result = await session.execute(select(func.count(User.id)))
        total_users = total_users_result.scalar()

        total_projects_result = await session.execute(select(func.count(Project.id)))
        total_projects = total_projects_result.scalar()

        print(f"Total Users: {total_users}")
        print(f"Total Projects: {total_projects}")


if __name__ == "__main__":
    asyncio.run(check_users_and_projects())
