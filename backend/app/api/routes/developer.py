"""
Developer Platform Management API Routes.
Step 37: Public API, Developer Platform & SDK Layer.
Manages developer applications, API credentials, scopes, quotas, webhooks, and approvals.
"""
from typing import Any, Dict, List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.auth import get_current_user
from backend.app.db.database import get_db
from backend.app.db.models.user import User
from backend.app.services.access_control.authorization import AuthorizationService
from backend.app.services.access_control.permissions import (
    DEVELOPER_ADMIN,
    DEVELOPER_CREDENTIAL_CREATE,
    DEVELOPER_CREDENTIAL_REVOKE,
    DEVELOPER_MANAGE,
    DEVELOPER_READ,
)
from backend.app.services.developer_platform.schemas import (
    APICredentialCreate,
    APICredentialCreatedResponse,
    APICredentialListResponse,
    APICredentialResponse,
    APICredentialRotateRequest,
    APIQuotaCreate,
    APIQuotaResponse,
    APIUsageAggregateResponse,
    ApplicationApprovalResponse,
    ApplicationApprovalReview,
    DeveloperApplicationCreate,
    DeveloperApplicationListResponse,
    DeveloperApplicationResponse,
    DeveloperApplicationUpdate,
    DeveloperOverviewResponse,
    WebhookSubscriptionCreate,
    WebhookSubscriptionCreatedResponse,
    WebhookSubscriptionListResponse,
    WebhookSubscriptionResponse,
    WebhookSubscriptionUpdate,
)
from backend.app.services.developer_platform.service import DeveloperPlatformService

developer_router = APIRouter(prefix="/developer", tags=["developer-platform"])


async def _resolve_org_id(user: User, db: AsyncSession, organization_id: Optional[str] = None) -> str:
    if organization_id:
        return organization_id
    auth_svc = AuthorizationService(db)
    ctx = await auth_svc.resolve_context(user)
    if ctx.organization_id:
        return str(ctx.organization_id)
    return str(user.id)


# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------

