"""Tests for project endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestProjectEndpoints:
    """Test project-related endpoints."""

    async def test_create_project_success(self, client: AsyncClient):
        """Test successful project creation."""
        # Create user and get token
        signup_response = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "user@example.com",
                "username": "user",
                "password": "SecurePassword123!",
            },
        )
        access_token = signup_response.json()["access_token"]

        # Create project
        response = await client.post(
            "/api/v1/projects/",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "name": "Test Project",
                "description": "A test project",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Project"
        assert data["description"] == "A test project"
        assert "id" in data
        assert "url" in data
        assert "ic0.app" in data["url"]

    async def test_create_project_missing_auth(self, client: AsyncClient):
        """Test project creation fails without authentication."""
        response = await client.post(
            "/api/v1/projects/",
            json={
                "name": "Test Project",
                "description": "A test project",
            },
        )
        assert response.status_code == 401

    async def test_create_project_invalid_token(self, client: AsyncClient):
        """Test project creation fails with invalid token."""
        response = await client.post(
            "/api/v1/projects/",
            headers={"Authorization": "Bearer invalid-token"},
            json={
                "name": "Test Project",
                "description": "A test project",
            },
        )
        assert response.status_code == 401

    async def test_list_projects_success(self, client: AsyncClient):
        """Test listing user's projects."""
        # Create user and get token
        signup_response = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "user@example.com",
                "username": "user",
                "password": "SecurePassword123!",
            },
        )
        access_token = signup_response.json()["access_token"]

        # Create multiple projects
        project_names = []
        for i in range(3):
            name = f"Project {i + 1}"
            project_names.append(name)
            await client.post(
                "/api/v1/projects/",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "name": name,
                    "description": f"Description {i + 1}",
                },
            )

        # List projects
        response = await client.get(
            "/api/v1/projects/",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        # Check that all created projects are present (order may vary)
        returned_names = [p["name"] for p in data]
        for name in project_names:
            assert name in returned_names

    async def test_list_projects_with_pagination(self, client: AsyncClient):
        """Test listing projects with pagination."""
        # Create user and get token
        signup_response = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "user@example.com",
                "username": "user",
                "password": "SecurePassword123!",
            },
        )
        access_token = signup_response.json()["access_token"]

        # Create 15 projects
        for i in range(15):
            await client.post(
                "/api/v1/projects/",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "name": f"Project {i + 1}",
                    "description": f"Description {i + 1}",
                },
            )

        # List first 10 projects
        response = await client.get(
            "/api/v1/projects/?skip=0&limit=10",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10

        # List next 5 projects
        response = await client.get(
            "/api/v1/projects/?skip=10&limit=10",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

    async def test_list_projects_missing_auth(self, client: AsyncClient):
        """Test listing projects fails without authentication."""
        response = await client.get("/api/v1/projects/")
        assert response.status_code == 401

    async def test_get_project_success(self, client: AsyncClient):
        """Test getting a specific project."""
        # Create user and get token
        signup_response = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "user@example.com",
                "username": "user",
                "password": "SecurePassword123!",
            },
        )
        access_token = signup_response.json()["access_token"]

        # Create project
        create_response = await client.post(
            "/api/v1/projects/",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "name": "Test Project",
                "description": "A test project",
            },
        )
        project_id = create_response.json()["id"]

        # Get project
        response = await client.get(
            f"/api/v1/projects/{project_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Project"
        assert data["description"] == "A test project"
        assert data["id"] == project_id

    async def test_get_project_not_found(self, client: AsyncClient):
        """Test getting a non-existent project."""
        # Create user and get token
        signup_response = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "user@example.com",
                "username": "user",
                "password": "SecurePassword123!",
            },
        )
        access_token = signup_response.json()["access_token"]

        # Try to get non-existent project
        response = await client.get(
            "/api/v1/projects/99999",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 404

    async def test_get_project_unauthorized(self, client: AsyncClient):
        """Test getting another user's project fails."""
        # Create first user and project
        signup_response1 = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "user1@example.com",
                "username": "user1",
                "password": "SecurePassword123!",
            },
        )
        token1 = signup_response1.json()["access_token"]

        create_response = await client.post(
            "/api/v1/projects/",
            headers={"Authorization": f"Bearer {token1}"},
            json={
                "name": "User1 Project",
                "description": "User1's project",
            },
        )
        project_id = create_response.json()["id"]

        # Create second user
        signup_response2 = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "user2@example.com",
                "username": "user2",
                "password": "SecurePassword123!",
            },
        )
        token2 = signup_response2.json()["access_token"]

        # Try to get first user's project as second user
        response = await client.get(
            f"/api/v1/projects/{project_id}",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert response.status_code == 404

    async def test_update_project_success(self, client: AsyncClient):
        """Test updating a project."""
        # Create user and get token
        signup_response = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "user@example.com",
                "username": "user",
                "password": "SecurePassword123!",
            },
        )
        access_token = signup_response.json()["access_token"]

        # Create project
        create_response = await client.post(
            "/api/v1/projects/",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "name": "Original Name",
                "description": "Original Description",
            },
        )
        project_id = create_response.json()["id"]

        # Update project
        response = await client.put(
            f"/api/v1/projects/{project_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "name": "Updated Name",
                "description": "Updated Description",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "Updated Description"

    async def test_update_project_not_found(self, client: AsyncClient):
        """Test updating a non-existent project."""
        # Create user and get token
        signup_response = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "user@example.com",
                "username": "user",
                "password": "SecurePassword123!",
            },
        )
        access_token = signup_response.json()["access_token"]

        # Try to update non-existent project
        response = await client.put(
            "/api/v1/projects/99999",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "name": "Updated Name",
                "description": "Updated Description",
            },
        )
        assert response.status_code == 404

    async def test_update_project_unauthorized(self, client: AsyncClient):
        """Test updating another user's project fails."""
        # Create first user and project
        signup_response1 = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "user1@example.com",
                "username": "user1",
                "password": "SecurePassword123!",
            },
        )
        token1 = signup_response1.json()["access_token"]

        create_response = await client.post(
            "/api/v1/projects/",
            headers={"Authorization": f"Bearer {token1}"},
            json={
                "name": "User1 Project",
                "description": "User1's project",
            },
        )
        project_id = create_response.json()["id"]

        # Create second user
        signup_response2 = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "user2@example.com",
                "username": "user2",
                "password": "SecurePassword123!",
            },
        )
        token2 = signup_response2.json()["access_token"]

        # Try to update first user's project as second user
        response = await client.put(
            f"/api/v1/projects/{project_id}",
            headers={"Authorization": f"Bearer {token2}"},
            json={
                "name": "Updated Name",
                "description": "Updated Description",
            },
        )
        assert response.status_code == 404

    async def test_delete_project_success(self, client: AsyncClient):
        """Test deleting a project."""
        # Create user and get token
        signup_response = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "user@example.com",
                "username": "user",
                "password": "SecurePassword123!",
            },
        )
        access_token = signup_response.json()["access_token"]

        # Create project
        create_response = await client.post(
            "/api/v1/projects/",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "name": "Project to Delete",
                "description": "Will be deleted",
            },
        )
        project_id = create_response.json()["id"]

        # Delete project
        response = await client.delete(
            f"/api/v1/projects/{project_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 204

        # Verify project is deleted
        response = await client.get(
            f"/api/v1/projects/{project_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 404

    async def test_delete_project_not_found(self, client: AsyncClient):
        """Test deleting a non-existent project."""
        # Create user and get token
        signup_response = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "user@example.com",
                "username": "user",
                "password": "SecurePassword123!",
            },
        )
        access_token = signup_response.json()["access_token"]

        # Try to delete non-existent project
        response = await client.delete(
            "/api/v1/projects/99999",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 404

    async def test_delete_project_unauthorized(self, client: AsyncClient):
        """Test deleting another user's project fails."""
        # Create first user and project
        signup_response1 = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "user1@example.com",
                "username": "user1",
                "password": "SecurePassword123!",
            },
        )
        token1 = signup_response1.json()["access_token"]

        create_response = await client.post(
            "/api/v1/projects/",
            headers={"Authorization": f"Bearer {token1}"},
            json={
                "name": "User1 Project",
                "description": "User1's project",
            },
        )
        project_id = create_response.json()["id"]

        # Create second user
        signup_response2 = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "user2@example.com",
                "username": "user2",
                "password": "SecurePassword123!",
            },
        )
        token2 = signup_response2.json()["access_token"]

        # Try to delete first user's project as second user
        response = await client.delete(
            f"/api/v1/projects/{project_id}",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert response.status_code == 404
