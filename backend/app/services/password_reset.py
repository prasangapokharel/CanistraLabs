"""Password reset service for handling forgot password functionality."""

import logging
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_

from app.models.user import User
from app.models.password_reset_token import PasswordResetToken
from app.utils.email import email_service
from app.utils.security import hash_password

logger = logging.getLogger(__name__)


class PasswordResetService:
    """Service for managing password reset functionality."""

    @staticmethod
    def generate_reset_token() -> str:
        """Generate a secure random reset token."""
        return str(uuid.uuid4())

    @staticmethod
    async def create_reset_token(
        session: AsyncSession, user: User, expires_in_hours: int = 1
    ) -> PasswordResetToken:
        """Create a new password reset token for a user."""
        # Invalidate any existing unused tokens for this user
        await PasswordResetService._invalidate_existing_tokens(session, user.id)

        # Create new token
        token = PasswordResetService.generate_reset_token()
        expires_at = PasswordResetToken.create_token_expiry(hours=expires_in_hours)

        reset_token = PasswordResetToken(
            user_id=user.id, token=token, expires_at=expires_at, is_used=False
        )

        session.add(reset_token)
        await session.flush()

        logger.info(f"Created password reset token for user {user.id}")
        return reset_token

    @staticmethod
    async def _invalidate_existing_tokens(session: AsyncSession, user_id: int) -> None:
        """Mark all existing unused tokens for a user as used."""
        stmt = select(PasswordResetToken).where(
            and_(
                PasswordResetToken.user_id == user_id,
                PasswordResetToken.is_used == False,
                PasswordResetToken.expires_at > datetime.utcnow(),
            )
        )
        result = await session.execute(stmt)
        existing_tokens = result.scalars().all()

        for token in existing_tokens:
            token.mark_as_used()

        if existing_tokens:
            logger.info(f"Invalidated {len(existing_tokens)} existing tokens for user {user_id}")

    @staticmethod
    async def get_valid_token(session: AsyncSession, token: str) -> Optional[PasswordResetToken]:
        """Get a valid (unused and not expired) reset token."""
        stmt = select(PasswordResetToken).where(
            and_(
                PasswordResetToken.token == token,
                PasswordResetToken.is_used == False,
                PasswordResetToken.expires_at > datetime.utcnow(),
            )
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def verify_reset_token(session: AsyncSession, token: str) -> bool:
        """Verify if a reset token is valid."""
        reset_token = await PasswordResetService.get_valid_token(session, token)
        return reset_token is not None

    @staticmethod
    async def request_password_reset(session: AsyncSession, email: str) -> bool:
        """Request a password reset for a user by email."""
        try:
            # Find user by email
            stmt = select(User).where(User.email == email.lower())
            result = await session.execute(stmt)
            user = result.scalars().first()

            if not user:
                # For security, don't reveal whether email exists
                logger.warning(f"Password reset requested for non-existent email: {email}")
                return True  # Return True to not reveal email existence

            if not user.is_active:
                logger.warning(f"Password reset requested for inactive user: {email}")
                return True  # Return True to not reveal account status

            # Create reset token
            reset_token = await PasswordResetService.create_reset_token(session, user)
            await session.commit()

            # Send email
            email_sent = await email_service.send_password_reset_email(
                to_email=user.email,
                to_name=user.full_name or user.username,
                reset_token=reset_token.token,
                expires_in_hours=1,
            )

            if not email_sent:
                logger.error(f"Failed to send password reset email to {email}")
                # Don't return False here to avoid revealing email delivery issues

            logger.info(f"Password reset requested successfully for {email}")
            return True

        except Exception as e:
            logger.error(f"Error requesting password reset for {email}: {str(e)}")
            return False

    @staticmethod
    async def reset_password(
        session: AsyncSession, token: str, new_password: str
    ) -> tuple[bool, Optional[str]]:
        """Reset password using a valid token."""
        try:
            # Get valid token
            reset_token = await PasswordResetService.get_valid_token(session, token)

            if not reset_token:
                return False, "Invalid or expired reset token"

            # Get user
            stmt = select(User).where(User.id == reset_token.user_id)
            result = await session.execute(stmt)
            user = result.scalars().first()

            if not user or not user.is_active:
                return False, "User not found or inactive"

            # Update password
            user.password_hash = hash_password(new_password)
            user.updated_at = datetime.utcnow()

            # Mark token as used
            reset_token.mark_as_used()

            await session.commit()

            # Send confirmation email
            await email_service.send_password_reset_confirmation_email(
                to_email=user.email, to_name=user.full_name or user.username
            )

            logger.info(f"Password reset successful for user {user.id}")
            return True, "Password reset successful"

        except Exception as e:
            logger.error(f"Error resetting password: {str(e)}")
            await session.rollback()
            return False, "An error occurred while resetting password"

    @staticmethod
    async def cleanup_expired_tokens(session: AsyncSession) -> int:
        """Clean up expired reset tokens."""
        try:
            # Find expired tokens
            stmt = select(PasswordResetToken).where(
                or_(
                    PasswordResetToken.expires_at <= datetime.utcnow(),
                    PasswordResetToken.is_used == True,
                )
            )
            result = await session.execute(stmt)
            expired_tokens = result.scalars().all()

            # Delete expired tokens
            for token in expired_tokens:
                await session.delete(token)

            await session.commit()

            count = len(expired_tokens)
            if count > 0:
                logger.info(f"Cleaned up {count} expired password reset tokens")

            return count

        except Exception as e:
            logger.error(f"Error cleaning up expired tokens: {str(e)}")
            await session.rollback()
            return 0
