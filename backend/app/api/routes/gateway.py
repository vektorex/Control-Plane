"""
REST API endpoints for the AI Gateway (Step 19).
Provides centralized endpoints for models, providers, operational health,
routing preview, execution test, and workspace model policies.
"""
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.db.database import get_db
from backend.app.db.models.ai_gateway import WorkspaceModelPolicy
from backend.app.db.models.user import User
from backend.app.services.ai_gateway import (
    AIGateway,
    GatewayError,
    GatewayRequest,
    GatewayResponse,
    default_ai_gateway,
    default_health_service,
    default_provider_registry,
    WorkspaceModelPolicyManager,
)
from backend.app.services.models.registry import default_model_registry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gateway", tags=["AI Gateway"])


def _resolve_workspace_id(
    user: User,
    header_ws_id: Optional[str] = None,
) -> UUID:
    """Extracts and verifies active workspace ID for the request."""
    if header_ws_id:
        try:
            return UUID(header_ws_id)
        except ValueError:
            pass
    if getattr(user, "default_workspace_id", None):
        return user.default_workspace_id
    if getattr(user, "workspaces", None) and len(user.workspaces) > 0:
        return user.workspaces[0].id
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Workspace context could not be resolved. Please specify 'X-Workspace-Id' header.",
    )


class GatewayPreviewRequest(BaseModel):
    model: str = Field(default="auto", description="Target model identifier or 'auto'")
    provider: Optional[str] = Field(default=None, description="Optional provider preference")
    messages: Optional[List[Dict[str, Any]]] = Field(default=None, description="Messages or dummy prompt")
    stream: bool = Field(default=False)
    tools: Optional[List[Dict[str, Any]]] = Field(default=None)
    response_format: Optional[Dict[str, Any]] = Field(default=None)
    latency_preference: str = Field(default="balanced")
    cost_preference: str = Field(default="balanced")


class GatewayTestRequest(BaseModel):
    model: str = Field(default="gpt-4o-mini", description="Target model")
    provider: Optional[str] = Field(default=None, description="Target provider")
    prompt: str = Field(default="Hello, respond with a short confirmation message.", description="Test prompt")
    temperature: float = Field(default=0.7)
    max_tokens: Optional[int] = Field(default=100)


class WorkspaceModelPolicyUpdate(BaseModel):
    allowed_providers: Optional[List[str]] = None
    allowed_models: Optional[List[str]] = None
    default_model: Optional[str] = None
    max_tokens_per_request: Optional[int] = None
    max_requests_per_run: Optional[int] = None
    max_concurrent_requests: Optional[int] = None
    fallback_enabled: Optional[bool] = None


# =============================================================================
# 1. Models & Providers Endpoints
# =============================================================================

@router.get("/models")
async def list_models(
    provider: Optional[str] = Query(None, description="Filter by provider"),
    enabled_only: bool = Query(False, description="Filter only enabled models"),
    current_user: User = Depends(get_current_user),
):
    """List models supported by the AI Gateway runtime with operational metadata."""
    models = default_model_registry.list_models(provider=provider, enabled_only=enabled_only)
    return [
        {
            "model_id": m.model_id,
            "provider": m.provider,
            "display_name": m.display_name,
            "capabilities": m.capabilities,
            "context_window": m.context_window,
            "max_output_tokens": m.max_output_tokens,
            "cost_class": m.cost_class,
            "latency_class": m.latency_class,
            "supports_streaming": m.supports_streaming,
            "supports_tools": m.supports_tools,
            "supports_structured_output": m.supports_structured_output,
            "supports_vision": m.supports_vision,
            "enabled": m.enabled,
            "is_default": m.is_default,
            "description": m.description,
        }
        for m in models
    ]


@router.get("/providers")
async def list_providers(
    current_user: User = Depends(get_current_user),
):
    """List registered provider adapters with safe capabilities and health status."""
    return default_provider_registry.list()


@router.get("/health")
async def get_gateway_health(
    current_user: User = Depends(get_current_user),
):
    """Return operational health metrics and circuit breaker statuses."""
    providers = default_provider_registry.list()
    health_reports = []

    for prov in providers:
        p_name = prov["name"]
        prov_health = default_health_service.get_health_status(provider=p_name)
        models_health = []
        for m in prov.get("models", []):
            m_id = m["model_id"]
            m_health = default_health_service.get_health_status(provider=p_name, model=m_id)
            models_health.append(m_health)

        health_reports.append({
            "provider": p_name,
            "display_name": prov["display_name"],
            "configured": prov["enabled"],
            "health": prov_health,
            "models": models_health,
        })

    return {
        "status": "healthy",
        "providers": health_reports,
    }


