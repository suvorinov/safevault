"""Сервис аутентификации и управления API ключами."""

import bcrypt
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.user import UserCreate, UserInDB
from datetime import datetime
from bson import ObjectId
import secrets


class AuthService:
    def __init__(self, db):
        self.collection = db.users

    def verify_key(
        self, plain_key_bytes: bytes, hashed_key_bytes: bytes
    ) -> bool:
        """Проверяет API ключ против хеша. Ожидает уже bytes."""
        return bcrypt.checkpw(plain_key_bytes, hashed_key_bytes)

    def hash_key(self, plain_key: str) -> bytes:
        """Хеширует API ключ. Возвращает bytes."""
        return bcrypt.hashpw(plain_key.encode("utf-8"), bcrypt.gensalt())

    def generate_api_key(self) -> str:
        """Генерирует безопасный случайный API ключ."""
        return f"sv_live_{secrets.token_urlsafe(32)}"

    async def create_user(self, user_data: UserCreate) -> dict:
        """
        Создает пользователя и возвращает сгенерированный API ключ.
        В БД сохраняется только хеш.
        """
        plain_api_key = self.generate_api_key()
        hashed_api_key = self.hash_key(plain_api_key)  # Возвращает bytes

        user_doc = {
            "name": user_data.name,
            "hashed_api_key": hashed_api_key,
            "is_active": True,
            "created_at": datetime.utcnow(),
        }

        result = await self.collection.insert_one(user_doc)

        return {
            "id": str(result.inserted_id),
            "name": user_data.name,
            "api_key": plain_api_key,
        }

    async def get_user_by_key(self, plain_api_key: str) -> UserInDB | None:
        """Находит пользователя по API ключу."""
        # Конвертируем искомый ключ в байты один раз
        key_bytes = plain_api_key.encode("utf-8")

        async for user_doc in self.collection.find({"is_active": True}):
            stored_hash = user_doc["hashed_api_key"]

            # Защита: если из БД пришла строка (редкий случай), конвертируем
            if isinstance(stored_hash, str):
                stored_hash = stored_hash.encode("utf-8")

            # Сравниваем байты с байтами
            if self.verify_key(key_bytes, stored_hash):
                return UserInDB(
                    id=str(user_doc["_id"]),
                    name=user_doc["name"],
                    hashed_api_key=user_doc["hashed_api_key"],
                    created_at=user_doc["created_at"],
                )
        return None
