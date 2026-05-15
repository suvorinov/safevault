from typing import Optional
from bson import ObjectId

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_database
from app.services.auth import AuthService
from app.services.project_service import ProjectService
from app.services.secret_service import SecretService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


async def get_auth_user(request: Request, db: AsyncIOMotorDatabase):
    """Получает авторизованного пользователя или None."""
    api_key = request.cookies.get("api_key")
    if not api_key:
        return None
    auth_service = AuthService(db)
    ip_address = request.client.host if request.client else None
    return await auth_service.get_user_by_key(api_key, ip_address=ip_address)


def require_auth(request: Request, db: AsyncIOMotorDatabase):
    """Требует авторизации, возвращает user или вызывает redirect."""
    import asyncio
    loop = asyncio.get_event_loop()
    user = loop.run_until_complete(get_auth_user(request, db))
    if not user:
        return RedirectResponse(url="/", status_code=303)
    return user


# --- Pages ---


@router.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login", response_class=HTMLResponse)
async def login_post(
    request: Request,
    api_key: str = Form(...),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_key(api_key)
    if not user:
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": "Invalid API Key"}
        )

    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(key="api_key", value=api_key, httponly=True)
    return response


@router.get("/logout")
async def logout():
    """Удаляет сессионную cookie и перенаправляет на страницу входа."""
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("api_key")
    return response


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request, db: AsyncIOMotorDatabase = Depends(get_database)
):
    user = await get_auth_user(request, db)
    if not user:
        return RedirectResponse(url="/", status_code=303)

    project_service = ProjectService(db)
    projects = await project_service.list_projects_by_owner(user.id)

    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "projects": projects, "api_key": user.id}
    )


@router.get("/project/{project_id}", response_class=HTMLResponse)
async def project_detail(
    request: Request, project_id: str, db: AsyncIOMotorDatabase = Depends(get_database)
):
    user = await get_auth_user(request, db)
    if not user:
        return RedirectResponse(url="/")

    project_service = ProjectService(db)
    project = await project_service.get_project(project_id, owner_id=user.id)
    if not project:
        raise HTTPException(status_code=404)

    secret_service = SecretService(db)
    secrets = await secret_service.list_secrets_by_project(
        project_id, project.encrypted_key
    )

    return templates.TemplateResponse(
        "project_detail.html",
        {
            "request": request,
            "project": project,
            "secrets": secrets,
            "api_key": user.id,
        },
    )


@router.post("/create-project")
async def create_project_web(
    request: Request,
    name: str = Form(...),
    description: str = Form(default=""),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    user = await get_auth_user(request, db)
    if not user:
        return RedirectResponse(url="/")

    from app.models.project import ProjectCreate

    project_service = ProjectService(db)
    await project_service.create_project(
        ProjectCreate(name=name, description=description), owner_id=user.id
    )

    return RedirectResponse(url="/dashboard", status_code=303)


@router.post("/add-secret/{project_id}", response_class=HTMLResponse)
async def add_secret_web(
    request: Request,
    project_id: str,
    key: str = Form(...),
    value: str = Form(...),
    description: str = Form(default=""),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    user = await get_auth_user(request, db)
    if not user:
        return HTMLResponse(content="Unauthorized", status_code=401)

    project_service = ProjectService(db)
    project = await project_service.get_project(project_id, owner_id=user.id)

    if not project:
        return HTMLResponse(content="Project not found", status_code=404)

    secret_service = SecretService(db)
    from app.models.secret import SecretCreate

    secret_data = SecretCreate(key=key, value=value, description=description)

    await secret_service.create_secret(project_id, secret_data, project.encrypted_key)

    secrets = await secret_service.list_secrets_by_project(
        project_id, project.encrypted_key
    )

    return templates.TemplateResponse(
        "partials/_secrets_list.html", {"request": request, "secrets": secrets}
    )


@router.post("/delete-secret/{secret_id}")
async def delete_secret_web(
    request: Request, secret_id: str, db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Удаляет секрет по ID через Web UI."""
    user = await get_auth_user(request, db)
    if not user:
        return HTMLResponse(content="Unauthorized", status_code=401)

    secret_service = SecretService(db)
    success = await secret_service.delete_secret(secret_id, owner_id=user.id)

    if not success:
        return HTMLResponse(content="Secret not found", status_code=404)

    return {"status": "deleted"}


@router.post("/delete-project/{project_id}")
async def delete_project_web(
    request: Request,
    project_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    user = await get_auth_user(request, db)
    if not user:
        return RedirectResponse(url="/")

    project_service = ProjectService(db)
    project = await project_service.get_project(project_id, owner_id=user.id)
    if not project:
        return RedirectResponse(url="/dashboard")

    secret_service = SecretService(db)
    await secret_service.delete_secrets_by_project(project_id)
    await project_service.delete_project(project_id)

    return RedirectResponse(url="/dashboard", status_code=303)