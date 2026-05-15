"""Pydantic models for Project entity."""

from datetime import datetime
from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field


class ProjectBase(BaseModel):
    """Base model for Project."""

    model_config = ConfigDict(str_min_length=1)

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    """Model for creating a new project."""

    pass


class ProjectInDB(ProjectBase):
    """Model representing Project in Database."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id")
    owner_id: str
    encrypted_key: bytes
    created_at: datetime = Field(default_factory=datetime.utcnow)