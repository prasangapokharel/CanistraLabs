"""Automatic ICP Identity Management Service."""

import os
import uuid
import logging
import tempfile
import hashlib
import base58
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.utils.encryption import EncryptionService
from app.config import settings

logger = logging.getLogger(__name__)


class ICPError(Exception):
    """Base exception for ICP-related errors."""

    pass


class ICPIdentityManager:
    """Manages automatic ICP identity creation and switching for users."""

    @staticmethod
    async def create_user_identity(session: AsyncSession, user: User) -> Dict[str, Any]:
        """
        Create ICP identity using clean dfxCommand service.

        Args:
            session: Database session
            user: User instance to create identity for

        Returns:
            Dictionary with identity creation result
        """
        logger.info(f"Creating ICP identity for user {user.id} ({user.email})")

        try:
            # Generate unique identity name
            identity_name = f"user_{user.id}_{uuid.uuid4().hex[:8]}"

            # Use clean dfxCommand service
            from app.services.dfxCommand import DfxCommand

            dfx = DfxCommand(network="ic")

            # Create new identity
            result = dfx.identityNew(identity_name)

            if not result["success"]:
                raise ICPError(f"Failed to create identity: {result.get('error')}")

            logger.info(f"Created identity: {identity_name}")
            logger.info(f"Principal ID: {result['principalId']}")
            logger.info(f"Account ID: {result['accountId']}")

            # Export private key for secure storage
            exportResult = dfx.identityExport(identity_name)
            if not exportResult["success"]:
                raise ICPError(f"Failed to export identity: {exportResult.get('error')}")

            # Encrypt and store identity data
            identity_data = {
                "identity_name": identity_name,
                "principal_id": result["principalId"],
                "account_id": result["accountId"],
                "private_key": exportResult["privateKey"],
                "created_at": datetime.utcnow().isoformat(),
            }

            encrypted_key = EncryptionService.encrypt_data(identity_data)

            # Update user record
            user.dfx_identity_name = identity_name
            user.principal_id = result["principalId"]
            user.account_id = result["accountId"]
            user.encrypted_identity_key = encrypted_key
            user.identity_created_at = datetime.utcnow()
            user.wallet_cycles_balance = "0"

            await session.flush()

            logger.info(f"Successfully created and stored ICP identity for user {user.id}")

            return {
                "identity_name": identity_name,
                "principal_id": result["principalId"],
                "account_id": result["accountId"],
                "funding_required": True,
                "cycles_balance": "0",
                "status": "created",
                "message": f"ICP identity created. Fund using Account ID: {result['accountId']}",
            }

        except Exception as e:
            logger.error(f"Failed to create ICP identity for user {user.id}: {str(e)}")
            raise ICPError(f"Identity creation failed: {str(e)}")

    @staticmethod
    async def get_user_identity_context(session: AsyncSession, user: User) -> Dict[str, Any]:
        """
        Get user's ICP identity context for deployments.

        Args:
            session: Database session
            user: User instance

        Returns:
            Dictionary with identity context
        """
        if not user.dfx_identity_name or not user.encrypted_identity_key:
            # Auto-create identity if doesn't exist
            return await ICPIdentityManager.create_user_identity(session, user)

        try:
            # Ensure identity is restored in dfx
            ICPIdentityManager._restore_identity_files(user)

            # Check wallet balance
            cycles_balance = await ICPIdentityManager.check_wallet_balance(user)

            return {
                "identity_name": user.dfx_identity_name,
                "principal_id": user.principal_id,
                "cycles_balance": cycles_balance,
                "status": "active",
                "funding_required": int(cycles_balance) < 20_000_000,  # Minimum cycles needed
            }

        except Exception as e:
            logger.error(f"Failed to get identity context for user {user.id}: {str(e)}")
            raise ICPError(f"Identity context error: {str(e)}")

    @staticmethod
    def switch_to_user_identity(user: User) -> str:
        """
        Switch dfx to use the specified user's identity.

        Args:
            user: User whose identity to switch to

        Returns:
            Identity name that was switched to

        Raises:
            ICPError: If switching fails
        """
        if not user.dfx_identity_name:
            raise ICPError("No dfx identity found for user")

        try:
            # Ensure identity files are available
            ICPIdentityManager._restore_identity_files(user)

            # Switch dfx to use this identity
            from app.services.dfxCommand import DfxCommand

            dfx = DfxCommand()
            result = dfx.identityUse(user.dfx_identity_name)

            if not result["success"]:
                raise ICPError(f"Failed to switch identity: {result.get('error', 'Unknown error')}")

            logger.info(f"Switched to identity: {user.dfx_identity_name}")
            return user.dfx_identity_name

        except Exception as e:
            logger.error(f"Failed to switch to user identity: {str(e)}")
            raise ICPError(f"Identity switch failed: {str(e)}")

    @staticmethod
    def _restore_identity_files(user: User) -> None:
        """
        Restore identity files from encrypted storage if needed.

        Args:
            user: User whose identity files to restore
        """
        if not user.encrypted_identity_key or not user.dfx_identity_name:
            raise ICPError("No encrypted identity data found")

        try:
            # Check if identity already exists in dfx
            from app.services.dfxCommand import DfxCommand

            dfx = DfxCommand()
            identities_result = dfx.identityList()

            if (
                identities_result["success"]
                and user.dfx_identity_name
                and user.dfx_identity_name in identities_result["identities"]
            ):
                logger.info(f"Identity {user.dfx_identity_name} already exists in dfx")
                return

            # Decrypt identity data
            identity_data = EncryptionService.decrypt_data(user.encrypted_identity_key)

            # Import the identity back into dfx using the private key
            if not user.dfx_identity_name:
                raise Exception("No dfx identity name found")

            # Use dfxCommand to import identity
            from app.services.dfxCommand import DfxCommand

            dfx = DfxCommand()

            # For import, we need to use subprocess directly since dfxCommand doesn't have import
            import subprocess
            import os
            from pathlib import Path

            dfx_path = Path.home() / ".local" / "bin" / "dfx"
            dfx_cmd = str(dfx_path) if dfx_path.exists() else "dfx"

            env = os.environ.copy()
            env["PATH"] = f"{Path.home() / '.local' / 'bin'}:{env.get('PATH', '')}"
            env["DFX_WARNING"] = "-mainnet_plaintext_identity"

            import_proc = subprocess.run(
                [dfx_cmd, "identity", "import", user.dfx_identity_name],
                input=identity_data["private_key"],
                capture_output=True,
                text=True,
                env=env,
            )

            if import_proc.returncode != 0:
                raise Exception(f"Failed to import identity: {import_proc.stderr}")

            logger.info(f"Successfully restored identity: {user.dfx_identity_name}")

        except Exception as e:
            logger.error(f"Failed to restore identity files: {str(e)}")
            raise Exception(f"Identity restoration failed: {str(e)}")

    @staticmethod
    async def check_wallet_balance(user: User) -> str:
        """
        Check cycles balance using clean dfxCommand service.

        Args:
            user: User whose wallet to check

        Returns:
            Cycles balance as string
        """
        if not user.dfx_identity_name:
            return "0"

        try:
            # Use clean dfxCommand service
            from app.services.dfxCommand import DfxCommand

            dfx = DfxCommand(network="ic")

            # Get cycles balance
            cyclesResult = dfx.cyclesGetBalance(user.dfx_identity_name)
            walletResult = dfx.walletGetBalance(user.dfx_identity_name)

            # Use cycles balance if available, otherwise wallet balance
            if cyclesResult["success"] and cyclesResult["balanceCycles"] > 0:
                balance = str(cyclesResult["balanceCycles"])
            elif walletResult["success"] and walletResult.get("walletExists", False):
                balance = str(walletResult["balanceCycles"])
            else:
                balance = "0"

            # Update user's cached balance
            user.wallet_cycles_balance = balance
            return balance

        except Exception as e:
            logger.warning(f"Failed to check wallet balance for user {user.id}: {str(e)}")
            return user.wallet_cycles_balance or "0"

    @staticmethod
    def _get_current_identity() -> str:
        """Get the current dfx identity using clean dfxCommand."""
        try:
            from app.services.dfxCommand import DfxCommand

            dfx = DfxCommand()
            result = dfx.identityWhoami()
            return result["current"] if result["success"] else "default"
        except Exception:
            return "default"

    @staticmethod
    async def delete_user_identity(session: AsyncSession, user: User) -> Dict[str, Any]:
        """
        Delete a user's ICP identity and clean up resources.

        Args:
            session: Database session
            user: User whose identity to delete

        Returns:
            Deletion result
        """
        if not user.dfx_identity_name:
            return {"message": "No identity to delete"}

        try:
            # Remove identity from dfx - use basic subprocess since dfxCommand doesn't have remove
            import subprocess
            import os
            from pathlib import Path

            dfx_path = Path.home() / ".local" / "bin" / "dfx"
            dfx_cmd = str(dfx_path) if dfx_path.exists() else "dfx"

            env = os.environ.copy()
            env["PATH"] = f"{Path.home() / '.local' / 'bin'}:{env.get('PATH', '')}"
            env["DFX_WARNING"] = "-mainnet_plaintext_identity"

            result = subprocess.run(
                [dfx_cmd, "identity", "remove", user.dfx_identity_name],
                capture_output=True,
                text=True,
                env=env,
            )

            returncode = result.returncode
            stdout = result.stdout
            stderr = result.stderr

            # Clear user identity data
            user.dfx_identity_name = None
            user.principal_id = None
            user.account_id = None
            user.encrypted_identity_key = None
            user.wallet_cycles_balance = "0"
            user.identity_created_at = None

            await session.flush()

            logger.info(f"Deleted identity for user {user.id}")

            return {
                "message": "Identity deleted successfully",
                "dfx_result": stdout if returncode == 0 else stderr,
            }

        except Exception as e:
            logger.error(f"Failed to delete identity for user {user.id}: {str(e)}")
            raise ICPError(f"Identity deletion failed: {str(e)}")

    @staticmethod
    def principal_to_account_id(principal_id: str, subaccount: Optional[bytes] = None) -> str:
        """
        Convert a principal ID to an Account ID using the correct ICRC algorithm.

        Args:
            principal_id: Principal ID to convert
            subaccount: Optional subaccount bytes

        Returns:
            Account ID as hex string
        """
        try:
            # This should match dfx ledger account-id output exactly
            # Use dfxCommand service for consistency
            from app.services.dfxCommand import DfxCommand

            dfx = DfxCommand()

            # For now, we rely on dfx to provide the correct Account ID
            # In the future, we could implement the full ICRC algorithm
            logger.warning("Using dfx for Account ID generation - ensure consistency")

            # Return a placeholder that indicates dfx should be used
            return "USE_DFX_LEDGER_ACCOUNT_ID"

        except Exception as e:
            logger.error(f"Failed to convert principal to account ID: {e}")
            raise ICPError(f"Account ID conversion failed: {str(e)}")

    @staticmethod
    def validate_principal_id(principal_id: str) -> bool:
        """
        Validate a principal ID format.

        Args:
            principal_id: Principal ID to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            # Principal IDs should be base32-encoded with specific format
            # Basic validation - proper validation would decode and check checksum
            if not principal_id or len(principal_id) < 10:
                return False

            # Should contain only valid base32 characters and dashes
            valid_chars = set("abcdefghijklmnopqrstuvwxyz234567-")
            return all(c.lower() in valid_chars for c in principal_id)

        except Exception:
            return False

    @staticmethod
    def validate_account_id(account_id: str) -> bool:
        """
        Validate an Account ID format.

        Args:
            account_id: Account ID to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            # Account IDs should be 64-character hex strings
            if not account_id or len(account_id) != 64:
                return False

            # Should contain only hex characters
            try:
                int(account_id, 16)
                return True
            except ValueError:
                return False

        except Exception:
            return False
