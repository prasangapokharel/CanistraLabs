"""Database initialization and migration utilities."""

import asyncio
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings
from app.database.db import Base

# Import all models to register them with Base
from app.models.user import User
from app.models.project import Project
from app.models.enrollment import ProjectEnrollment
from app.models.deployment import Deployment
from app.models.domain import CustomDomain
from app.models.password_reset_token import PasswordResetToken
from app.models.email_verification_token import EmailVerificationToken

logger = logging.getLogger(__name__)


async def init_database():
    """Initialize database with all tables."""
    try:
        # Create async engine
        engine = create_async_engine(
            settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
            echo=True,
        )

        async with engine.begin() as conn:
            # Drop all tables (for development)
            await conn.run_sync(Base.metadata.drop_all)

            # Create all tables
            await conn.run_sync(Base.metadata.create_all)

        await engine.dispose()
        logger.info("Database initialization completed successfully")

    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise


async def add_email_verification_column():
    """Add email_verified column to users table if it doesn't exist."""
    try:
        engine = create_async_engine(
            settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
            echo=True,
        )

        async with engine.begin() as conn:
            # Check if column exists
            result = await conn.execute(
                text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                AND column_name = 'email_verified';
            """)
            )

            if not result.fetchone():
                # Add the column
                await conn.execute(
                    text("""
                    ALTER TABLE users 
                    ADD COLUMN email_verified BOOLEAN DEFAULT FALSE NOT NULL;
                """)
                )
                logger.info("Added email_verified column to users table")
            else:
                logger.info("email_verified column already exists")

        await engine.dispose()

    except Exception as e:
        logger.error(f"Failed to add email_verified column: {str(e)}")
        raise


async def create_email_verification_tokens_table():
    """Create email_verification_tokens table if it doesn't exist."""
    try:
        engine = create_async_engine(
            settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
            echo=True,
        )

        async with engine.begin() as conn:
            # Check if table exists
            result = await conn.execute(
                text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = 'email_verification_tokens';
            """)
            )

            if not result.fetchone():
                # Create the table
                await conn.execute(
                    text("""
                    CREATE TABLE email_verification_tokens (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        token VARCHAR(255) UNIQUE NOT NULL,
                        expires_at TIMESTAMP NOT NULL,
                        is_used BOOLEAN DEFAULT FALSE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        used_at TIMESTAMP
                    );
                """)
                )

                await conn.execute(
                    text("""
                    CREATE INDEX idx_email_verification_tokens_user_id 
                    ON email_verification_tokens(user_id);
                """)
                )

                await conn.execute(
                    text("""
                    CREATE INDEX idx_email_verification_tokens_token 
                    ON email_verification_tokens(token);
                """)
                )

                logger.info("Created email_verification_tokens table")
            else:
                logger.info("email_verification_tokens table already exists")

        await engine.dispose()

    except Exception as e:
        logger.error(f"Failed to create email_verification_tokens table: {str(e)}")
        raise


if __name__ == "__main__":
    # Run database initialization
    asyncio.run(init_database())
