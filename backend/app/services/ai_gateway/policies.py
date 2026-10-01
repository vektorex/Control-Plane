from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.db.models.ai_gateway import WorkspaceModelPolicy
from backend.app.services.ai_gateway.errors import (
    ModelNotAllowedError,
    PolicyDeniedError,
)
from backend.app.services.ai_gateway.requests import GatewayRequest


class WorkspaceModelPolicyManager:
    """
    Manages workspace-level model governance policies.
    Enforces allowed providers, allowed models, token boundaries,
    and fallback enablement on the server.
    """

    @staticmethod
    def get_default_policy(workspace_id: Optional[str] = None) -> Dict[str, Any]:
        """Default policy when no workspace-specific policy is explicitly stored."""
        return {
            "workspace_id": workspace_id,
            "allowed_providers": ["openai", "mock"],
            "allowed_models": [],  # Empty means all registered models are allowed
            "default_model": None,
            "max_tokens_per_request": 4096,
            "max_requests_per_run": 50,
            "max_concurrent_requests": 10,
            "fallback_enabled": True,
        }

    @staticmethod
    async def get_policy(
        db: Optional[AsyncSession], workspace_id: Optional[str]
    ) -> Dict[str, Any]:
        """Fetch workspace model policy from DB or return defaults."""
        if not db or not workspace_id:
            return WorkspaceModelPolicyManager.get_default_policy(workspace_id)

        try:
            ws_uuid = uuid.UUID(str(workspace_id))
            stmt = select(WorkspaceModelPolicy).where(WorkspaceModelPolicy.workspace_id == ws_uuid)
            result = await db.execute(stmt)
            policy = result.scalars().first()
            if policy:
                return {
                    "id": str(policy.id),
                    "workspace_id": str(policy.workspace_id),
                    "allowed_providers": policy.allowed_providers or ["openai", "mock"],
                    "allowed_models": policy.allowed_models or [],
                    "default_model": policy.default_model,
                    "max_tokens_per_request": policy.max_tokens_per_request,
                    "max_requests_per_run": policy.max_requests_per_run,
                    "max_concurrent_requests": policy.max_concurrent_requests,
                    "fallback_enabled": policy.fallback_enabled,
                    "created_at": policy.created_at.isoformat() if policy.created_at else None,
                    "updated_at": policy.updated_at.isoformat() if policy.updated_at else None,
                }
        except Exception as e:
            logger.warning(f"[WorkspaceModelPolicy] Error fetching policy for ws '{workspace_id}': {e}")

        return WorkspaceModelPolicyManager.get_default_policy(workspace_id)

    @staticmethod
    def validate_request_policy(
        request: GatewayRequest,
        policy: Dict[str, Any],
        resolved_provider: Optional[str] = None,
    ) -> None:
        """
        Validate incoming GatewayRequest against the workspace model policy.
        Must be enforced strictly server-side before calling any provider.
        """
        provider = (resolved_provider or request.provider or "").lower()
        model = request.model

        # 1. Validate Provider
        allowed_providers = [p.lower() for p in policy.get("allowed_providers", [])]
        if provider and allowed_providers and provider not in allowed_providers:
            raise PolicyDeniedError(
                f"Provider '{provider}' is not permitted by workspace model policy. "
                f"Allowed providers: {', '.join(allowed_providers)}."
            )

        # 2. Validate Model
        allowed_models = policy.get("allowed_models", [])
        if allowed_models:
            # If explicit list is configured, model must be in allowed_models
            if model not in allowed_models and f"{provider}/{model}" not in allowed_models:
                raise ModelNotAllowedError(
                    f"Model '{model}' is not permitted by workspace model policy. "
                    f"Allowed models: {', '.join(allowed_models)}."
                )

        # 3. Validate Token Limit
        max_tokens_limit = policy.get("max_tokens_per_request")
        if max_tokens_limit and request.max_tokens and request.max_tokens > max_tokens_limit:
            raise PolicyDeniedError(
                f"Requested max_tokens ({request.max_tokens}) exceeds workspace policy limit ({max_tokens_limit})."
            )
