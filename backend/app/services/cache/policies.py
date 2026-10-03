"""
Cache Policies and Governance for Step 31: Semantic Cache.
Enforces workspace cache settings, threshold bounds, safety constraints, and authorization.
"""
import uuid
from typing import Any, Dict, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.db.models.user import User
from backend.app.services.access_control.policies import PolicyEngine
from backend.app.services.access_control.permissions import (
    CACHE_READ,
    CACHE_CONFIGURE,
    CACHE_INVALIDATE,
    CACHE_DELETE,
)
from backend.app.services.cache.constants import (
    CACHE_DEFAULT_SEMANTIC_THRESHOLD,
    CACHE_DEFAULT_TTL_SECONDS,
    CACHE_MAX_RESPONSE_BYTES,
    CACHE_MAX_SEMANTIC_THRESHOLD,
    CACHE_MIN_SEMANTIC_THRESHOLD,
    CacheMode,
)
from backend.app.services.cache.errors import (
    CachePolicyViolationError,
    CacheSecurityError,
)
from backend.app.services.cache.schemas import CachePolicyConfig


class CachePolicyEngine:
    """
    Evaluates and enforces cache policy rules across workspaces and tenants.
    """

    _workspace_policies: Dict[uuid.UUID, CachePolicyConfig] = {}

    @classmethod
    async def get_workspace_policy(
        cls,
        db_or_workspace_id: Any,
        workspace_id: Optional[uuid.UUID] = None,
    ) -> CachePolicyConfig:
        """
        Retrieves active CachePolicyConfig for the workspace, or standard defaults.
        Accepts (workspace_id) or (db, workspace_id).
        """
        if isinstance(db_or_workspace_id, uuid.UUID):
            target_ws = db_or_workspace_id
        elif workspace_id:
            target_ws = workspace_id
        else:
            target_ws = uuid.uuid4()

        if target_ws in cls._workspace_policies:
            return cls._workspace_policies[target_ws]

        return CachePolicyConfig(
            enabled=True,
            default_mode=CacheMode.AUTO,
            semantic_enabled=True,
            semantic_threshold=CACHE_DEFAULT_SEMANTIC_THRESHOLD,
            default_ttl=CACHE_DEFAULT_TTL_SECONDS,
            max_entry_size=CACHE_MAX_RESPONSE_BYTES,
            allow_cross_model_cache=False,
            stale_while_revalidate=True,
            max_namespace_entries=10_000,
        )

    @classmethod
    def validate_policy_update(
        cls,
        new_policy: CachePolicyConfig,
    ) -> tuple[bool, str]:
        """Validates threshold ranges and policy constraints."""
        if (
            new_policy.semantic_threshold < CACHE_MIN_SEMANTIC_THRESHOLD
            or new_policy.semantic_threshold > CACHE_MAX_SEMANTIC_THRESHOLD
        ):
            return (
                False,
                f"Semantic threshold {new_policy.semantic_threshold:.2f} is outside the allowed safe range "
                f"[{CACHE_MIN_SEMANTIC_THRESHOLD:.2f}, {CACHE_MAX_SEMANTIC_THRESHOLD:.2f}].",
            )
        return True, "Valid"

    @classmethod
    async def save_workspace_policy(
        cls,
        db_or_ws_id: Any,
        workspace_id_or_policy: Any,
        policy: Optional[CachePolicyConfig] = None,
    ) -> CachePolicyConfig:
        """Saves workspace policy with bounds checking."""
        if policy is not None:
            target_ws = workspace_id_or_policy
            target_policy = policy
        elif isinstance(db_or_ws_id, uuid.UUID):
            target_ws = db_or_ws_id
            target_policy = workspace_id_or_policy
        else:
            target_ws = workspace_id_or_policy
            target_policy = policy

        is_valid, msg = cls.validate_policy_update(target_policy)
        if not is_valid:
            raise CachePolicyViolationError(msg)

        cls._workspace_policies[target_ws] = target_policy
        return target_policy

    @classmethod
    def update_workspace_policy(
        cls,
        workspace_id: uuid.UUID,
        new_policy: CachePolicyConfig,
    ) -> CachePolicyConfig:
        """
        Validates and updates workspace cache policy.
        Rejects out-of-range thresholds or dangerous configurations.
        """
        is_valid, msg = cls.validate_policy_update(new_policy)
        if not is_valid:
            raise CachePolicyViolationError(msg)

        if new_policy.default_ttl <= 0:
            raise CachePolicyViolationError("Default TTL must be a positive integer.")

        cls._workspace_policies[workspace_id] = new_policy
        logger.info(f"[CachePolicyEngine] Updated cache policy for workspace {workspace_id}")
        return new_policy

    @classmethod
    def verify_tenant_boundary(
        cls,
        user: User,
        organization_id: uuid.UUID,
    ) -> None:
        """
        Guarantees that a user belonging to Organization A cannot query, admit,
        or invalidate cache entries of Organization B.
        """
        if getattr(user, "is_superuser", False):
            return

        user_org = getattr(user, "organization_id", None)
        if user_org and user_org != organization_id:
            logger.warning(
                f"[CachePolicyEngine] Cross-tenant cache violation: User org '{user_org}' "
                f"attempted access to target org '{organization_id}'."
            )
            raise CacheSecurityError("Cross-tenant cache access is strictly forbidden.")

    @classmethod
    async def authorize_action(
        cls,
        session: AsyncSession,
        user: User,
        workspace_id: uuid.UUID,
        permission: str,
        project_id: Optional[uuid.UUID] = None,
    ) -> None:
        """
        Verifies role-based access control for cache operations.
        """
        if getattr(user, "is_superuser", False):
            return

        allowed = await PolicyEngine.check_workspace_permission(
            session=session,
            user=user,
            workspace_id=workspace_id,
            permission=permission,
        )
        if not allowed:
            raise CacheSecurityError(
                f"User '{user.id}' lacks required permission '{permission}' for workspace '{workspace_id}'."
            )
