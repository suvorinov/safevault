"""Main application entry point."""

import logging

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.database import connect_to_mongo, close_mongo_connection, get_database
from app.config import get_settings
from app.routers import (auth_router, project_router, secret_router, web_router)
from app.utils.rate_limit import limiter
from app.services.audit import init_audit_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    init_audit_service(get_database())
    logger.info(f"{settings.app_name} started")
    yield
    await close_mongo_connection()
    logger.info(f"{settings.app_name} stopped")


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(auth_router.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(project_router.router, prefix="/api/v1/projects", tags=["Projects"])
app.include_router(secret_router.router, prefix="/api/v1/secrets", tags=["Secrets"])
app.include_router(web_router.router, tags=["Web UI"])


@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.app_name}. Visit /docs for API documentation.",
        "hint": "Use POST /api/v1/auth/register to get an API Key first.",
    }
