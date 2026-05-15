"""Сервис для управления секретами."""

from datetime import datetime
from typing import List

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.secret import SecretCreate, SecretResponse, SecretUpdate
from app.services.crypto import crypto_service
from app.utils.helpers import to_binary


class SecretService:
    """Класс для работы с секретами проектов."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.secrets
        self.projects = db.projects

    async def create_secret(
        self, project_id: str, secret_data: SecretCreate, encrypted_project_key: bytes
    ) -> SecretResponse:
        """Создает и шифрует новый секрет."""
        from app.services.audit import audit_service

        encrypted_value = crypto_service.encrypt_secret(
            secret_data.value, encrypted_project_key
        )

        secret_doc = {
            "project_id": project_id,
            "key": secret_data.key,
            "description": secret_data.description,
            "encrypted_value": to_binary(encrypted_value),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        result = await self.collection.insert_one(secret_doc)
        secret_id = str(result.inserted_id)

        await audit_service.log_secret_access(
            user_id="system",
            project_id=project_id,
            secret_id=secret_id,
            action="create",
            success=True,
        )

        return SecretResponse(
            id=secret_id,
            project_id=project_id,
            key=secret_data.key,
            value=secret_data.value,
            description=secret_data.description,
            updated_at=secret_doc["updated_at"],
        )

    async def get_secret(
        self, secret_id: str, encrypted_project_key: bytes
    ) -> SecretResponse | None:
        """Получает и расшифровывает секрет."""
        if not ObjectId.is_valid(secret_id):
            return None

        doc = await self.collection.find_one({"_id": ObjectId(secret_id)})
        if not doc:
            return None

        # Расшифровываем значение
        decrypted_value = crypto_service.decrypt_secret(
            doc["encrypted_value"], encrypted_project_key
        )

        return SecretResponse(
            id=str(doc["_id"]),
            project_id=doc["project_id"],
            key=doc["key"],
            value=decrypted_value,
            description=doc.get("description"),
            updated_at=doc["updated_at"],
        )

    async def list_secrets_by_project(
        self, project_id: str, encrypted_project_key: bytes
    ) -> List[SecretResponse]:
        """Возвращает все расшифрованные секреты проекта."""
        cursor = self.collection.find({"project_id": project_id})
        secrets = []
        async for doc in cursor:
            decrypted_value = crypto_service.decrypt_secret(
                doc["encrypted_value"], encrypted_project_key
            )
            secrets.append(
                SecretResponse(
                    id=str(doc["_id"]),
                    project_id=doc["project_id"],
                    key=doc["key"],
                    value=decrypted_value,
                    description=doc.get("description"),
                    updated_at=doc["updated_at"],
                )
            )
        return secrets

    async def delete_secret(self, secret_id: str, owner_id: str) -> bool:
        """Удаляет секрет, проверяя владельца проекта."""
        from app.services.audit import audit_service

        if not ObjectId.is_valid(secret_id):
            return False
        
        doc = await self.collection.find_one({"_id": ObjectId(secret_id)})
        if not doc:
            return False
        
        project = await self.projects.find_one({
            "_id": ObjectId(doc["project_id"]),
            "owner_id": owner_id
        })
        if not project:
            return False
        
        await self.collection.delete_one({"_id": ObjectId(secret_id)})

        await audit_service.log_secret_access(
            user_id=owner_id,
            project_id=doc["project_id"],
            secret_id=secret_id,
            action="delete",
            success=True,
        )
        return True

    async def delete_secrets_by_project(self, project_id: str):
        """Удаляет все секреты, связанные с проектом."""
        result = await self.collection.delete_many({"project_id": project_id})
        return result.deleted_count
