"""Сервис аутентификации и управления API ключами."""

import hmac
import secrets
from datetime import datetime

import bcrypt
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import get_settings
from app.models.user import UserCreate, UserInDB

settings = get_settings()


class AuthService:
    def __init__(self, db):
        self.collection = db.users

    def _apply_pepper(self, data: bytes) -> bytes:
        """Применяет SECRET_KEY как pepper к данным."""
        return hmac.new(
            settings.secret_key.encode(), data, digestmod="sha256"
        ).digest()

    def verify_key(self, plain_key_bytes: bytes, hashed_key_bytes: bytes) -> bool:
        """Проверяет API ключ против хеша с использованием pepper."""
        peppered_key = self._apply_pepper(plain_key_bytes)
        return bcrypt.checkpw(peppered_key, hashed_key_bytes)

    def hash_key(self, plain_key: str) -> bytes:
        """Хеширует API ключ с pepper. Возвращает bytes."""
        key_bytes = plain_key.encode("utf-8")
        peppered_key = self._apply_pepper(key_bytes)
        return bcrypt.hashpw(peppered_key, bcrypt.gensalt())

    def generate_api_key(self) -> str:
        """Генерирует безопасный случайный API ключ."""
        random_bytes = secrets.token_bytes(32)
        signature = hmac.new(
            settings.secret_key.encode(), random_bytes, digestmod="sha256"
        ).hexdigest()[:16]
        return f"sv_live_{secrets.token_urlsafe(24)}_{signature}"

    async def create_user(self, user_data: UserCreate, ip_address: str = None) -> dict:
        """Создает пользователя и возвращает сгенерированный API ключ."""
        from app.services.audit import audit_service

        plain_api_key = self.generate_api_key()
        hashed_api_key = self.hash_key(plain_api_key)

        user_doc = {
            "name": user_data.name,
            "hashed_api_key": hashed_api_key,
            "is_active": True,
            "created_at": datetime.utcnow(),
        }

        result = await self.collection.insert_one(user_doc)
        user_id = str(result.inserted_id)

        await audit_service.log_auth_event(
            user_id=user_id,
            action="register",
            ip_address=ip_address,
            success=True,
            details=f"User '{user_data.name}' registered",
        )

        return {
            "id": user_id,
            "name": user_data.name,
            "api_key": plain_api_key,
        }

    async def get_user_by_key(self, plain_api_key: str, ip_address: str = None) -> UserInDB | None:
        """Находит пользователя по API ключу."""
        from app.services.audit import audit_service

        key_bytes = plain_api_key.encode("utf-8")

        async for user_doc in self.collection.find({"is_active": True}):
            stored_hash = user_doc["hashed_api_key"]

            if isinstance(stored_hash, str):
                stored_hash = stored_hash.encode("utf-8")

            if self.verify_key(key_bytes, stored_hash):
                user = UserInDB(
                    id=str(user_doc["_id"]),
                    name=user_doc["name"],
                    hashed_api_key=user_doc["hashed_api_key"],
                    created_at=user_doc["created_at"],
                )
                await audit_service.log_auth_event(
                    user_id=user.id,
                    action="login",
                    ip_address=ip_address,
                    success=True,
                )
                return user

        await audit_service.log_auth_event(
            user_id="unknown",
            action="login_failed",
            ip_address=ip_address,
            success=False,
            details=f"Invalid API key attempt",
        )
        return None
