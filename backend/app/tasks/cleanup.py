"""Cleanup tasks for expired password reset tokens."""

import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.services.password_reset import PasswordResetService

logger = logging.getLogger(__name__)

# Get celery app instance
from app.tasks.celeryApp import celery_app


async def get_async_session() -> AsyncSession:
    """Create async database session for tasks."""
    engine = create_async_engine(settings.database_url)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    return async_session()


@celery_app.task(bind=True)
def cleanup_expired_reset_tokens(self):
    """Cleanup expired password reset tokens."""
    try:

        async def _cleanup():
            session = await get_async_session()
            try:
                count = await PasswordResetService.cleanup_expired_tokens(session)
                logger.info(f"Cleaned up {count} expired password reset tokens")
                return count
            finally:
                await session.close()

        # Run the async cleanup function
        count = asyncio.run(_cleanup())
        return {"success": True, "cleaned_tokens": count}

    except Exception as e:
        logger.error(f"Error cleaning up expired reset tokens: {str(e)}")
        return {"success": False, "error": str(e)}
