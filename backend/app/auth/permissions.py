"""Role-Based Access Control (RBAC) permission dependencies."""

from typing import List

from fastapi import Depends

from app.auth.dependencies import get_current_active_user
from app.core.exceptions import AuthorizationException
from app.models.user import User, UserRole


class RoleChecker:
    """Dependency callable verifying if current user possesses one of the permitted roles."""

    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_active_user)) -> User:
        if user.role not in self.allowed_roles:
            raise AuthorizationException(f"Role '{user.role.value}' is not authorized to access this resource")
        return user


# Convenience RBAC Guards
require_admin = RoleChecker([UserRole.ADMIN])
require_data_scientist = RoleChecker([UserRole.ADMIN, UserRole.DATA_SCIENTIST])
require_authenticated_user = RoleChecker([UserRole.ADMIN, UserRole.DATA_SCIENTIST, UserRole.USER])


def require_role(*roles: UserRole) -> RoleChecker:
    """Dynamic role check helper."""
    return RoleChecker(list(roles))
