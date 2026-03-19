"""Encryption utilities for secure storage of sensitive data."""

import base64
import json
import logging
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.config import settings

logger = logging.getLogger(__name__)


class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""

    @staticmethod
    def _get_key() -> bytes:
        """Generate encryption key from JWT secret."""
        # Use JWT secret as base for encryption key
        password = settings.jwt_secret_key.encode()
        salt = b"icp_identity_salt_12345"  # Fixed salt for consistent keys

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key

    @staticmethod
    def encrypt_data(data: Dict[str, Any]) -> str:
        """
        Encrypt sensitive data for secure storage.

        Args:
            data: Dictionary containing sensitive data to encrypt

        Returns:
            Base64 encoded encrypted string
        """
        try:
            # Convert dict to JSON string
            json_str = json.dumps(data)

            # Encrypt the JSON string
            key = EncryptionService._get_key()
            f = Fernet(key)
            encrypted_data = f.encrypt(json_str.encode())

            # Return base64 encoded string for database storage
            return base64.urlsafe_b64encode(encrypted_data).decode()

        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise ValueError(f"Failed to encrypt data: {str(e)}")

    @staticmethod
    def decrypt_data(encrypted_str: str) -> Dict[str, Any]:
        """
        Decrypt sensitive data from storage.

        Args:
            encrypted_str: Base64 encoded encrypted string

        Returns:
            Dictionary containing decrypted data
        """
        try:
            # Decode base64
            encrypted_data = base64.urlsafe_b64decode(encrypted_str.encode())

            # Decrypt the data
            key = EncryptionService._get_key()
            f = Fernet(key)
            decrypted_data = f.decrypt(encrypted_data)

            # Parse JSON and return dict
            return json.loads(decrypted_data.decode())

        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise ValueError(f"Failed to decrypt data: {str(e)}")

    @staticmethod
    def encrypt_string(text: str) -> str:
        """
        Encrypt a simple string.

        Args:
            text: String to encrypt

        Returns:
            Base64 encoded encrypted string
        """
        return EncryptionService.encrypt_data({"value": text})

    @staticmethod
    def decrypt_string(encrypted_str: str) -> str:
        """
        Decrypt a simple string.

        Args:
            encrypted_str: Base64 encoded encrypted string

        Returns:
            Decrypted string
        """
        data = EncryptionService.decrypt_data(encrypted_str)
        return data["value"]
