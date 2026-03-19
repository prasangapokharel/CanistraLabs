"""Tests for authentication endpoints."""

import pytest
from httpx import AsyncClient

from app.schemas.user import UserCreate


@pytest.mark.asyncio
class TestAuthenticationEndpoints:
    """Test authentication-related endpoints."""

    async def test_signup_success(self, client: AsyncClient):
        """Test successful user registration."""
        response = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "SecurePassword123!",
                "full_name": "New User",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_signup_duplicate_email(self, client: AsyncClient):
        """Test signup fails with duplicate email."""
        # First signup
        await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "user@example.com",
                "username": "user1",
                "password": "SecurePassword123!",
            },
        )
        # Second signup with same email
        response = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "user@example.com",
                "username": "user2",
                "password": "SecurePassword123!",
            },
        )
        assert response.status_code == 400

    async def test_signup_duplicate_username(self, client: AsyncClient):
        """Test signup fails with duplicate username."""
        # First signup
        await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "user1@example.com",
                "username": "duplicate",
                "password": "SecurePassword123!",
            },
        )
        # Second signup with same username
        response = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "user2@example.com",
                "username": "duplicate",
                "password": "SecurePassword123!",
            },
        )
        assert response.status_code == 400

    async def test_signup_invalid_email(self, client: AsyncClient):
        """Test signup fails with invalid email."""
        response = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "invalid-email",
                "username": "user",
                "password": "SecurePassword123!",
            },
        )
        assert response.status_code == 422

    async def test_signup_weak_password(self, client: AsyncClient):
        """Test signup fails with weak password."""
        response = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "user@example.com",
                "username": "user",
                "password": "weak",
            },
        )
        assert response.status_code == 422

    async def test_login_success(self, client: AsyncClient):
        """Test successful login."""
        # Create user
        await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "user@example.com",
                "username": "user",
                "password": "SecurePassword123!",
            },
        )
        # Login
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "SecurePassword123!"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_login_invalid_email(self, client: AsyncClient):
        """Test login with invalid email."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "SomePassword123!"},
        )
        assert response.status_code == 401

    async def test_login_invalid_password(self, client: AsyncClient):
        """Test login with invalid password."""
        # Create user
        await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "user@example.com",
                "username": "user",
                "password": "SecurePassword123!",
            },
        )
        # Try to login with wrong password
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "WrongPassword!"},
        )
        assert response.status_code == 401

    async def test_refresh_token_success(self, client: AsyncClient):
        """Test successful token refresh."""
        # Create user and get tokens
        signup_response = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "user@example.com",
                "username": "user",
                "password": "SecurePassword123!",
            },
        )
        refresh_token = signup_response.json()["refresh_token"]

        # Refresh token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_get_current_user_success(self, client: AsyncClient):
        """Test getting current user info."""
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

        # Get current user
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "user@example.com"
        assert data["username"] == "user"

    async def test_get_current_user_missing_token(self, client: AsyncClient):
        """Test getting current user without token."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """Test getting current user with invalid token."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401
