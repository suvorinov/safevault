"""Роутер управления пользователями и ключами."""

from fastapi import APIRouter, Depends, Request
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_database
from app.models.user import UserCreate
from app.services.auth import AuthService
from app.utils.rate_limit import limiter

router = APIRouter()


def get_auth_service(
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> AuthService:
    return AuthService(db)


@router.post("/register", summary="Создать нового пользователя и получить API Key")
@limiter.limit("5/minute")
async def register_user(
    request: Request,
    user_data: UserCreate,
    service: AuthService = Depends(get_auth_service),
):
    """
    Создает сервисный аккаунт.
    Возвращает API ключ в открытом виде. СОХРАНИТЕ ЕГО!
    Лимит: 5 регистраций в минуту.
    """
    return await service.create_user(user_data)
