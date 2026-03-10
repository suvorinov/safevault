"""Роутер управления пользователями и ключами."""

from fastapi import APIRouter, Depends
from app.database import get_database
from app.services.auth import AuthService
from app.models.user import UserCreate
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter()


def get_auth_service(
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> AuthService:
    return AuthService(db)


@router.post(
    "/register", summary="Создать нового пользователя и получить API Key"
)
async def register_user(
    user_data: UserCreate, service: AuthService = Depends(get_auth_service)
):
    """
    Создает сервисный аккаунт.
    Возвращает API ключ в открытом виде. СОХРАНИТЕ ЕГО!
    """
    return await service.create_user(user_data)
