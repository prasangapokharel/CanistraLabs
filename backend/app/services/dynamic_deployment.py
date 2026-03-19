"""
Dynamic Project Deployment Service

Handles fully automated deployment of projects to Internet Computer canisters.
Supports various project types (HTML, React, etc.) with zero manual intervention.
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from app.services.dfxCommand import DfxCommand
from app.models.project import Project, ProjectStatus
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class DeploymentConfig:
    """Configuration for project deployment."""

    project_id: int
    project_name: str
    content: str
    content_type: str  # 'html', 'react', 'vue', etc.
    identity: str
    network: str = "ic"


class DynamicDeploymentService:
    """Service for automated project deployment to ICP canisters."""

    def __init__(self, network: str = "ic"):
        self.network = network
        self.dfx = DfxCommand(network=network)
        self.base_work_dir = Path("/tmp/icp_deployments")
        self.base_work_dir.mkdir(exist_ok=True)

    def create_deployment_workspace(self, config: DeploymentConfig) -> Path:
        """Create a temporary workspace for deployment."""
        workspace = self.base_work_dir / f"project_{config.project_id}_{config.project_name}"

        # Clean up existing workspace
        if workspace.exists():
            shutil.rmtree(workspace)

        workspace.mkdir(parents=True)
        return workspace

    def create_dfx_json(self, workspace: Path, canister_name: str) -> Dict[str, Any]:
        """Create dfx.json configuration for the project."""
        dfx_config = {
            "version": 1,
            "canisters": {
                canister_name: {"type": "assets", "source": [f"src/{canister_name}/assets/"]}
            },
            "networks": {self.network: {"providers": ["https://ic0.app"], "type": "persistent"}},
            "defaults": {"build": {"packtool": ""}},
        }

        dfx_json_path = workspace / "dfx.json"
        with open(dfx_json_path, "w") as f:
            json.dump(dfx_config, f, indent=2)

        return dfx_config

    def setup_assets_structure(
        self, workspace: Path, canister_name: str, content: str, content_type: str
    ) -> Path:
        """Set up the assets directory structure and content."""
        assets_dir = workspace / "src" / canister_name / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)

        # Determine main file name based on content type
        if content_type.lower() in ["html", "static"]:
            main_file = "index.html"
        elif content_type.lower() in ["react", "vue", "angular"]:
            main_file = "index.html"  # For now, treat all as static HTML
        else:
            main_file = "index.html"  # Default fallback

        # Write the main content file
        main_file_path = assets_dir / main_file
        with open(main_file_path, "w", encoding="utf-8") as f:
            f.write(content)

        # Create basic security policy for assets
        ic_assets_config = [{"match": "**/*", "security_policy": "standard"}]

        assets_config_path = workspace / ".ic-assets.json5"
        with open(assets_config_path, "w") as f:
            json.dump(ic_assets_config, f, indent=2)

        return assets_dir

    async def deploy_project(self, config: DeploymentConfig) -> Dict[str, Any]:
        """
        Fully automated project deployment.

        Returns:
            Dict containing deployment results with canister_id, url, etc.
        """
        try:
            # Step 1: Create workspace
            workspace = self.create_deployment_workspace(config)
            canister_name = f"app_{config.project_id}"

            print(f"📁 Created workspace: {workspace}")

            # Step 2: Create dfx.json
            dfx_config = self.create_dfx_json(workspace, canister_name)
            print(f"📋 Created dfx.json configuration")

            # Step 3: Set up assets
            assets_dir = self.setup_assets_structure(
                workspace, canister_name, config.content, config.content_type
            )
            print(f"📦 Set up assets in: {assets_dir}")

            # Step 4: Create canister
            print(f"🔨 Creating canister...")

            # Change to workspace directory for dfx commands
            original_cwd = os.getcwd()
            os.chdir(workspace)

            try:
                # Ensure we're using the correct identity before creating canister
                identity_result = self.dfx.identityUse(config.identity)
                if not identity_result.get("success"):
                    return {
                        "success": False,
                        "error": f"Failed to switch to identity {config.identity}: {identity_result.get('error')}",
                        "stage": "identity_setup",
                    }

                print(f"🆔 Using identity: {config.identity}")

                # Check cycles balance before attempting creation
                cycles_balance = self.dfx.cyclesGetBalance(identity=config.identity)
                if cycles_balance.get("balanceTc", 0) < 0.5:
                    return {
                        "success": False,
                        "error": f"Insufficient cycles: {cycles_balance.get('balanceTc', 0)} TC (need >= 0.5 TC)",
                        "stage": "insufficient_cycles",
                    }

                print(f"💰 Cycles available: {cycles_balance.get('balanceTc', 0)} TC")

                # Create canister with sufficient cycles (1 trillion cycles)
                create_result = self.dfx.canisterCreate(
                    name=canister_name,
                    withCycles="1000000000000",  # 1 TC
                    identity=config.identity,
                )

                if not create_result.get("success"):
                    return {
                        "success": False,
                        "error": f"Canister creation failed: {create_result.get('error', 'Unknown error')}",
                        "stage": "canister_creation",
                    }

                canister_id = create_result.get("canisterId")
                if not canister_id:
                    return {
                        "success": False,
                        "error": "No canister ID returned from creation",
                        "stage": "canister_creation",
                    }

                print(f"✅ Created canister: {canister_id}")

                # Step 5: Deploy to canister
                print(f"🚀 Deploying content...")

                deploy_result = self.dfx.canisterDeploy(
                    name=canister_name, identity=config.identity
                )

                if not deploy_result.get("success"):
                    return {
                        "success": False,
                        "error": f"Deployment failed: {deploy_result.get('error', 'Unknown error')}",
                        "stage": "deployment",
                        "canister_id": canister_id,
                    }

                # Step 6: Generate URLs
                ic_url = f"https://{canister_id}.icp0.io/"
                raw_url = f"https://{canister_id}.raw.icp0.io/"

                print(f"🌐 Deployment successful!")
                print(f"   URL: {ic_url}")

                # Step 7: Clean up workspace (optional - keep for debugging)
                # shutil.rmtree(workspace)

                return {
                    "success": True,
                    "canister_id": canister_id,
                    "url": ic_url,
                    "raw_url": raw_url,
                    "deployment_output": deploy_result.get("output", ""),
                    "stage": "completed",
                    "workspace": str(workspace),  # For debugging
                }

            finally:
                # Always restore working directory
                os.chdir(original_cwd)

        except Exception as e:
            return {
                "success": False,
                "error": f"Deployment exception: {str(e)}",
                "stage": "exception",
            }

    async def update_project_database(
        self, session: AsyncSession, project_id: int, deployment_result: Dict[str, Any]
    ) -> bool:
        """Update project in database with deployment results."""
        try:
            # Get project
            result = await session.execute(select(Project).where(Project.id == project_id))
            project = result.scalar_one_or_none()

            if not project:
                print(f"❌ Project {project_id} not found in database")
                return False

            if deployment_result.get("success"):
                # Update with successful deployment
                project.canister_id = deployment_result["canister_id"]
                project.url = deployment_result["url"]
                project.status = ProjectStatus.ACTIVE
                project.deployed_at = datetime.utcnow()

                session.add(project)
                await session.commit()

                print(f"✅ Updated project {project_id} in database")
                print(f"   Canister ID: {project.canister_id}")
                print(f"   URL: {project.url}")
                print(f"   Status: {project.status}")

                return True
            else:
                # Update with failed deployment
                project.status = ProjectStatus.FAILED
                session.add(project)
                await session.commit()

                print(f"❌ Marked project {project_id} as failed in database")
                return False

        except Exception as e:
            print(f"❌ Database update error: {str(e)}")
            await session.rollback()
            return False


# Add missing imports
from datetime import datetime
from sqlalchemy import select
