"""T1 & T7: RBAC birim testleri"""
import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException

from app.models.user import User, UserRole
from app.core.rbac import has_permission, require_owner_or_admin, Permission


def make_user(role: UserRole) -> User:
    user = MagicMock(spec=User)
    user.role = role
    user.id = 1
    return user


def test_admin_has_all_permissions():
    admin = make_user(UserRole.ADMIN)
    for perm in Permission:
        assert has_permission(admin, perm)


def test_user_cannot_access_admin_panel():
    user = make_user(UserRole.USER)
    assert not has_permission(user, Permission.ADMIN_PANEL)
    assert not has_permission(user, Permission.PURCHASE_REVIEW)
    assert not has_permission(user, Permission.AUDIT_LOGS_READ)


def test_user_can_create_reports():
    user = make_user(UserRole.USER)
    assert has_permission(user, Permission.REPORT_CREATE)
    assert has_permission(user, Permission.REPORT_EXPORT)
    assert has_permission(user, Permission.AI_USE)


def test_require_owner_or_admin_passes_for_owner():
    user = make_user(UserRole.USER)
    user.id = 5
    require_owner_or_admin(resource_owner_id=5, current_user=user)  # should not raise


def test_require_owner_or_admin_raises_for_other_user():
    user = make_user(UserRole.USER)
    user.id = 5
    with pytest.raises(HTTPException) as exc_info:
        require_owner_or_admin(resource_owner_id=99, current_user=user)
    assert exc_info.value.status_code == 403


def test_admin_bypasses_owner_check():
    admin = make_user(UserRole.ADMIN)
    admin.id = 1
    require_owner_or_admin(resource_owner_id=99, current_user=admin)  # should not raise
