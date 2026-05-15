"""Pydantic models for Secret entity."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SecretBase(BaseModel):
    """Base model for Secret."""

    key: str = Field(..., description="Название переменной (например, API_KEY)")
    value: str = Field(..., description="Значение секрета (будет зашифровано)")
    description: Optional[str] = Field(
        None, description="Описание для чего нужен секрет"
    )


class SecretCreate(SecretBase):
    """Model for creating a secret."""

    pass


class SecretUpdate(BaseModel):
    """Model for updating a secret."""

    value: str
    description: Optional[str] = None


class SecretResponse(BaseModel):
    """Model for response to client (decrypted value)."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    project_id: str
    key: str
    value: str
    description: Optional[str]
    updated_at: datetime