#!/usr/bin/env python3
"""
Test script for dynamic deployment system.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.dynamic_deployment import DynamicDeploymentService, DeploymentConfig
from app.database.db import async_session_maker
from app.services.auth import AuthService
from app.models.project import Project
from sqlalchemy import select


async def test_dynamic_deployment():
    """Test the dynamic deployment system."""
    print("🧪 Testing Dynamic Deployment System")
    print("=" * 50)

    async with async_session_maker() as session:
        # Get user and project
        user = await AuthService.get_user_by_id(session, 37)
        if not user or not user.dfx_identity_name:
            print("❌ User 37 not found or no dfx identity")
            return

        result = await session.execute(select(Project).where(Project.user_id == 37))
        projects = result.scalars().all()

        if not projects:
            print("❌ No projects found for user 37")
            return

        project = projects[0]  # Use first project

        print(f"👤 User: {user.id} (identity: {user.dfx_identity_name})")
        print(f"📁 Project: {project.id} - {project.name}")
        print(f"💾 Content: {len(project.code_content)} characters")
        print(f"🏷️  Language: {project.language}")
        print()

        # Create deployment config
        config = DeploymentConfig(
            project_id=project.id,
            project_name=project.name.replace(" ", "_").lower(),  # Safe name
            content=project.code_content,
            content_type=project.language or "html",
            identity=user.dfx_identity_name,
        )

        # Test deployment
        print("🚀 Starting Dynamic Deployment...")
        deployment_service = DynamicDeploymentService(network="ic")

        result = await deployment_service.deploy_project(config)

        print("\n📊 Deployment Results:")
        print(f"Success: {result.get('success')}")

        if result.get("success"):
            print(f"✅ Canister ID: {result.get('canister_id')}")
            print(f"🌐 URL: {result.get('url')}")
            print(f"📁 Workspace: {result.get('workspace')}")

            # Update database
            print("\n💾 Updating Database...")
            db_updated = await deployment_service.update_project_database(
                session, project.id, result
            )
            print(f"Database updated: {db_updated}")

        else:
            print(f"❌ Error: {result.get('error')}")
            print(f"🔍 Stage: {result.get('stage')}")


async def test_auto_deploy_funded_projects():
    """Test the auto-deploy functionality."""
    print("\n🤖 Testing Auto-Deploy for Funded Projects")
    print("=" * 50)

    from app.api.v1.dynamic_deployment import auto_deploy_funded_projects
    from app.database.db import async_session_maker

    async with async_session_maker() as session:
        result = await auto_deploy_funded_projects(session)

        print(f"✅ Auto-deploy completed")
        print(f"📊 Result: {result.get('message')}")

        deployments = result.get("deployments", [])
        for deployment in deployments:
            status = deployment.get("status")
            project_name = deployment.get("project_name", "Unknown")

            if status == "deployed":
                print(f"  ✅ {project_name}: {deployment.get('url')}")
            elif status == "insufficient_cycles":
                balance = deployment.get("cycles_balance", 0)
                print(f"  ⏳ {project_name}: Need cycles (has {balance} TC)")
            elif status == "failed":
                error = deployment.get("error", "Unknown error")
                print(f"  ❌ {project_name}: {error}")
            else:
                print(f"  ❓ {project_name}: {status}")


if __name__ == "__main__":
    print("🚀 Dynamic Deployment Test Suite")
    print("=" * 60)

    # Test individual deployment
    asyncio.run(test_dynamic_deployment())

    # Test auto-deploy system
    asyncio.run(test_auto_deploy_funded_projects())
