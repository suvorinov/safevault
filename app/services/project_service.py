"""Сервис для управления проектами."""

from datetime import datetime
from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.project import ProjectCreate, ProjectInDB
from app.services.crypto import crypto_service
from app.utils.helpers import to_binary


class ProjectService:
    """Класс, инкапсулирующий логику работы с проектами."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.projects

    async def create_project(
        self, project_data: ProjectCreate, owner_id: str
    ) -> ProjectInDB:
        """Создает новый проект, привязанный к владельцу."""
        from app.services.audit import audit_service

        plain_key, encrypted_key = crypto_service.generate_data_key()

        project_doc = {
            "name": project_data.name,
            "description": project_data.description,
            "owner_id": owner_id,
            "encrypted_key": to_binary(encrypted_key),
            "created_at": datetime.utcnow(),
        }

        result = await self.collection.insert_one(project_doc)
        project_id = str(result.inserted_id)

        await audit_service.log_project_access(
            user_id=owner_id,
            project_id=project_id,
            action="create",
            success=True,
        )

        return ProjectInDB(
            id=project_id,
            name=project_doc["name"],
            description=project_doc["description"],
            owner_id=owner_id,
            encrypted_key=encrypted_key,
            created_at=project_doc["created_at"],
        )

    async def get_project(
        self, project_id: str, owner_id: Optional[str] = None
    ) -> Optional[ProjectInDB]:
        """Получает проект по ID. Если указан owner_id, проверяет владельца."""
        if not ObjectId.is_valid(project_id):
            return None

        query = {"_id": ObjectId(project_id)}
        if owner_id:
            query["owner_id"] = owner_id

        doc = await self.collection.find_one(query)
        if doc:
            return ProjectInDB(
                id=str(doc["_id"]),
                name=doc["name"],
                description=doc.get("description"),
                owner_id=doc["owner_id"],
                encrypted_key=doc["encrypted_key"],
                created_at=doc["created_at"],
            )
        return None

    async def list_projects_by_owner(self, owner_id: str) -> list:
        """Возвращает список проектов конкретного владельца."""
        cursor = self.collection.find(
            {"owner_id": owner_id}, {"encrypted_key": 0}
        )
        projects = []
        async for doc in cursor:
            projects.append(
                {
                    "id": str(doc["_id"]),
                    "name": doc["name"],
                    "description": doc.get("description"),
                    "created_at": doc["created_at"],
                }
            )
        return projects

    async def delete_project(self, project_id: str, owner_id: str = None) -> bool:
        """Удаляет проект. Опционально проверяет владельца."""
        from app.services.audit import audit_service

        if not ObjectId.is_valid(project_id):
            return False
        
        query = {"_id": ObjectId(project_id)}
        if owner_id:
            query["owner_id"] = owner_id
        
        result = await self.collection.delete_one(query)
        
        if result.deleted_count > 0 and owner_id:
            await audit_service.log_project_access(
                user_id=owner_id,
                project_id=project_id,
                action="delete",
                success=True,
            )
        
        return result.deleted_count > 0