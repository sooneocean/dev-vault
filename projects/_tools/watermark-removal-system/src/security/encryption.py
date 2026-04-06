"""
Data protection and encryption.

Supports encryption at rest and secure key management.
"""

import logging
import secrets
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import cryptography
try:
    from cryptography.fernet import Fernet
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False
    logger.warning("cryptography library not available, encryption disabled")


class EncryptionKey:
    """Encryption key management."""

    def __init__(self, key_id: str, key_bytes: bytes):
        self.key_id = key_id
        self.key_bytes = key_bytes
        self.rotated = False

    @staticmethod
    def generate(key_id: str, key_size: int = 32) -> "EncryptionKey":
        """Generate random encryption key."""
        key_bytes = secrets.token_bytes(key_size)
        return EncryptionKey(key_id, key_bytes)


class KeyManager:
    """Manage encryption keys."""

    def __init__(self):
        self.keys: dict[str, EncryptionKey] = {}
        # Initialize with default key
        default_key = EncryptionKey.generate("default")
        self.keys["default"] = default_key
        self.active_key_id = "default"

    def get_key(self, key_id: str = "default") -> Optional[EncryptionKey]:
        """Get encryption key."""
        return self.keys.get(key_id)

    def get_active_key(self) -> EncryptionKey:
        """Get currently active encryption key."""
        return self.keys[self.active_key_id]

    def rotate_key(self, new_key_id: str) -> bool:
        """
        Rotate to new encryption key.

        Args:
            new_key_id: ID of new key to use

        Returns:
            True if rotation successful
        """
        if new_key_id not in self.keys:
            logger.error(f"Key {new_key_id} not found")
            return False

        old_key_id = self.active_key_id
        self.active_key_id = new_key_id
        self.keys[old_key_id].rotated = True

        logger.info(f"Rotated encryption key from {old_key_id} to {new_key_id}")
        return True

    def add_key(self, key_id: str, key: EncryptionKey) -> bool:
        """Add new encryption key."""
        if key_id in self.keys:
            logger.warning(f"Key {key_id} already exists")
            return False

        self.keys[key_id] = key
        logger.info(f"Added encryption key {key_id}")
        return True


class DataEncryptor:
    """Encrypt and decrypt data."""

    def __init__(self, key_manager: KeyManager):
        self.key_manager = key_manager

    def encrypt_data(self, data: bytes, key_id: str = "default") -> Optional[bytes]:
        """
        Encrypt data.

        Args:
            data: Data to encrypt
            key_id: Key ID to use

        Returns:
            Encrypted data or None if error
        """
        try:
            if not HAS_CRYPTOGRAPHY:
                logger.warning("cryptography not available, returning data unencrypted")
                return data

            key = self.key_manager.get_key(key_id)
            if key is None:
                logger.error(f"Key {key_id} not found")
                return None

            # For Fernet, key must be URL-safe base64 encoded 32 bytes
            import base64

            encoded_key = base64.urlsafe_b64encode(key.key_bytes[:32])
            cipher = Fernet(encoded_key)
            encrypted = cipher.encrypt(data)

            logger.debug(f"Encrypted {len(data)} bytes with key {key_id}")
            return encrypted

        except Exception as e:
            logger.error(f"Encryption error: {e}")
            return None

    def decrypt_data(self, encrypted_data: bytes, key_id: str = "default") -> Optional[bytes]:
        """
        Decrypt data.

        Args:
            encrypted_data: Encrypted data
            key_id: Key ID to use

        Returns:
            Decrypted data or None if error
        """
        try:
            if not HAS_CRYPTOGRAPHY:
                logger.warning("cryptography not available, returning data unencrypted")
                return encrypted_data

            key = self.key_manager.get_key(key_id)
            if key is None:
                logger.error(f"Key {key_id} not found")
                return None

            import base64

            encoded_key = base64.urlsafe_b64encode(key.key_bytes[:32])
            cipher = Fernet(encoded_key)
            decrypted = cipher.decrypt(encrypted_data)

            logger.debug(f"Decrypted data with key {key_id}")
            return decrypted

        except Exception as e:
            logger.error(f"Decryption error: {e}")
            return None


class PII:
    """PII redaction utilities."""

    EMAIL_PATTERN = r"[\w\.-]+@[\w\.-]+\.\w+"
    PHONE_PATTERN = r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"
    SSN_PATTERN = r"\b\d{3}-\d{2}-\d{4}\b"

    @staticmethod
    def redact_email(text: str) -> str:
        """Redact email addresses."""
        import re

        return re.sub(PII.EMAIL_PATTERN, "[EMAIL_REDACTED]", text)

    @staticmethod
    def redact_phone(text: str) -> str:
        """Redact phone numbers."""
        import re

        return re.sub(PII.PHONE_PATTERN, "[PHONE_REDACTED]", text)

    @staticmethod
    def redact_ssn(text: str) -> str:
        """Redact SSN."""
        import re

        return re.sub(PII.SSN_PATTERN, "[SSN_REDACTED]", text)

    @staticmethod
    def redact_all(text: str) -> str:
        """Redact all common PII."""
        text = PII.redact_email(text)
        text = PII.redact_phone(text)
        text = PII.redact_ssn(text)
        return text


class SecureLogFormatter:
    """Format logs with PII redaction."""

    @staticmethod
    def sanitize_log_message(message: str, redact_pii: bool = True) -> str:
        """
        Sanitize log message.

        Args:
            message: Log message
            redact_pii: Whether to redact PII

        Returns:
            Sanitized message
        """
        if redact_pii:
            return PII.redact_all(message)
        return message


# Global instances
key_manager = KeyManager()
data_encryptor = DataEncryptor(key_manager)
