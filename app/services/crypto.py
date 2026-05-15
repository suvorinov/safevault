"""Cryptography services for data protection."""

import base64
import hmac
import os

from cryptography.fernet import Fernet

from app.config import get_settings

settings = get_settings()


class CryptoService:
    def __init__(self):
        derived_master_key = self._derive_master_key(settings.master_key.encode())
        self.master_fernet = Fernet(base64.urlsafe_b64encode(derived_master_key))

    def _derive_master_key(self, master_key: bytes) -> bytes:
        """Derives the actual master key using SECRET_KEY as a salt."""
        return hmac.new(
            settings.secret_key.encode(), master_key, digestmod="sha256"
        ).digest()

    def generate_data_key(self) -> tuple[bytes, bytes]:
        """
        Generates a new data key.
        Returns: (plaintext_key, encrypted_key)
        """
        plain_key = Fernet.generate_key()
        encrypted_key = self.master_fernet.encrypt(plain_key)
        return plain_key, encrypted_key

    def decrypt_data_key(self, encrypted_key: bytes) -> Fernet:
        """Decrypts the data key to be used for data encryption."""
        plain_key = self.master_fernet.decrypt(encrypted_key)
        return Fernet(plain_key)

    def encrypt_secret(self, value: str, encrypted_key: bytes) -> bytes:
        """Encrypts a secret value using the project's data key."""
        fernet = self.decrypt_data_key(encrypted_key)
        return fernet.encrypt(value.encode())

    def decrypt_secret(self, encrypted_value: bytes, encrypted_key: bytes) -> str:
        """Decrypts a secret value using the project's data key."""
        fernet = self.decrypt_data_key(encrypted_key)
        return fernet.decrypt(encrypted_value).decode()


crypto_service = CryptoService()
