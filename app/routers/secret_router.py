"""API роутер для управления секретами."""

from fastapi import APIRouter, Depends, HTTPException
from app.database import get_database
from app.models.secret import SecretCreate, SecretResponse
from app.models.user import UserInDB
from app.services.secret_service import SecretService
from app.services.project_service import ProjectService
from app.utils.auth_deps import get_current_user
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter()


# Правильное получение сервисов
def get_secret_service(
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> SecretService:
    return SecretService(db)


def get_project_service(
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> ProjectService:
    return ProjectService(db)


@router.post(
    "/{project_id}",
    response_model=SecretResponse,
    summary="Добавить секрет в проект",
)
async def create_secret(
    project_id: str,
    secret_data: SecretCreate,
    secret_service: SecretService = Depends(get_secret_service),
    project_service: ProjectService = Depends(get_project_service),
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Добавляет новый секрет в указанный проект.
    Значение шифруется ключом проекта перед сохранением.
    """
    # 1. Проверяем проект и получаем ключ
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")

    # 2. Создаем секрет через secret_service
    return await secret_service.create_secret(
        project_id, secret_data, project.encrypted_key
    )


@router.get(
    "/{project_id}",
    response_model=list[SecretResponse],
    summary="Получить все секреты проекта",
)
async def list_secrets(
    project_id: str,
    secret_service: SecretService = Depends(get_secret_service),
    project_service: ProjectService = Depends(get_project_service),
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Возвращает список всех секретов проекта в расшифрованном виде.
    """
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")

    return await secret_service.list_secrets_by_project(
        project_id, project.encrypted_key
    )


@router.delete("/{secret_id}", summary="Удалить секрет")
async def delete_secret(
    secret_id: str,
    secret_service: SecretService = Depends(get_secret_service),
    current_user: UserInDB = Depends(get_current_user),
):
    """Удаляет секрет по его ID."""
    success = await secret_service.delete_secret(secret_id)
    if not success:
        raise HTTPException(status_code=404, detail="Секрет не найден")
    return {"status": "deleted"}
