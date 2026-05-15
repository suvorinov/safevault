"""Зависимости (Dependencies) для авторизации."""

from fastapi import Depends, Header, HTTPException, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_database
from app.models.user import UserInDB
from app.services.auth import AuthService


async def get_current_user(
    request: Request,
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> UserInDB:
    """
    Извлекает пользователя по API ключу из заголовка.
    Логирует попытки аутентификации.
    """
    ip_address = request.client.host if request.client else None
    service = AuthService(db)
    user = await service.get_user_by_key(x_api_key, ip_address=ip_address)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key"
        )
    return user