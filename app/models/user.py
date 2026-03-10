from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    name: str = Field(..., description="Имя владельца ключа")


class UserInDB(BaseModel):
    id: str = Field(alias="_id")
    name: str
    hashed_api_key: bytes  # bcrypt возвращает bytes, MongoDB хранит как Binary
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