@developer_router.get("/overview", response_model=DeveloperOverviewResponse)
async def get_developer_overview(
    organization_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns aggregated platform metrics for the developer dashboard."""
    org_id = await _resolve_org_id(user, db, organization_id)
    dev_svc = DeveloperPlatformService(db)
    data = await dev_svc.repository.get_overview(org_id)
    return DeveloperOverviewResponse(**data)


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------

@developer_router.get("/applications", response_model=DeveloperApplicationListResponse)
async def list_applications(
    organization_id: Optional[str] = Query(None),
    environment: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists developer applications for an organization."""
    org_id = await _resolve_org_id(user, db, organization_id)
    dev_svc = DeveloperPlatformService(db)
    apps = await dev_svc.applications.list_applications(
        organization_id=org_id,
        environment=environment,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    return DeveloperApplicationListResponse(
        applications=[DeveloperApplicationResponse.model_validate(a) for a in apps],
        total=len(apps),
    )


@developer_router.post("/applications", response_model=DeveloperApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    data: DeveloperApplicationCreate,
    organization_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Creates a new developer application."""
    org_id = await _resolve_org_id(user, db, organization_id)
    dev_svc = DeveloperPlatformService(db)
    app = await dev_svc.applications.create_application(
        organization_id=org_id,
        user_id=str(user.id),
        data=data,
    )
    return DeveloperApplicationResponse.model_validate(app)


@developer_router.get("/applications/{application_id}", response_model=DeveloperApplicationResponse)
async def get_application(
    application_id: str,
    organization_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves an application by ID."""
    org_id = await _resolve_org_id(user, db, organization_id)
    dev_svc = DeveloperPlatformService(db)
    app = await dev_svc.applications.get_application(application_id, org_id)
    return DeveloperApplicationResponse.model_validate(app)


@developer_router.patch("/applications/{application_id}", response_model=DeveloperApplicationResponse)
async def update_application(
    application_id: str,
    data: DeveloperApplicationUpdate,
    organization_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Updates an application name, description, or status."""
    org_id = await _resolve_org_id(user, db, organization_id)
    dev_svc = DeveloperPlatformService(db)
    app = await dev_svc.applications.update_application(application_id, org_id, data)
    return DeveloperApplicationResponse.model_validate(app)


@developer_router.delete("/applications/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(
    application_id: str,
    organization_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Deletes an application and cascades its credentials."""
    org_id = await _resolve_org_id(user, db, organization_id)
    dev_svc = DeveloperPlatformService(db)
    await dev_svc.applications.delete_application(application_id, org_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Credentials
# ---------------------------------------------------------------------------

@developer_router.post("/applications/{application_id}/credentials", response_model=APICredentialCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_credential(
    application_id: str,
    data: APICredentialCreate,
    organization_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generates a new scoped API key for an application.
    Returns the plaintext secret_key ONLY ONCE.
    """
    org_id = await _resolve_org_id(user, db, organization_id)
    auth_svc = AuthorizationService(db)
    ctx = await auth_svc.resolve_context(user, organization_id=uuid.UUID(org_id))
    is_admin = ctx.organization_role in ("owner", "admin")

    dev_svc = DeveloperPlatformService(db)
    cred, secret_key = await dev_svc.credentials.create_credential(
        application_id=application_id,
        organization_id=org_id,
        user_id=str(user.id),
        data=data,
        creator_permissions=ctx.permissions,
        is_org_admin=is_admin,
    )

    scopes = [s.scope for s in cred.scopes] if hasattr(cred, "scopes") and cred.scopes else data.scopes
    return APICredentialCreatedResponse(
        id=cred.id,
        application_id=cred.application_id,
        name=cred.name,
        key_prefix=cred.key_prefix,
        credential_type=cred.credential_type,
        environment=cred.environment,
        status=cred.status,
        created_at=cred.created_at,
        expires_at=cred.expires_at,
        last_used_at=cred.last_used_at,
        revoked_at=cred.revoked_at,
        created_by=cred.created_by,
        scopes=scopes,
        secret_key=secret_key,
    )


@developer_router.get("/applications/{application_id}/credentials", response_model=APICredentialListResponse)
async def list_credentials(
    application_id: str,
    organization_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists credentials for an application (without plaintext secrets)."""
    org_id = await _resolve_org_id(user, db, organization_id)
    dev_svc = DeveloperPlatformService(db)
    creds = await dev_svc.credentials.list_credentials(application_id, org_id)

    res = []
    for c in creds:
        scopes = [s.scope for s in c.scopes] if c.scopes else []
        res.append(
            APICredentialResponse(
                id=c.id,
                application_id=c.application_id,
                name=c.name,
                key_prefix=c.key_prefix,
                credential_type=c.credential_type,
                environment=c.environment,
                status=c.status,
                created_at=c.created_at,
                expires_at=c.expires_at,
                last_used_at=c.last_used_at,
                revoked_at=c.revoked_at,
                created_by=c.created_by,
                scopes=scopes,
            )
        )
    return APICredentialListResponse(credentials=res, total=len(res))


@developer_router.post("/credentials/{credential_id}/rotate", response_model=APICredentialCreatedResponse)
async def rotate_credential(
    credential_id: str,
    data: APICredentialRotateRequest,
    organization_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Rotates a credential. Returns the new plaintext key ONCE."""
    org_id = await _resolve_org_id(user, db, organization_id)
    dev_svc = DeveloperPlatformService(db)
    new_cred, secret_key = await dev_svc.credentials.rotate_credential(
        credential_id=credential_id,
        organization_id=org_id,
        user_id=str(user.id),
        data=data,
    )
    scopes = [s.scope for s in new_cred.scopes] if new_cred.scopes else []
    return APICredentialCreatedResponse(
        id=new_cred.id,
        application_id=new_cred.application_id,
        name=new_cred.name,
        key_prefix=new_cred.key_prefix,
        credential_type=new_cred.credential_type,
        environment=new_cred.environment,
        status=new_cred.status,
        created_at=new_cred.created_at,
        expires_at=new_cred.expires_at,
        last_used_at=new_cred.last_used_at,
        revoked_at=new_cred.revoked_at,
        created_by=new_cred.created_by,
        scopes=scopes,
        secret_key=secret_key,
    )


@developer_router.post("/credentials/{credential_id}/revoke", response_model=APICredentialResponse)
async def revoke_credential(
    credential_id: str,
    organization_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revokes an API credential immediately."""
    org_id = await _resolve_org_id(user, db, organization_id)
    dev_svc = DeveloperPlatformService(db)
    cred = await dev_svc.credentials.revoke_credential(credential_id, org_id, str(user.id))
    scopes = [s.scope for s in cred.scopes] if cred.scopes else []
    return APICredentialResponse(
        id=cred.id,
        application_id=cred.application_id,
        name=cred.name,
        key_prefix=cred.key_prefix,
        credential_type=cred.credential_type,
        environment=cred.environment,
        status=cred.status,
        created_at=cred.created_at,
        expires_at=cred.expires_at,
        last_used_at=cred.last_used_at,
        revoked_at=cred.revoked_at,
        created_by=cred.created_by,
        scopes=scopes,
    )


# ---------------------------------------------------------------------------
# Webhooks (Management)
# ---------------------------------------------------------------------------

@developer_router.get("/applications/{application_id}/webhooks", response_model=WebhookSubscriptionListResponse)
async def list_webhooks(
    application_id: str,
    organization_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists webhooks for an application."""
    org_id = await _resolve_org_id(user, db, organization_id)
    dev_svc = DeveloperPlatformService(db)
    subs = await dev_svc.webhooks.list_subscriptions(application_id, org_id)
    return WebhookSubscriptionListResponse(
        webhooks=[WebhookSubscriptionResponse.model_validate(s) for s in subs],
        total=len(subs),
    )


@developer_router.post("/applications/{application_id}/webhooks", response_model=WebhookSubscriptionCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    application_id: str,
    data: WebhookSubscriptionCreate,
    organization_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Creates a new webhook subscription. Returns signing secret ONCE."""
    org_id = await _resolve_org_id(user, db, organization_id)
    dev_svc = DeveloperPlatformService(db)
    sub, secret = await dev_svc.webhooks.create_subscription(
        application_id=application_id,
        organization_id=org_id,
        data=data,
        allow_local_for_testing=True,
    )
    return WebhookSubscriptionCreatedResponse(
        id=sub.id,
        application_id=sub.application_id,
        organization_id=sub.organization_id,
        url=sub.url,
        status=sub.status,
        events=sub.events,
        created_at=sub.created_at,
        updated_at=sub.updated_at,
        failure_count=sub.failure_count,
        webhook_secret=secret,
    )


@developer_router.patch("/webhooks/{webhook_id}", response_model=WebhookSubscriptionResponse)
async def update_webhook(
    webhook_id: str,
    data: WebhookSubscriptionUpdate,
    organization_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Updates a webhook URL, events, or status."""
    org_id = await _resolve_org_id(user, db, organization_id)
    dev_svc = DeveloperPlatformService(db)
    sub = await dev_svc.webhooks.update_subscription(webhook_id, org_id, data, allow_local_for_testing=True)
    return WebhookSubscriptionResponse.model_validate(sub)


@developer_router.delete("/webhooks/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: str,
    organization_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Deletes a webhook subscription."""
    org_id = await _resolve_org_id(user, db, organization_id)
    dev_svc = DeveloperPlatformService(db)
    await dev_svc.webhooks.delete_subscription(webhook_id, org_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Usage Telemetry (Management)
# ---------------------------------------------------------------------------

@developer_router.get("/applications/{application_id}/usage", response_model=APIUsageAggregateResponse)
async def get_application_usage(
    application_id: str,
    period_hours: int = Query(24, ge=1, le=720),
    organization_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves usage telemetry for an application."""
    org_id = await _resolve_org_id(user, db, organization_id)
    dev_svc = DeveloperPlatformService(db)
    return await dev_svc.usage.get_usage_summary(
        organization_id=org_id,
        application_id=application_id,
        period_hours=period_hours,
    )


# ---------------------------------------------------------------------------
# Quotas (Management)
# ---------------------------------------------------------------------------

@developer_router.get("/quotas", response_model=List[APIQuotaResponse])
async def list_quotas(
    application_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists quotas configured for an application."""
    dev_svc = DeveloperPlatformService(db)
    quotas = await dev_svc.repository.list_quotas(application_id)
    return [APIQuotaResponse.model_validate(q) for q in quotas]


@developer_router.post("/quotas", response_model=APIQuotaResponse, status_code=status.HTTP_201_CREATED)
async def create_quota(
    application_id: str,
    data: APIQuotaCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Sets a volumetric quota on an application."""
    dev_svc = DeveloperPlatformService(db)
    quota = await dev_svc.repository.create_quota(
        application_id=application_id,
        resource_type=data.resource_type,
        limit=data.limit,
        period=data.period,
    )
    return APIQuotaResponse.model_validate(quota)


# ---------------------------------------------------------------------------
# Approvals (Management)
# ---------------------------------------------------------------------------

@developer_router.get("/approvals", response_model=List[ApplicationApprovalResponse])
async def list_approvals(
    status_filter: Optional[str] = Query(None, alias="status"),
    organization_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists production application approval requests."""
    org_id = await _resolve_org_id(user, db, organization_id)
    dev_svc = DeveloperPlatformService(db)
    approvals = await dev_svc.repository.list_approvals(org_id, status=status_filter)
    return [ApplicationApprovalResponse.model_validate(a) for a in approvals]


@developer_router.post("/approvals/{approval_id}/review", response_model=ApplicationApprovalResponse)
async def review_approval(
    approval_id: str,
    data: ApplicationApprovalReview,
    organization_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reviews (approves/rejects) a production application request."""
    org_id = await _resolve_org_id(user, db, organization_id)
    dev_svc = DeveloperPlatformService(db)
    approval = await dev_svc.repository.review_approval(
        approval_id=approval_id,
        organization_id=org_id,
        reviewer_id=str(user.id),
        decision=data.decision,
        notes=data.notes,
    )
    return ApplicationApprovalResponse.model_validate(approval)


# ---------------------------------------------------------------------------
# OpenAPI Public Spec Generator
# ---------------------------------------------------------------------------

@developer_router.get("/openapi.json")
async def get_public_openapi_spec():
    """Generates an OpenAPI 3.0 specification representing ONLY the Public API contracts."""
    from backend.app.api.routes.public_v1 import public_v1_router
    from fastapi.openapi.utils import get_openapi
    from fastapi import FastAPI

    temp_app = FastAPI(
        title="AI Work Layer Public API",
        version="1.0.0",
        description="Public developer API for programmatic task and workflow execution, multimodal artifacts, and webhooks.",
    )
    temp_app.include_router(public_v1_router, prefix="/api/v1")
    schema = get_openapi(
        title=temp_app.title,
        version=temp_app.version,
        openapi_version="3.0.2",
        description=temp_app.description,
        routes=temp_app.routes,
    )
    return schema
