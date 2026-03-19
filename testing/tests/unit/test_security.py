"""Tests for security utilities."""

from datetime import datetime, timedelta
from jose import jwt

from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    TokenData,
)
from app.config import settings


class TestPasswordHashing:
    """Test password hashing utilities."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "MySecurePassword123!"
        hashed = hash_password(password)

        # Hash should not be the same as password
        assert hashed != password
        # Hash should be non-empty
        assert len(hashed) > 0
        # Hash should be string
        assert isinstance(hashed, str)

    def test_verify_password_success(self):
        """Test successful password verification."""
        password = "MySecurePassword123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_failure(self):
        """Test failed password verification."""
        password = "MySecurePassword123!"
        wrong_password = "WrongPassword456!"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_hash_consistency(self):
        """Test that same password produces different hashes."""
        password = "MySecurePassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Hashes should be different (argon2 uses salt)
        assert hash1 != hash2
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTTokens:
    """Test JWT token creation and verification."""

    def test_create_access_token(self):
        """Test creating an access token."""
        data = {"sub": "123"}
        token = create_access_token(data)

        # Token should be a string
        assert isinstance(token, str)
        # Token should not be empty
        assert len(token) > 0

        # Decode token to verify
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["sub"] == "123"
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_create_access_token_with_expiration(self):
        """Test creating an access token with custom expiration."""
        data = {"sub": "123"}
        expires_delta = timedelta(hours=1)
        token = create_access_token(data, expires_delta)

        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["sub"] == "123"
        assert payload["type"] == "access"

        # Verify expiration is approximately 1 hour from the token's "issued at" time
        exp_timestamp = payload["exp"]
        iat_timestamp = payload["iat"]
        time_diff = exp_timestamp - iat_timestamp
        # Should be approximately 3600 seconds (1 hour), allowing some tolerance
        assert 3590 < time_diff < 3610

    def test_create_refresh_token(self):
        """Test creating a refresh token."""
        data = {"sub": "123"}
        token = create_refresh_token(data)

        # Token should be a string
        assert isinstance(token, str)
        # Token should not be empty
        assert len(token) > 0

        # Decode token to verify
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["sub"] == "123"
        assert payload["type"] == "refresh"
        assert "exp" in payload
        assert "iat" in payload

    def test_verify_token_success(self):
        """Test successful token verification."""
        data = {"sub": "123"}
        token = create_access_token(data)

        token_data = verify_token(token, token_type="access")
        assert token_data is not None
        assert token_data.sub == "123"
        assert token_data.type == "access"

    def test_verify_token_invalid_signature(self):
        """Test verification fails with invalid signature."""
        data = {"sub": "123"}
        token = jwt.encode(data, "wrong-secret-key", algorithm="HS256")

        token_data = verify_token(token, token_type="access")
        assert token_data is None

    def test_verify_token_wrong_type(self):
        """Test verification fails when token type doesn't match."""
        data = {"sub": "123"}
        refresh_token = create_refresh_token(data)

        # Try to verify refresh token as access token
        token_data = verify_token(refresh_token, token_type="access")
        assert token_data is None

    def test_verify_token_missing_subject(self):
        """Test verification fails when token is missing subject."""
        data = {"exp": datetime.utcnow() + timedelta(hours=1), "type": "access"}
        token = jwt.encode(data, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

        token_data = verify_token(token, token_type="access")
        assert token_data is None

    def test_verify_expired_token(self):
        """Test verification fails for expired token."""
        data = {"sub": "123"}
        # Create token that expired 1 hour ago
        expires_delta = timedelta(hours=-1)
        token = create_access_token(data, expires_delta)

        token_data = verify_token(token, token_type="access")
        assert token_data is None

    def test_verify_token_with_additional_claims(self):
        """Test verification works with additional claims."""
        data = {"sub": "123", "email": "user@example.com", "name": "John Doe"}
        token = create_access_token(data)

        token_data = verify_token(token, token_type="access")
        assert token_data is not None
        assert token_data.sub == "123"

        # Decode to check additional claims
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["email"] == "user@example.com"
        assert payload["name"] == "John Doe"

    def test_token_data_model(self):
        """Test TokenData model."""
        now = datetime.utcnow()
        token_data = TokenData(sub="123", exp=now, iat=now, type="access")

        assert token_data.sub == "123"
        assert token_data.type == "access"
        assert token_data.exp == now
        assert token_data.iat == now
