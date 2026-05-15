"""Pydantic models for User entity."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    """Model for user registration."""

    model_config = ConfigDict(str_min_length=1)

    name: str = Field(..., description="Имя владельца ключа")


class UserInDB(BaseModel):
    """Model for user in database."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id")
    name: str
    hashed_api_key: bytes
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)