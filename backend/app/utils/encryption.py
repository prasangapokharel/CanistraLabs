"""Encryption utilities for secure storage of sensitive data."""

import base64
import json
import logging
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.config import settings

logger = logging.getLogger(__name__)

# Legacy salt used before ENCRYPTION_KEY was introduced (decrypt-only fallback)
_LEGACY_SALT = b"icp_identity_salt_12345"


class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""

    @staticmethod
    def _derive_key(password: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100_000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    @staticmethod
    def _get_primary_key() -> bytes:
        """Current encryption key derived from dedicated ENCRYPTION_KEY."""
        salt = b"icp_hosting_v2_" + settings.effective_encryption_key[:16].encode()
        return EncryptionService._derive_key(settings.effective_encryption_key, salt)

    @staticmethod
    def _get_legacy_key() -> bytes:
        """Legacy key derived from JWT secret (for decrypting existing records)."""
        return EncryptionService._derive_key(settings.jwt_secret_key, _LEGACY_SALT)

    @staticmethod
    def encrypt_data(data: Dict[str, Any]) -> str:
        """Encrypt sensitive data for secure storage."""
        try:
            json_str = json.dumps(data)
            f = Fernet(EncryptionService._get_primary_key())
            encrypted_data = f.encrypt(json_str.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error("Encryption failed: %s", e)
            raise ValueError(f"Failed to encrypt data: {e}") from e

    @staticmethod
    def decrypt_data(encrypted_str: str) -> Dict[str, Any]:
        """Decrypt sensitive data, with legacy key fallback for migration."""
        encrypted_data = base64.urlsafe_b64decode(encrypted_str.encode())
        last_error: Optional[Exception] = None

        for key_fn in (EncryptionService._get_primary_key, EncryptionService._get_legacy_key):
            try:
                f = Fernet(key_fn())
                decrypted_data = f.decrypt(encrypted_data)
                return json.loads(decrypted_data.decode())
            except Exception as e:
                last_error = e

        logger.error("Decryption failed: %s", last_error)
        raise ValueError("Failed to decrypt data") from last_error

    @staticmethod
    def encrypt_string(text: str) -> str:
        return EncryptionService.encrypt_data({"value": text})

    @staticmethod
    def decrypt_string(encrypted_str: str) -> str:
        data = EncryptionService.decrypt_data(encrypted_str)
        return data["value"]
