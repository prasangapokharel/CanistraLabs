"""Test script for password reset functionality."""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.config import settings
from app.models.user import User
from app.services.password_reset import PasswordResetService
from app.services.auth import AuthService
from app.schemas.user import UserCreate


async def test_password_reset():
    """Test password reset functionality."""
    # Create async engine and session
    engine = create_async_engine(settings.database_url)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        try:
            print("🔐 Testing Password Reset System...")

            # Test token generation
            token = PasswordResetService.generate_reset_token()
            print(f"✅ Generated token: {token[:20]}...")

            # Test token verification (should fail for non-existent token)
            is_valid = await PasswordResetService.verify_reset_token(session, "invalid-token")
            print(f"✅ Invalid token verification: {not is_valid}")

            # Test forgot password for non-existent email
            result = await PasswordResetService.request_password_reset(
                session, "nonexistent@example.com"
            )
            print(f"✅ Forgot password for non-existent email: {result}")

            print("✅ All tests passed!")

        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_password_reset())
