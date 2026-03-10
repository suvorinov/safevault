"""Pydantic models for Project entity."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId

class ProjectBase(BaseModel):
    """Base model for Project."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    """Model for creating a new project."""
    pass

class ProjectInDB(ProjectBase):
    """Model representing Project in Database."""
    id: str = Field(alias="_id")
    encrypted_key: bytes  # Encrypted Data Key
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {bytes: lambda v: v.decode('utf-8') if isinstance(v, bytes) else v}
