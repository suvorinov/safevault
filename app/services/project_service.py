"""Сервис для управления проектами."""
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.project import ProjectCreate, ProjectInDB
from app.services.crypto import crypto_service
from app.utils.helpers import to_binary
from datetime import datetime
from bson import ObjectId

class ProjectService:
    """Класс, инкапсулирующий логику работы с проектами."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.projects

    async def create_project(self, project_data: ProjectCreate) -> ProjectInDB:
        """
        Создает новый проект.
        Генерирует уникальный ключ шифрования (Data Key) для проекта,
        шифрует его Master Key и сохраняет в БД.
        """
        # 1. Генерируем Data Key (plain) и его зашифрованную версию (encrypted)
        plain_key, encrypted_key = crypto_service.generate_data_key()

        # 2. Формируем документ для БД
        project_doc = {
            "name": project_data.name,
            "description": project_data.description,
            "encrypted_key": to_binary(encrypted_key),
            "created_at": datetime.utcnow()
        }

        # 3. Вставка в БД
        result = await self.collection.insert_one(project_doc)
        
        # Возвращаем модель (в реальности plain_key мы не сохраняем, но он нужен, 
        # если мы хотим сразу что-то зашифровать в рамках транзакции, 
        # но в KISS архитектуре клиент запросит ключ потом)
        return ProjectInDB(
            id=str(result.inserted_id),
            name=project_doc["name"],
            description=project_doc["description"],
            encrypted_key=encrypted_key,
            created_at=project_doc["created_at"]
        )

    async def get_project(self, project_id: str) -> ProjectInDB | None:
        """Получает проект по ID."""
        if not ObjectId.is_valid(project_id):
            return None
        
        doc = await self.collection.find_one({"_id": ObjectId(project_id)})
        if doc:
            return ProjectInDB(
                id=str(doc["_id"]),
                name=doc["name"],
                description=doc.get("description"),
                encrypted_key=doc["encrypted_key"],
                created_at=doc["created_at"]
            )
        return None

    async def list_projects(self):
        """Возвращает список всех проектов (без ключей шифрования)."""
        # Проецируем без encrypted_key для безопасности
        cursor = self.collection.find({}, {"encrypted_key": 0})
        projects = []
        async for doc in cursor:
            projects.append({
                "id": str(doc["_id"]),
                "name": doc["name"],
                "description": doc.get("description"),
                "created_at": doc["created_at"]
            })
        return projects
