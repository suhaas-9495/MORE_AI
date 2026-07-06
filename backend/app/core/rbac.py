from enum import Enum
from typing import List
from fastapi import HTTPException, status


class Role(str, Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"


# permission matrix — what each role can do
ROLE_PERMISSIONS = {
    Role.ADMIN: [
        "agent:run", "agent:read",
        "eval:run", "eval:read",
        "rag:write", "rag:read",
        "registry:read", "registry:write",
        "audit:read", "users:manage",
    ],
    Role.DEVELOPER: [
        "agent:run", "agent:read",
        "eval:run", "eval:read",
        "rag:write", "rag:read",
        "registry:read",
    ],
    Role.VIEWER: [
        "agent:read",
        "eval:read",
        "rag:read",
        "registry:read",
    ],
}


def get_user_permissions(role: str) -> List[str]:
    try:
        return ROLE_PERMISSIONS[Role(role)]
    except ValueError:
        return ROLE_PERMISSIONS[Role.VIEWER]


def require_permission(permission: str):
    """
    FastAPI dependency factory — use like:
    Depends(require_permission("agent:run"))
    Raises 403 if user's role doesn't have the permission.
    """
    async def checker(current_user: dict = __import__(
        'fastapi').Depends(
        __import__('backend.app.core.dependencies',
                   fromlist=['get_current_user']).get_current_user)):
        role = current_user.get("role", Role.VIEWER)
        permissions = get_user_permissions(role)
        if permission not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: requires '{permission}'",
            )
        return current_user
    return checker