# =============================================================================
# 2. Preview and Test Endpoints
# =============================================================================

@router.post("/preview")
async def preview_routing(
    payload: GatewayPreviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_workspace_id: Optional[str] = Header(None),
):
    """
    Generate routing preview showing selected model, provider, and fallback sequence
    WITHOUT executing any model request.
    """
    ws_id = _resolve_workspace_id(current_user, header_ws_id=x_workspace_id)
    req = GatewayRequest(
        model=payload.model,
        provider=payload.provider,
        messages=payload.messages or [{"role": "user", "content": "preview query"}],
        stream=payload.stream,
        tools=payload.tools,
        response_format=payload.response_format,
        metadata={
            "latency_preference": payload.latency_preference,
            "cost_preference": payload.cost_preference,
        },
        workspace_id=str(ws_id),
    )
    return await default_ai_gateway.preview(req, db=db)


@router.post("/test", response_model=GatewayResponse)
async def test_gateway(
    payload: GatewayTestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_workspace_id: Optional[str] = Header(None),
):
    """
    Execute a diagnostic test prompt through the real AI Gateway runtime.
    Enforces workspace policies, request limits, and records telemetry.
    """
    ws_id = _resolve_workspace_id(current_user, header_ws_id=x_workspace_id)
    req = GatewayRequest(
        model=payload.model,
        provider=payload.provider,
        messages=[{"role": "user", "content": payload.prompt}],
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
        workspace_id=str(ws_id),
        metadata={"source": "api_test", "user_id": str(current_user.id)},
    )
    try:
        response = await default_ai_gateway.test(req, db=db)
        return response
    except GatewayError as ge:
        raise HTTPException(status_code=ge.status_code, detail=ge.to_safe_dict())
    except Exception as exc:
        logger.error(f"[Gateway API] Test failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": True, "code": "GATEWAY_ERROR", "message": str(exc)},
        )


# =============================================================================
# 3. Workspace Model Policy Endpoints
# =============================================================================

@router.get("/policies")
async def get_workspace_policy(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_workspace_id: Optional[str] = Header(None),
):
    """Get the model routing policy configured for the active workspace."""
    ws_id = _resolve_workspace_id(current_user, header_ws_id=x_workspace_id)
    return await WorkspaceModelPolicyManager.get_policy(db, str(ws_id))


@router.patch("/policies")
async def update_workspace_policy(
    payload: WorkspaceModelPolicyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_workspace_id: Optional[str] = Header(None),
):
    """Update workspace model policy (allowed providers, models, limits, fallback)."""
    ws_id = _resolve_workspace_id(current_user, header_ws_id=x_workspace_id)

    stmt = select(WorkspaceModelPolicy).where(WorkspaceModelPolicy.workspace_id == ws_id)
    result = await db.execute(stmt)
    policy = result.scalars().first()

    if not policy:
        policy = WorkspaceModelPolicy(
            workspace_id=ws_id,
            allowed_providers=payload.allowed_providers or ["openai", "mock"],
            allowed_models=payload.allowed_models or [],
            default_model=payload.default_model,
            max_tokens_per_request=payload.max_tokens_per_request or 4096,
            max_requests_per_run=payload.max_requests_per_run or 50,
            max_concurrent_requests=payload.max_concurrent_requests or 10,
            fallback_enabled=True if payload.fallback_enabled is None else payload.fallback_enabled,
        )
        db.add(policy)
    else:
        if payload.allowed_providers is not None:
            policy.allowed_providers = payload.allowed_providers
        if payload.allowed_models is not None:
            policy.allowed_models = payload.allowed_models
        if payload.default_model is not None:
            policy.default_model = payload.default_model
        if payload.max_tokens_per_request is not None:
            policy.max_tokens_per_request = payload.max_tokens_per_request
        if payload.max_requests_per_run is not None:
            policy.max_requests_per_run = payload.max_requests_per_run
        if payload.max_concurrent_requests is not None:
            policy.max_concurrent_requests = payload.max_concurrent_requests
        if payload.fallback_enabled is not None:
            policy.fallback_enabled = payload.fallback_enabled

    await db.commit()
    await db.refresh(policy)

    return {
        "id": str(policy.id),
        "workspace_id": str(policy.workspace_id),
        "allowed_providers": policy.allowed_providers,
        "allowed_models": policy.allowed_models,
        "default_model": policy.default_model,
        "max_tokens_per_request": policy.max_tokens_per_request,
        "max_requests_per_run": policy.max_requests_per_run,
        "max_concurrent_requests": policy.max_concurrent_requests,
        "fallback_enabled": policy.fallback_enabled,
        "updated_at": policy.updated_at.isoformat() if policy.updated_at else None,
    }
