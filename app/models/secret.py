"""Pydantic модели для сущности Secret."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class SecretBase(BaseModel):
    """Базовая модель секрета."""
    key: str = Field(..., description="Название переменной (например, API_KEY)")
    value: str = Field(..., description="Значение секрета (будет зашифровано)")
    description: Optional[str] = Field(None, description="Описание для чего нужен секрет")

class SecretCreate(SecretBase):
    """Модель для создания секрета."""
    pass

class SecretUpdate(BaseModel):
    """Модель для обновления секрета."""
    value: str
    description: Optional[str] = None

class SecretInDB(BaseModel):
    """Модель секрета, хранящаяся в БД (с метаданными)."""
    id: str = Field(alias="_id")
    project_id: str
    key: str
    encrypted_value: bytes
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        # Для корректного отображения байтов в JSON при отладке
        json_encoders = {bytes: lambda v: "<encrypted>"}

class SecretResponse(BaseModel):
    """Модель ответа для клиента (расшифрованное значение)."""
    id: str
    project_id: str
    key: str
    value: str
    description: Optional[str]
    updated_at: datetime
