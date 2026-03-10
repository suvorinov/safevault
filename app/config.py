"""Application configuration module."""
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    app_name: str = Field(default="SafeVault", alias="APP_NAME")
    debug: bool = Field(default=False, alias="DEBUG")
    secret_key: str = Field(..., alias="SECRET_KEY")
    
    mongo_uri: str = Field(..., alias="MONGO_URI")
    mongo_db_name: str = Field(..., alias="MONGO_DB_NAME")
    
    master_key: str = Field(..., alias="MASTER_KEY")

    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache()
def get_settings() -> Settings:
    """Returns a cached instance of the Settings object."""
    return Settings()
