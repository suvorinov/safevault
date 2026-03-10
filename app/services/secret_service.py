"""Сервис для управления секретами."""
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.secret import SecretCreate, SecretUpdate, SecretInDB, SecretResponse
from app.services.crypto import crypto_service
from app.utils.helpers import to_binary
from datetime import datetime
from bson import ObjectId
from typing import List

class SecretService:
    """Класс для работы с секретами проектов."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.secrets

    async def create_secret(self, project_id: str, secret_data: SecretCreate, encrypted_project_key: bytes) -> SecretResponse:
        """
        Создает и шифрует новый секрет.
        Принимает уже извлеченный из проекта ключ шифрования.
        """
        # Шифруем значение секрета ключом проекта
        encrypted_value = crypto_service.encrypt_secret(secret_data.value, encrypted_project_key)

        secret_doc = {
            "project_id": project_id,
            "key": secret_data.key,
            "description": secret_data.description,
            "encrypted_value": to_binary(encrypted_value),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        result = await self.collection.insert_one(secret_doc)

        # Возвращаем ответ (включая исходное значение, так как это ответ на создание)
        return SecretResponse(
            id=str(result.inserted_id),
            project_id=project_id,
            key=secret_data.key,
            value=secret_data.value,
            description=secret_data.description,
            updated_at=secret_doc["updated_at"]
        )

    async def get_secret(self, secret_id: str, encrypted_project_key: bytes) -> SecretResponse | None:
        """Получает и расшифровывает секрет."""
        if not ObjectId.is_valid(secret_id):
            return None

        doc = await self.collection.find_one({"_id": ObjectId(secret_id)})
        if not doc:
            return None

        # Расшифровываем значение
        decrypted_value = crypto_service.decrypt_secret(doc["encrypted_value"], encrypted_project_key)

        return SecretResponse(
            id=str(doc["_id"]),
            project_id=doc["project_id"],
            key=doc["key"],
            value=decrypted_value,
            description=doc.get("description"),
            updated_at=doc["updated_at"]
        )

    async def list_secrets_by_project(self, project_id: str, encrypted_project_key: bytes) -> List[SecretResponse]:
        """Возвращает все расшифрованные секреты проекта."""
        cursor = self.collection.find({"project_id": project_id})
        secrets = []
        async for doc in cursor:
            decrypted_value = crypto_service.decrypt_secret(doc["encrypted_value"], encrypted_project_key)
            secrets.append(SecretResponse(
                id=str(doc["_id"]),
                project_id=doc["project_id"],
                key=doc["key"],
                value=decrypted_value,
                description=doc.get("description"),
                updated_at=doc["updated_at"]
            ))
        return secrets

    async def delete_secret(self, secret_id: str) -> bool:
        """Удаляет секрет."""
        if not ObjectId.is_valid(secret_id):
            return False
        result = await self.collection.delete_one({"_id": ObjectId(secret_id)})
        return result.deleted_count > 0
