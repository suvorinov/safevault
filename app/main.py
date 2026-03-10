"""Main application entry point."""

from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import connect_to_mongo, close_mongo_connection
from app.config import get_settings

# Импорт всех роутеров
from app.routers import project_router, secret_router, auth_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    yield
    # Shutdown
    await close_mongo_connection()


app = FastAPI(
    title=settings.app_name,
    description="Self-hosted secrets manager with Envelope Encryption and API Key Auth",
    version="1.0.0",
    lifespan=lifespan,
)

# Подключение роутеров
# Auth не требует защиты (там регистрация)
app.include_router(auth_router.router, prefix="/api/v1/auth", tags=["Auth"])

# Projects и Secrets требуют защиты (через Depends в роутерах)
app.include_router(
    project_router.router, prefix="/api/v1/projects", tags=["Projects"]
)
app.include_router(
    secret_router.router, prefix="/api/v1/secrets", tags=["Secrets"]
)


@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.app_name}. Visit /docs for API documentation.",
        "hint": "Use POST /api/v1/auth/register to get an API Key first.",
    }
