"""Audit logging service."""

from datetime import datetime
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase


class AuditService:
    """Service for logging security-related events."""

    def __init__(self, db):
        self.collection = db.audit_logs if db is not None else None

    async def log(
        self,
        event_type: str,
        user_id: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        project_id: Optional[str] = None,
        action: str = "access",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[str] = None,
        success: bool = True,
    ):
        """Записывает событие в лог аудита."""
        if not self.collection:
            return
        doc = {
            "event_type": event_type,
            "user_id": user_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "project_id": project_id,
            "action": action,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "details": details,
            "success": success,
            "timestamp": datetime.utcnow(),
        }
        await self.collection.insert_one(doc)

    async def log_secret_access(
        self,
        user_id: str,
        project_id: str,
        secret_id: str,
        action: str,
        ip_address: str = None,
        success: bool = True,
    ):
        """Логирует доступ к секрету."""
        await self.log(
            event_type="secret_access",
            user_id=user_id,
            resource_type="secret",
            resource_id=secret_id,
            project_id=project_id,
            action=action,
            ip_address=ip_address,
            success=success,
        )

    async def log_project_access(
        self,
        user_id: str,
        project_id: str,
        action: str,
        ip_address: str = None,
        success: bool = True,
    ):
        """Логирует доступ к проекту."""
        await self.log(
            event_type="project_access",
            user_id=user_id,
            resource_type="project",
            resource_id=project_id,
            project_id=project_id,
            action=action,
            ip_address=ip_address,
            success=success,
        )

    async def log_auth_event(
        self,
        user_id: str,
        action: str,
        ip_address: str = None,
        success: bool = True,
        details: str = None,
    ):
        """Логирует событие аутентификации."""
        await self.log(
            event_type="auth",
            user_id=user_id,
            resource_type="user",
            resource_id=user_id,
            action=action,
            ip_address=ip_address,
            success=success,
            details=details,
        )


audit_service = AuditService(None)


def init_audit_service(db: AsyncIOMotorDatabase):
    """Инициализирует глобальный экземпляр AuditService."""
    global audit_service
    audit_service = AuditService(db)