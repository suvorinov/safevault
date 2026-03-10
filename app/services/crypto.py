"""Cryptography services for data protection."""
from cryptography.fernet import Fernet
from app.config import get_settings
import base64
import os

settings = get_settings()

class CryptoService:
    """Service for handling encryption and decryption."""

    def __init__(self):
        # Инициализация Master Key
        self.master_fernet = Fernet(settings.master_key.encode())

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

# Singleton instance
crypto_service = CryptoService()
