"""Integration tests for deployment functionality."""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.canister import Canister
from app.models.deployment import Deployment
from app.models.project import Project
from app.models.user import User
from app.utils.icp_utils import (
    ICPService,
    ICPError,
    DfxNotInstalledException,
    CanisterCreationException,
    CanisterDeploymentException,
)
from app.utils.security import create_access_token


@pytest_asyncio.fixture
async def test_user(async_session_maker):
    """Create a test user."""
    async with async_session_maker() as session:
        user = User(
            email="testuser@example.com",
            username="testuser",
            full_name="Test User",
            password_hash="hashed_password",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest_asyncio.fixture
async def test_project(async_session_maker, test_user):
    """Create a test project."""
    async with async_session_maker() as session:
        project = Project(
            name="test-project",
            description="Test project for deployment",
            user_id=test_user.id,
            code_content='actor { public func greet() : async Text { return "Hello"; } }',
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)
        return project


@pytest_asyncio.fixture
def valid_token(test_user):
    """Create a valid JWT token for test user."""
    return create_access_token({"sub": str(test_user.id)})


@pytest.mark.asyncio
async def test_deploy_project_creates_new_canister(
    client, async_session_maker, test_user, test_project, valid_token
):
    """Test deploying a project to shared canister."""
    with patch("app.utils.icp_utils.ICPService.deploy_to_shared_canister") as mock_deploy:
        # Mock successful deployment to shared canister
        mock_deploy.return_value = {
            "canister_id": "uxrrr-q7777-77774-qaaaq-cai",
            "project_path": f"project-{test_project.id}",
            "status": "deployed",
            "url": f"https://uxrrr-q7777-77774-qaaaq-cai.ic0.app/project-{test_project.id}/",
        }

        response = await client.post(
            f"/api/v1/deployments/projects/{test_project.id}/deploy",
            json={"code_content": 'actor { public func test() : async Text { return "test"; } }'},
            headers={"Authorization": f"Bearer {valid_token}"},
        )

        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "success"
        assert data["canister_id"] == "uxrrr-q7777-77774-qaaaq-cai"
        assert "deployment_id" in data


@pytest.mark.asyncio
async def test_deploy_project_updates_existing_canister(
    client, async_session_maker, test_user, test_project, valid_token
):
    """Test deploying a project to shared canister (redeployment)."""
    # Set up project with existing canister reference
    async with async_session_maker() as session:
        project = await session.get(Project, test_project.id)
        project.canister_id = "uxrrr-q7777-77774-qaaaq-cai"
        project.principal_id = "existing-principal-456"
        project.status = "deployed"
        await session.commit()

    with patch("app.utils.icp_utils.ICPService.deploy_to_shared_canister") as mock_deploy:
        # Mock successful redeployment to shared canister
        mock_deploy.return_value = {
            "canister_id": "uxrrr-q7777-77774-qaaaq-cai",
            "project_path": f"project-{test_project.id}",
            "status": "deployed",
            "url": f"https://uxrrr-q7777-77774-qaaaq-cai.ic0.app/project-{test_project.id}/",
        }

        response = await client.post(
            f"/api/v1/deployments/projects/{test_project.id}/deploy",
            json={
                "code_content": 'actor { public func updated() : async Text { return "updated"; } }'
            },
            headers={"Authorization": f"Bearer {valid_token}"},
        )

        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "success"
        assert data["canister_id"] == "uxrrr-q7777-77774-qaaaq-cai"


@pytest.mark.asyncio
async def test_deploy_project_without_authorization(client, test_project):
    """Test deploying without authorization returns 401."""
    response = await client.post(
        f"/api/v1/deployments/projects/{test_project.id}/deploy",
        json={"code_content": "actor { }"},
    )

    assert response.status_code == 401
    assert "authorization" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_deploy_project_invalid_token(client, test_project):
    """Test deploying with invalid token returns 401."""
    response = await client.post(
        f"/api/v1/deployments/projects/{test_project.id}/deploy",
        json={"code_content": "actor { }"},
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_deploy_nonexistent_project(client, async_session_maker, test_user, valid_token):
    """Test deploying nonexistent project returns 404."""
    response = await client.post(
        "/api/v1/deployments/projects/9999/deploy",
        json={"code_content": "actor { }"},
        headers={"Authorization": f"Bearer {valid_token}"},
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_deploy_project_not_owned(client, async_session_maker, valid_token):
    """Test deploying someone else's project returns 404."""
    # Create another user's project
    async with async_session_maker() as session:
        other_user = User(
            email="otheruser@example.com",
            username="otheruser",
            full_name="Other User",
            password_hash="hashed_password",
        )
        session.add(other_user)
        await session.flush()

        other_project = Project(
            name="other-project",
            description="Other user's project",
            user_id=other_user.id,
            code_content="actor { }",
        )
        session.add(other_project)
        await session.commit()
        project_id = other_project.id

    response = await client.post(
        f"/api/v1/deployments/projects/{project_id}/deploy",
        json={"code_content": "actor { }"},
        headers={"Authorization": f"Bearer {valid_token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_deploy_handles_canister_creation_error(
    client, async_session_maker, test_user, test_project, valid_token
):
    """Test handling of deployment errors."""
    with patch("app.utils.icp_utils.ICPService.deploy_to_shared_canister") as mock_deploy:
        mock_deploy.side_effect = CanisterCreationException("Failed to deploy")

        response = await client.post(
            f"/api/v1/deployments/projects/{test_project.id}/deploy",
            json={"code_content": "actor { }"},
            headers={"Authorization": f"Bearer {valid_token}"},
        )

        assert response.status_code == 500
        assert "deployment failed" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_deployment_status(
    client, async_session_maker, test_user, test_project, valid_token
):
    """Test getting deployment status."""
    # Create a deployment
    async with async_session_maker() as session:
        deployment = Deployment(
            project_id=test_project.id,
            status="completed",
            message="Successfully deployed",
        )
        session.add(deployment)
        await session.commit()
        deployment_id = deployment.id

    response = await client.get(
        f"/api/v1/deployments/projects/{test_project.id}/deployments/{deployment_id}",
        headers={"Authorization": f"Bearer {valid_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["message"] == "Successfully deployed"
    assert data["deployment_id"] == deployment_id


@pytest.mark.asyncio
async def test_get_deployment_status_not_found(client, test_user, test_project, valid_token):
    """Test getting nonexistent deployment returns 404."""
    response = await client.get(
        f"/api/v1/deployments/projects/{test_project.id}/deployments/9999",
        headers={"Authorization": f"Bearer {valid_token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_deployment_status_wrong_project(
    client, async_session_maker, test_user, test_project, valid_token
):
    """Test getting deployment from wrong project returns 404."""
    # Create a deployment for different project
    async with async_session_maker() as session:
        other_project = Project(
            name="other-project",
            description="Other project",
            user_id=test_user.id,
            code_content="actor { }",
        )
        session.add(other_project)
        await session.flush()

        deployment = Deployment(
            project_id=other_project.id,
            status="completed",
            message="Deployed",
        )
        session.add(deployment)
        await session.commit()
        deployment_id = deployment.id

    response = await client.get(
        f"/api/v1/deployments/projects/{test_project.id}/deployments/{deployment_id}",
        headers={"Authorization": f"Bearer {valid_token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_deployments(client, async_session_maker, test_user, test_project, valid_token):
    """Test listing deployments for a project."""
    # Create multiple deployments
    async with async_session_maker() as session:
        deployments = [
            Deployment(
                project_id=test_project.id,
                status="completed",
                message=f"Deployment {i}",
            )
            for i in range(3)
        ]
        session.add_all(deployments)
        await session.commit()

    response = await client.get(
        f"/api/v1/deployments/projects/{test_project.id}/deployments",
        headers={"Authorization": f"Bearer {valid_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert all(d["status"] == "completed" for d in data)


@pytest.mark.asyncio
async def test_list_deployments_pagination(
    client, async_session_maker, test_user, test_project, valid_token
):
    """Test pagination of deployments."""
    # Create multiple deployments
    async with async_session_maker() as session:
        deployments = [
            Deployment(
                project_id=test_project.id,
                status="completed",
                message=f"Deployment {i}",
            )
            for i in range(15)
        ]
        session.add_all(deployments)
        await session.commit()

    # Test default limit
    response = await client.get(
        f"/api/v1/deployments/projects/{test_project.id}/deployments",
        headers={"Authorization": f"Bearer {valid_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 10  # Default limit


@pytest.mark.asyncio
async def test_get_canister_status(
    client, async_session_maker, test_user, test_project, valid_token
):
    """Test getting canister status."""
    with patch("app.utils.icp_utils.ICPService.get_canister_status") as mock_status:
        mock_status.return_value = {
            "canister_id": "test-canister-123",
            "status": "running",
            "cycles": 1000000,
            "memory_usage": 5000,
        }

        response = await client.get(
            "/api/v1/deployments/canisters/test-canister-123/status",
            headers={"Authorization": f"Bearer {valid_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["canister_id"] == "test-canister-123"
        assert data["status"] == "running"
        assert data["cycles"] == 1000000


@pytest.mark.asyncio
async def test_get_canister_status_fallback_to_db(
    client, async_session_maker, test_user, valid_token
):
    """Test getting canister status falls back to database on ICP error."""
    # Create a canister in database
    async with async_session_maker() as session:
        project = Project(
            name="project-with-canister",
            description="Project with canister",
            user_id=test_user.id,
            code_content="actor { }",
        )
        session.add(project)
        await session.flush()

        canister = Canister(
            project_id=project.id,
            canister_name="cached-canister-123",
            principal_id="principal-456",
            status="running",
            cycles_balance="500000",
        )
        session.add(canister)
        await session.commit()

    with patch("app.utils.icp_utils.ICPService.get_canister_status") as mock_status:
        mock_status.side_effect = ICPError("ICP service unavailable")

        response = await client.get(
            "/api/v1/deployments/canisters/cached-canister-123/status",
            headers={"Authorization": f"Bearer {valid_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["canister_id"] == "cached-canister-123"
        assert data["status"] == "running"
        assert data["cycles"] == "500000"


@pytest.mark.asyncio
async def test_deployment_records_status_progression(
    client, async_session_maker, test_user, test_project, valid_token
):
    """Test that deployment records track status progression."""
    with patch("app.utils.icp_utils.ICPService.deploy_to_shared_canister") as mock_deploy:
        mock_deploy.return_value = {
            "canister_id": "uxrrr-q7777-77774-qaaaq-cai",
            "project_path": f"project-{test_project.id}",
            "status": "deployed",
            "url": f"https://uxrrr-q7777-77774-qaaaq-cai.ic0.app/project-{test_project.id}/",
        }

        response = await client.post(
            f"/api/v1/deployments/projects/{test_project.id}/deploy",
            json={"code_content": "actor { }"},
            headers={"Authorization": f"Bearer {valid_token}"},
        )

        assert response.status_code == 202
        deployment_id = response.json()["deployment_id"]

        # Verify final status in database
        async with async_session_maker() as session:
            deployment = await session.get(Deployment, deployment_id)
            assert deployment.status == "success"
            assert "Successfully deployed" in deployment.message
            assert deployment.completed_at is not None


@pytest.mark.asyncio
async def test_deployment_error_handling(
    client, async_session_maker, test_user, test_project, valid_token
):
    """Test that deployment errors result in 500 response."""
    with patch("app.utils.icp_utils.ICPService.deploy_to_shared_canister") as mock_deploy:
        error_message = "Network connection failed"
        mock_deploy.side_effect = CanisterDeploymentException(error_message)

        response = await client.post(
            f"/api/v1/deployments/projects/{test_project.id}/deploy",
            json={"code_content": "actor { }"},
            headers={"Authorization": f"Bearer {valid_token}"},
        )

        # Should get 500 error
        assert response.status_code == 500
        assert "deployment failed" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_deploy_uses_project_code_content_if_not_provided(
    client, async_session_maker, test_user, test_project, valid_token
):
    """Test that deployment uses project code if not provided in request."""
    project_code = 'actor { public func project_method() : async Text { return "project"; } }'

    # Update project with specific code
    async with async_session_maker() as session:
        project = await session.get(Project, test_project.id)
        project.code_content = project_code
        await session.commit()

    with patch("app.utils.icp_utils.ICPService.deploy_to_shared_canister") as mock_deploy:
        mock_deploy.return_value = {
            "canister_id": "uxrrr-q7777-77774-qaaaq-cai",
            "project_path": f"project-{test_project.id}",
            "status": "deployed",
            "url": f"https://uxrrr-q7777-77774-qaaaq-cai.ic0.app/project-{test_project.id}/",
        }

        # Deploy without providing code_content
        response = await client.post(
            f"/api/v1/deployments/projects/{test_project.id}/deploy",
            json={},
            headers={"Authorization": f"Bearer {valid_token}"},
        )

        assert response.status_code == 202
        # Verify that deploy_to_shared_canister was called with project's code
        mock_deploy.assert_called_once()
        call_kwargs = mock_deploy.call_args[1]
        assert call_kwargs["code_content"] == project_code


@pytest.mark.asyncio
async def test_deployment_missing_authorization_header(client, test_project):
    """Test deployment without authorization header returns 401."""
    response = await client.post(
        f"/api/v1/deployments/projects/{test_project.id}/deploy",
        json={"code_content": "actor { }"},
    )

    assert response.status_code == 401
    assert "authorization" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_deployment_malformed_authorization_header(client, test_project):
    """Test deployment with malformed authorization header returns 401."""
    response = await client.post(
        f"/api/v1/deployments/projects/{test_project.id}/deploy",
        json={"code_content": "actor { }"},
        headers={"Authorization": "InvalidFormat"},
    )

    assert response.status_code == 401
    assert "authorization" in response.json()["detail"].lower()
