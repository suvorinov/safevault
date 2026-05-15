"""Application configuration module."""

from functools import lru_cache

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = ConfigDict(env_file=".env", extra="ignore")

    app_name: str = Field(default="SafeVault", alias="APP_NAME")
    debug: bool = Field(default=False, alias="DEBUG")
    secret_key: str = Field(..., alias="SECRET_KEY")

    mongo_uri: str = Field(..., alias="MONGO_URI")
    mongo_db_name: str = Field(..., alias="MONGO_DB_NAME")

    master_key: str = Field(..., alias="MASTER_KEY")


@lru_cache()
def get_settings() -> Settings:
    """Returns a cached instance of the Settings object."""
    return Settings()