"""Authentication API routes."""

from datetime import timedelta
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.schemas.user import (
    LoginRequest,
    TokenRefreshRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    VerifyResetTokenRequest,
    VerifyEmailRequest,
    ResendVerificationRequest,
    MessageResponse,
)
from app.services.auth import AuthService
from app.services.password_reset import PasswordResetService
from app.services.email_verification import EmailVerificationService
from app.utils.security import create_access_token, create_refresh_token, verify_token
from app.utils.rate_limit import rate_limiter, RateLimitExceeded

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


async def get_bearer_token(authorization: Annotated[Optional[str], Header()] = None) -> str:
    """Extract bearer token from Authorization header."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
        )

    return parts[1]


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    user_create: UserCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Register a new user."""
    try:
        user = await AuthService.create_user(session, user_create)
        await session.commit()

        # Create email verification token
        await EmailVerificationService.create_verification_token(session, user)

    except ValueError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=86400,  # 24 hours
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    login_request: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Login user and return tokens."""
    user = await AuthService.authenticate_user(session, login_request.email, login_request.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=86400,  # 24 hours
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_request: TokenRefreshRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Refresh access token using refresh token."""
    token_data = verify_token(token_request.refresh_token, token_type="refresh")

    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Verify user still exists and is active
    user = await AuthService.get_user_by_id(session, int(token_data.sub))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    new_access_token = create_access_token({"sub": str(user.id)})
    new_refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=86400,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    token: Annotated[str, Depends(get_bearer_token)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """Get current authenticated user."""
    token_data = verify_token(token, token_type="access")

    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user = await AuthService.get_user_by_id(session, int(token_data.sub))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse.model_validate(user)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    token: Annotated[str, Depends(get_bearer_token)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    """Logout user and invalidate tokens."""
    # Verify the token is valid before logging out
    token_data = verify_token(token, token_type="access")

    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    # For JWT tokens, we primarily rely on client-side token removal
    # In a production system, you might want to add server-side token blacklisting
    # TODO: Add token blacklisting for enhanced security if needed

    return MessageResponse(
        message="Successfully logged out",
        success=True,
    )


def get_client_ip(request: Request) -> str:
    """Get client IP address for rate limiting."""
    # Check for forwarded IP first (for proxy/load balancer scenarios)
    forwarded_ip = request.headers.get("X-Forwarded-For")
    if forwarded_ip:
        # X-Forwarded-For can contain multiple IPs, get the first one
        return forwarded_ip.split(",")[0].strip()

    # Check for real IP (another common header)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Fall back to direct connection IP
    return request.client.host if request.client else "unknown"


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    request: Request,
    forgot_request: ForgotPasswordRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    """Request a password reset email."""
    client_ip = get_client_ip(request)
    rate_limit_key = f"forgot_password:{client_ip}"

    # Check rate limit (5 requests per 5 minutes)
    is_allowed, retry_after = rate_limiter.is_allowed(
        rate_limit_key, max_requests=5, window_seconds=300
    )

    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many password reset requests. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )

    try:
        success = await PasswordResetService.request_password_reset(session, forgot_request.email)

        # Always return success message for security
        return MessageResponse(
            message="If the email address exists, you will receive password reset instructions.",
            success=True,
        )

    except Exception as e:
        # Log error but don't expose it to user
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error processing forgot password request: {str(e)}")

        return MessageResponse(
            message="If the email address exists, you will receive password reset instructions.",
            success=True,
        )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    request: Request,
    reset_request: ResetPasswordRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    """Reset password using a reset token."""
    client_ip = get_client_ip(request)
    rate_limit_key = f"reset_password:{client_ip}"

    # Check rate limit (10 attempts per 5 minutes)
    is_allowed, retry_after = rate_limiter.is_allowed(
        rate_limit_key, max_requests=10, window_seconds=300
    )

    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many password reset attempts. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )

    success, message = await PasswordResetService.reset_password(
        session, reset_request.token, reset_request.new_password
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message or "Invalid or expired reset token",
        )

    return MessageResponse(
        message="Password has been reset successfully. You can now log in with your new password.",
        success=True,
    )


@router.get("/verify-reset-token", response_model=MessageResponse)
async def verify_reset_token(
    token: str,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    """Verify if a password reset token is valid."""
    is_valid = await PasswordResetService.verify_reset_token(session, token)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token"
        )

    return MessageResponse(message="Reset token is valid", success=True)


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    request: Request,
    verify_request: VerifyEmailRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    """Verify user's email address using verification token."""
    client_ip = get_client_ip(request)
    rate_limit_key = f"verify_email:{client_ip}"

    # Check rate limit (10 attempts per 5 minutes)
    is_allowed, retry_after = rate_limiter.is_allowed(
        rate_limit_key, max_requests=10, window_seconds=300
    )

    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many email verification attempts. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )

    result = await EmailVerificationService.verify_token(session, verify_request.token)

    if not result["success"]:
        error_code = result.get("error", "VERIFICATION_FAILED")
        if error_code == "TOKEN_NOT_FOUND":
            status_code = status.HTTP_404_NOT_FOUND
        elif error_code in ["TOKEN_EXPIRED_OR_USED", "EMAIL_ALREADY_VERIFIED"]:
            status_code = status.HTTP_400_BAD_REQUEST
        else:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        raise HTTPException(
            status_code=status_code,
            detail=result["message"],
        )

    return MessageResponse(
        message=result["message"],
        success=True,
    )


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification_email(
    request: Request,
    resend_request: ResendVerificationRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    """Resend email verification token to user."""
    client_ip = get_client_ip(request)
    rate_limit_key = f"resend_verification:{client_ip}"

    # Check rate limit (5 attempts per 10 minutes)
    is_allowed, retry_after = rate_limiter.is_allowed(
        rate_limit_key, max_requests=5, window_seconds=600
    )

    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many resend attempts. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )

    result = await EmailVerificationService.resend_verification_email(session, resend_request.email)

    if not result["success"]:
        error_code = result.get("error", "RESEND_FAILED")
        if error_code == "USER_NOT_FOUND":
            # Don't reveal if user exists or not for security
            pass  # Still return success message
        elif error_code == "EMAIL_ALREADY_VERIFIED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already verified",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send verification email",
            )

    return MessageResponse(
        message="If the email address is registered, a verification email has been sent.",
        success=True,
    )
