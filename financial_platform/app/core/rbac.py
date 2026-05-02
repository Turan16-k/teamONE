"""
T1 & T7: Rol Bazlı Erişim Kontrolü (RBAC)
Admin ve kullanıcı panelleri arasında kod düzeyinde yetkilendirme katmanı.
"""
from enum import Enum
from typing import List, Callable
from functools import wraps
from fastapi import HTTPException, status
from app.models.user import User, UserRole


class Permission(str, Enum):
    # Kullanıcı yönetimi
    USER_READ = "user:read"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    # Şirket yönetimi
    COMPANY_READ = "company:read"
    COMPANY_CREATE = "company:create"
    COMPANY_UPDATE = "company:update"
    COMPANY_DELETE = "company:delete"

    # Finansal rapor
    REPORT_READ = "report:read"
    REPORT_CREATE = "report:create"
    REPORT_UPDATE = "report:update"
    REPORT_DELETE = "report:delete"
    REPORT_EXPORT = "report:export"

    # AI operasyonları
    AI_USE = "ai:use"
    AI_LOGS_READ = "ai:logs:read"

    # Abonelik ve satın alma
    SUBSCRIPTION_READ = "subscription:read"
    SUBSCRIPTION_MANAGE = "subscription:manage"
    PURCHASE_REQUEST = "purchase:request"
    PURCHASE_REVIEW = "purchase:review"       # sadece admin

    # Sistem
    ADMIN_PANEL = "admin:panel"
    AUDIT_LOGS_READ = "audit:logs:read"


# Her role atanan izin seti
ROLE_PERMISSIONS: dict[UserRole, List[Permission]] = {
    UserRole.ADMIN: list(Permission),  # admin tüm izinlere sahip

    UserRole.ANALYST: [
        Permission.COMPANY_READ,
        Permission.REPORT_READ,
        Permission.REPORT_CREATE,
        Permission.REPORT_UPDATE,
        Permission.REPORT_EXPORT,
        Permission.AI_USE,
        Permission.SUBSCRIPTION_READ,
    ],

    UserRole.USER: [
        Permission.COMPANY_READ,
        Permission.COMPANY_CREATE,
        Permission.COMPANY_UPDATE,
        Permission.REPORT_READ,
        Permission.REPORT_CREATE,
        Permission.REPORT_UPDATE,
        Permission.REPORT_EXPORT,
        Permission.AI_USE,
        Permission.SUBSCRIPTION_READ,
        Permission.PURCHASE_REQUEST,
    ],
}


def has_permission(user: User, permission: Permission) -> bool:
    user_permissions = ROLE_PERMISSIONS.get(user.role, [])
    return permission in user_permissions


def require_permission(*permissions: Permission) -> Callable:
    """FastAPI dependency olarak kullanılır: @router.get(..., dependencies=[Depends(require_permission(...))])"""
    def dependency(current_user: User) -> User:
        for perm in permissions:
            if not has_permission(current_user, perm):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Bu işlem için yetkiniz yok: {perm.value}",
                )
        return current_user
    return dependency


def require_admin(current_user: User) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu endpoint yalnızca admin kullanıcılar içindir.",
        )
    return current_user


def require_owner_or_admin(resource_owner_id: int, current_user: User) -> None:
    """Kaynak sahibi veya admin olma kontrolü."""
    if current_user.role != UserRole.ADMIN and current_user.id != resource_owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu kaynağa erişim yetkiniz yok.",
        )
