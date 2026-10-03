"""
Namespace Resolution and Boundary Enforcement for Step 31: Semantic Cache.
"""
import uuid
from typing import Optional

from backend.app.services.cache.constants import CacheNamespace
from backend.app.services.cache.errors import CacheSecurityError


class NamespaceResolver:
    """
    Resolves and enforces the target namespace for cache entries.
    Guarantees user-private responses remain user-scoped and never leak into workspace or global cache.
    """

    @classmethod
    def resolve_namespace(
        cls,
        user_id: Optional[uuid.UUID] = None,
        project_id: Optional[uuid.UUID] = None,
        is_user_private: bool = False,
        requested_namespace: Optional[CacheNamespace] = None,
        allow_global: bool = False,
    ) -> CacheNamespace:
        """
        Determines the appropriate cache namespace.
        """
        if is_user_private:
            return CacheNamespace.USER

        if requested_namespace == CacheNamespace.GLOBAL:
            if not allow_global:
                raise CacheSecurityError("Global cache namespace is forbidden by default security policy.")
            return CacheNamespace.GLOBAL

        if requested_namespace == CacheNamespace.USER and user_id:
            return CacheNamespace.USER

        if requested_namespace == CacheNamespace.PROJECT and project_id:
            return CacheNamespace.PROJECT

        if project_id and not requested_namespace:
            return CacheNamespace.PROJECT

        return CacheNamespace.WORKSPACE

    @classmethod
    def validate_namespace_access(
        cls,
        entry_namespace: str,
        entry_user_id: Optional[uuid.UUID],
        entry_project_id: Optional[uuid.UUID],
        requesting_user_id: Optional[uuid.UUID],
        requesting_project_id: Optional[uuid.UUID],
    ) -> bool:
        """
        Enforces that a user can only read an entry if they satisfy the namespace criteria.
        """
        if entry_namespace == CacheNamespace.USER.value:
            # User namespace entries can ONLY be accessed by the same user
            if not entry_user_id or not requesting_user_id or entry_user_id != requesting_user_id:
                return False

        elif entry_namespace == CacheNamespace.PROJECT.value:
            # Project namespace entries require matching project
            if entry_project_id and requesting_project_id and entry_project_id != requesting_project_id:
                return False

        return True
