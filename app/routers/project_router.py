"""API роутер для управления проектами."""

from fastapi import APIRouter, Depends, HTTPException
from app.database import get_database
from app.models.project import ProjectCreate, ProjectInDB
from app.models.user import UserInDB  # Для типизации current_user
from app.services.project_service import ProjectService
from app.utils.auth_deps import get_current_user  # Наша защита
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter()


def get_project_service(
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> ProjectService:
    """Зависимость для получения экземпляра ProjectService."""
    return ProjectService(db)


@router.post("/", response_model=ProjectInDB, summary="Создать новый проект")
async def create_project(
    project_data: ProjectCreate,
    service: ProjectService = Depends(get_project_service),
    current_user: UserInDB = Depends(
        get_current_user
    ),  # ЗАЩИТА: Требуется API Key
):
    """
    Создает новый проект для хранения секретов.
    Автоматически генерирует ключ шифрования для проекта.
    """
    # Можно добавить логику привязки проекта к user_id: project_data.owner_id = current_user.id
    return await service.create_project(project_data)


@router.get("/", summary="Получить список проектов")
async def list_projects(
    service: ProjectService = Depends(get_project_service),
    current_user: UserInDB = Depends(get_current_user),  # ЗАЩИТА
):
    """Возвращает список всех проектов (без секретных ключей)."""
    return await service.list_projects()


@router.get(
    "/{project_id}", response_model=ProjectInDB, summary="Получить проект по ID"
)
async def get_project(
    project_id: str,
    service: ProjectService = Depends(get_project_service),
    current_user: UserInDB = Depends(get_current_user),  # ЗАЩИТА
):
    """Возвращает информацию о проекте."""
    project = await service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")
    return project
