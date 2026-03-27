"""Email verification service for user email validation."""

import secrets
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.email_verification_token import EmailVerificationToken
from app.config import settings

logger = logging.getLogger(__name__)


class EmailVerificationService:
    """Service for handling email verification tokens."""

    @staticmethod
    def generate_token() -> str:
        """Generate a secure random token for email verification."""
        return secrets.token_urlsafe(32)

    @staticmethod
    async def create_verification_token(
        session: AsyncSession, user: User
    ) -> EmailVerificationToken:
        """
        Create a new email verification token for a user.

        Args:
            session: Database session
            user: User to create token for

        Returns:
            Created email verification token
        """
        # Invalidate any existing tokens
        existing_tokens = await session.execute(
            select(EmailVerificationToken).where(
                EmailVerificationToken.user_id == user.id, EmailVerificationToken.is_used == False
            )
        )

        for token in existing_tokens.scalars():
            token.is_used = True
            token.used_at = datetime.utcnow()

        # Create new token
        token_string = EmailVerificationService.generate_token()
        verification_token = EmailVerificationToken(
            user_id=user.id,
            token=token_string,
            expires_at=EmailVerificationToken.create_token_expiry(hours=24),  # 24 hour expiry
        )

        session.add(verification_token)
        await session.commit()
        await session.refresh(verification_token)

        logger.info(f"Created email verification token for user {user.id}")
        return verification_token

    @staticmethod
    async def verify_token(session: AsyncSession, token: str) -> Dict[str, Any]:
        """
        Verify an email verification token and mark user's email as verified.

        Args:
            session: Database session
            token: Verification token string

        Returns:
            Verification result with success status and message
        """
        try:
            # Find token
            result = await session.execute(
                select(EmailVerificationToken).where(EmailVerificationToken.token == token)
            )
            verification_token = result.scalar_one_or_none()

            if not verification_token:
                return {
                    "success": False,
                    "message": "Invalid verification token",
                    "error": "TOKEN_NOT_FOUND",
                }

            # Check if token is valid
            if not verification_token.is_valid():
                return {
                    "success": False,
                    "message": "Verification token has expired or been used",
                    "error": "TOKEN_EXPIRED_OR_USED",
                }

            # Get user
            user = await session.get(User, verification_token.user_id)
            if not user:
                return {"success": False, "message": "User not found", "error": "USER_NOT_FOUND"}

            # Check if email is already verified
            if user.email_verified:
                return {
                    "success": True,
                    "message": "Email is already verified",
                    "user_id": user.id,
                    "already_verified": True,
                }

            # Mark token as used
            verification_token.mark_as_used()

            # Mark user email as verified
            user.email_verified = True

            await session.commit()

            logger.info(f"Email verified successfully for user {user.id}")

            return {
                "success": True,
                "message": "Email verified successfully",
                "user_id": user.id,
                "email": user.email,
                "verified_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Email verification failed: {str(e)}")
            await session.rollback()
            return {
                "success": False,
                "message": "Email verification failed",
                "error": f"VERIFICATION_ERROR: {str(e)}",
            }

    @staticmethod
    async def resend_verification_email(session: AsyncSession, email: str) -> Dict[str, Any]:
        """
        Resend verification email to a user.

        Args:
            session: Database session
            email: User email address

        Returns:
            Resend result with success status and message
        """
        try:
            # Find user by email
            result = await session.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()

            if not user:
                return {"success": False, "message": "User not found", "error": "USER_NOT_FOUND"}

            # Check if email is already verified
            if user.email_verified:
                return {
                    "success": False,
                    "message": "Email is already verified",
                    "error": "EMAIL_ALREADY_VERIFIED",
                }

            # Create new verification token
            verification_token = await EmailVerificationService.create_verification_token(
                session, user
            )

            # In a real application, you would send an email here
            # For now, we'll just return the token for testing purposes
            verification_url = (
                f"{settings.frontend_url}/verify-email?token={verification_token.token}"
            )

            logger.info(f"Verification email resent for user {user.id}")

            return {
                "success": True,
                "message": "Verification email sent successfully",
                "user_id": user.id,
                "email": user.email,
                "verification_url": verification_url,  # Remove in production
                "token": verification_token.token,  # Remove in production
                "expires_at": verification_token.expires_at.isoformat(),
            }

        except Exception as e:
            logger.error(f"Resend verification email failed: {str(e)}")
            await session.rollback()
            return {
                "success": False,
                "message": "Failed to resend verification email",
                "error": f"RESEND_ERROR: {str(e)}",
            }

    @staticmethod
    async def get_user_verification_status(session: AsyncSession, user_id: int) -> Dict[str, Any]:
        """
        Get email verification status for a user.

        Args:
            session: Database session
            user_id: User ID

        Returns:
            Verification status information
        """
        try:
            user = await session.get(User, user_id)
            if not user:
                return {"success": False, "message": "User not found", "error": "USER_NOT_FOUND"}

            # Get pending tokens
            result = await session.execute(
                select(EmailVerificationToken).where(
                    EmailVerificationToken.user_id == user_id,
                    EmailVerificationToken.is_used == False,
                )
            )
            pending_tokens = result.scalars().all()
            valid_tokens = [token for token in pending_tokens if token.is_valid()]

            return {
                "success": True,
                "user_id": user.id,
                "email": user.email,
                "email_verified": user.email_verified,
                "pending_tokens_count": len(valid_tokens),
                "latest_token_expires_at": (
                    max(token.expires_at for token in valid_tokens).isoformat()
                    if valid_tokens
                    else None
                ),
            }

        except Exception as e:
            logger.error(f"Get verification status failed: {str(e)}")
            return {
                "success": False,
                "message": "Failed to get verification status",
                "error": f"STATUS_ERROR: {str(e)}",
            }
