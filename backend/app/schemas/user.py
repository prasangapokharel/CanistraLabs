"""User schemas for request/response validation."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for user creation."""

    password: str = Field(..., min_length=8, max_length=255)


class UserUpdate(BaseModel):
    """Schema for user updates."""

    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8, max_length=255)


class UserResponse(UserBase):
    """Schema for user response."""

    id: int
    is_active: bool
    is_superuser: bool
    email_verified: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """Schema for login request."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema for token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenRefreshRequest(BaseModel):
    """Schema for token refresh."""

    refresh_token: str


class PasswordChangeRequest(BaseModel):
    """Schema for password change."""

    old_password: str
    new_password: str = Field(..., min_length=8, max_length=255)


class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Schema for password reset request."""

    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=255)


class VerifyResetTokenRequest(BaseModel):
    """Schema for verifying reset token."""

    token: str = Field(..., min_length=1)


class MessageResponse(BaseModel):
    """Schema for simple message responses."""

    message: str
    success: bool = True


class VerifyEmailRequest(BaseModel):
    """Schema for email verification request."""

    token: str = Field(..., min_length=1)


class ResendVerificationRequest(BaseModel):
    """Schema for resending email verification."""

    email: EmailStr
