"""API роутер для управления проектами."""

from fastapi import APIRouter, Depends, HTTPException, Request
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_database
from app.models.project import ProjectCreate, ProjectInDB
from app.models.user import UserInDB
from app.services.project_service import ProjectService
from app.services.secret_service import SecretService
from app.utils.auth_deps import get_current_user
from app.utils.rate_limit import limiter

router = APIRouter()


def get_project_service(
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> ProjectService:
    return ProjectService(db)


def get_secret_service(
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> SecretService:
    return SecretService(db)


@router.post("/", response_model=ProjectInDB, summary="Создать новый проект")
@limiter.limit("20/minute")
async def create_project(
    request: Request,
    project_data: ProjectCreate,
    service: ProjectService = Depends(get_project_service),
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Создает новый проект для хранения секретов.
    Автоматически генерирует ключ шифрования для проекта.
    Привязывает проект к текущему пользователю. Лимит: 20 в минуту.
    """
    return await service.create_project(project_data, owner_id=current_user.id)


@router.get("/", summary="Получить список проектов")
@limiter.limit("60/minute")
async def list_projects(
    request: Request,
    service: ProjectService = Depends(get_project_service),
    current_user: UserInDB = Depends(get_current_user),
):
    """Возвращает список проектов текущего пользователя. Лимит: 60 в минуту."""
    return await service.list_projects_by_owner(current_user.id)


@router.get(
    "/{project_id}", response_model=ProjectInDB, summary="Получить проект по ID"
)
@limiter.limit("60/minute")
async def get_project(
    request: Request,
    project_id: str,
    service: ProjectService = Depends(get_project_service),
    current_user: UserInDB = Depends(get_current_user),
):
    """Возвращает информацию о проекте, принадлежащем пользователю. Лимит: 60 в минуту."""
    project = await service.get_project(project_id, owner_id=current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")
    return project


@router.delete("/{project_id}", summary="Удалить проект")
@limiter.limit("20/minute")
async def delete_project(
    request: Request,
    project_id: str,
    project_service: ProjectService = Depends(get_project_service),
    secret_service: SecretService = Depends(get_secret_service),
    current_user: UserInDB = Depends(get_current_user),
):
    """Удаляет проект и все связанные секреты. Лимит: 20 в минуту."""
    project = await project_service.get_project(project_id, owner_id=current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")
    await secret_service.delete_secrets_by_project(project_id)
    await project_service.delete_project(project_id)
    return {"status": "deleted"}