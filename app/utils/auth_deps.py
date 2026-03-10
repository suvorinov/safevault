"""Зависимости (Dependencies) для авторизации."""

from fastapi import Depends, HTTPException, status, Header
from app.database import get_database
from app.services.auth import AuthService
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.user import UserInDB


async def get_current_user(
    x_api_key: str = Header(..., alias="X-API-Key"),  # Ожидаем ключ в заголовке
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> UserInDB:
    """
    Извлекает пользователя по API ключу из заголовка.
    Выбрасывает 401, если ключ неверен.
    """
    service = AuthService(db)
    user = await service.get_user_by_key(x_api_key)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key"
        )
    return user
