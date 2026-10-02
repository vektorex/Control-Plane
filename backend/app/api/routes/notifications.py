"""
REST API endpoints for Step 25: Notifications & External Delivery Layer.
Covers In-App Notifications, Webhook Management, Notification Preferences, and Delivery Logs.
"""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.db.database import get_db
from backend.app.db.models.user import User
from backend.app.services.notifications.schemas import (
    NotificationDeliveryListResponse,
    NotificationDeliveryResponse,
    NotificationPreferenceItem,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
    NotificationResponse,
    UnreadCountResponse,
    WebhookEndpointCreate,
    WebhookEndpointResponse,
    WebhookEndpointUpdate,
    WebhookEndpointWithSecretResponse,
    WebhookTestResponse,
)
from backend.app.services.notifications.service import NotificationService

logger = logging.getLogger(__name__)


def _resolve_workspace_id(
    user: User,
    header_ws_id: Optional[str] = None,
    query_ws_id: Optional[UUID] = None,
) -> UUID:
    """Extracts and verifies active workspace ID for the request context."""
    if query_ws_id:
        return query_ws_id
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


# -----------------------------------------------------------------------------
# 1. In-App Notifications Router (/api/notifications)
# -----------------------------------------------------------------------------
notifications_router = APIRouter(prefix="/notifications", tags=["Notifications"])


@notifications_router.get("", response_model=List[NotificationResponse])
async def list_notifications(
    unread_only: bool = Query(False, description="Filter for unread notifications only"),
    severity: Optional[str] = Query(None, description="Filter by severity: info, success, warning, error, critical"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    source_type: Optional[str] = Query(None, description="Filter by source type: workflow, trigger, job, etc."),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_workspace_id: Optional[str] = Header(None),
):
    """
    List in-app notifications for the authenticated user and workspace.
    """
    ws_id = _resolve_workspace_id(current_user, header_ws_id=x_workspace_id)
    service = NotificationService(db)

    status_filter = "unread" if unread_only else None
    items, _ = await service.list_notifications(
        workspace_id=ws_id,
        user_id=current_user.id,
        status=status_filter,
        severity=severity,
        event_type=event_type,
        source_type=source_type,
        limit=limit,
        offset=offset,
    )
    return [NotificationResponse.model_validate(n) for n in items]


@notifications_router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_workspace_id: Optional[str] = Header(None),
):
    """
    Get unread notification count for the authenticated user in the current workspace.
    """
    ws_id = _resolve_workspace_id(current_user, header_ws_id=x_workspace_id)
    service = NotificationService(db)
    count = await service.get_unread_count(workspace_id=ws_id, user_id=current_user.id)
    return UnreadCountResponse(unread_count=count, workspace_id=ws_id)


@notifications_router.post("/read-all", response_model=dict)
async def mark_all_notifications_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_workspace_id: Optional[str] = Header(None),
):
    """
    Mark all unread notifications for the user as read.
    """
    ws_id = _resolve_workspace_id(current_user, header_ws_id=x_workspace_id)
    service = NotificationService(db)
    count = await service.mark_all_as_read(workspace_id=ws_id, user_id=current_user.id)
    return {"status": "success", "count": count}


@notifications_router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_workspace_id: Optional[str] = Header(None),
):
    """
    Fetch a single notification by ID.
    """
    ws_id = _resolve_workspace_id(current_user, header_ws_id=x_workspace_id)
    service = NotificationService(db)
    notif = await service.get_notification(notification_id=notification_id, workspace_id=ws_id)
    return NotificationResponse.model_validate(notif)


@notifications_router.post("/{notification_id}/read", response_model=dict)
async def mark_notification_read(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_workspace_id: Optional[str] = Header(None),
):
    """
    Mark a specific notification as read.
    """
    ws_id = _resolve_workspace_id(current_user, header_ws_id=x_workspace_id)
    service = NotificationService(db)
    notif = await service.mark_as_read(
        notification_id=notification_id,
        workspace_id=ws_id,
        user_id=current_user.id,
    )
    return {"status": "success", "id": str(notif.id), "read": True}


@notifications_router.post("/{notification_id}/archive", response_model=dict)
async def archive_notification(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_workspace_id: Optional[str] = Header(None),
):
    """
    Archive a notification.
    """
    ws_id = _resolve_workspace_id(current_user, header_ws_id=x_workspace_id)
    service = NotificationService(db)
    notif = await service.archive_notification(
        notification_id=notification_id,
        workspace_id=ws_id,
        user_id=current_user.id,
    )
    return {"status": "success", "id": str(notif.id), "status": "archived"}


# -----------------------------------------------------------------------------
# 2. Webhooks Management Router (/api/webhooks)
# -----------------------------------------------------------------------------
webhooks_router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@webhooks_router.post("", response_model=WebhookEndpointWithSecretResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook_endpoint(
    payload: WebhookEndpointCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_workspace_id: Optional[str] = Header(None),
):
    """
    Register a new outbound webhook endpoint. Returns signing secret once upon creation.
    """
    ws_id = _resolve_workspace_id(current_user, header_ws_id=x_workspace_id)
    service = NotificationService(db)
    endpoint, secret = await service.create_webhook_endpoint(
        workspace_id=ws_id,
        name=payload.name,
        url=payload.url,
        subscribed_events=payload.subscribed_events,
        active=payload.active,
    )
    res_dict = WebhookEndpointResponse.model_validate(endpoint).model_dump()
    res_dict["secret"] = secret
    return WebhookEndpointWithSecretResponse(**res_dict)


@webhooks_router.get("", response_model=List[WebhookEndpointResponse])
async def list_webhook_endpoints(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_workspace_id: Optional[str] = Header(None),
):
    """
    List configured webhook endpoints for the current workspace (secrets hidden).
    """
    ws_id = _resolve_workspace_id(current_user, header_ws_id=x_workspace_id)
    service = NotificationService(db)
    endpoints = await service.list_webhook_endpoints(workspace_id=ws_id)
    return [WebhookEndpointResponse.model_validate(ep) for ep in endpoints]


@webhooks_router.get("/{endpoint_id}", response_model=WebhookEndpointResponse)
async def get_webhook_endpoint(
    endpoint_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_workspace_id: Optional[str] = Header(None),
):
    """
    Get webhook endpoint details (secret hidden).
    """
    ws_id = _resolve_workspace_id(current_user, header_ws_id=x_workspace_id)
    service = NotificationService(db)
    ep = await service.get_webhook_endpoint(endpoint_id=endpoint_id, workspace_id=ws_id)
    return WebhookEndpointResponse.model_validate(ep)


@webhooks_router.patch("/{endpoint_id}", response_model=WebhookEndpointResponse)
async def update_webhook_endpoint(
    endpoint_id: UUID,
    payload: WebhookEndpointUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_workspace_id: Optional[str] = Header(None),
):
    """
    Update webhook configuration (URL, subscribed events, active state).
    """
    ws_id = _resolve_workspace_id(current_user, header_ws_id=x_workspace_id)
    service = NotificationService(db)
    ep = await service.update_webhook_endpoint(
        endpoint_id=endpoint_id,
        workspace_id=ws_id,
        name=payload.name,
        url=payload.url,
        active=payload.active,
        subscribed_events=payload.subscribed_events,
    )
    return WebhookEndpointResponse.model_validate(ep)


@webhooks_router.delete("/{endpoint_id}", response_model=dict)
async def delete_webhook_endpoint(
    endpoint_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_workspace_id: Optional[str] = Header(None),
):
    """
    Delete a webhook endpoint.
    """
    ws_id = _resolve_workspace_id(current_user, header_ws_id=x_workspace_id)
    service = NotificationService(db)
    await service.delete_webhook_endpoint(endpoint_id=endpoint_id, workspace_id=ws_id)
    return {"status": "success", "id": str(endpoint_id)}


@webhooks_router.post("/{endpoint_id}/test", response_model=WebhookTestResponse)
async def test_webhook_endpoint(
    endpoint_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_workspace_id: Optional[str] = Header(None),
):
    """
    Send a synthetic test payload to the webhook destination.
    """
    ws_id = _resolve_workspace_id(current_user, header_ws_id=x_workspace_id)
    service = NotificationService(db)
    result = await service.send_test_webhook(endpoint_id=endpoint_id, workspace_id=ws_id)
    return WebhookTestResponse(**result)


@webhooks_router.post("/{endpoint_id}/rotate-secret", response_model=WebhookEndpointWithSecretResponse)
async def rotate_webhook_secret(
    endpoint_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_workspace_id: Optional[str] = Header(None),
):
    """
    Rotate signing secret for the webhook endpoint. Returns new secret once.
    """
    ws_id = _resolve_workspace_id(current_user, header_ws_id=x_workspace_id)
    service = NotificationService(db)
    ep, new_secret = await service.rotate_webhook_secret(endpoint_id=endpoint_id, workspace_id=ws_id)
    res_dict = WebhookEndpointResponse.model_validate(ep).model_dump()
    res_dict["secret"] = new_secret
    return WebhookEndpointWithSecretResponse(**res_dict)


@webhooks_router.get("/{endpoint_id}/deliveries", response_model=List[NotificationDeliveryResponse])
async def list_webhook_deliveries(
    endpoint_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_workspace_id: Optional[str] = Header(None),
):
    """
    List recent delivery attempts for this webhook endpoint.
    """
    ws_id = _resolve_workspace_id(current_user, header_ws_id=x_workspace_id)
    service = NotificationService(db)
    ep = await service.get_webhook_endpoint(endpoint_id=endpoint_id, workspace_id=ws_id)
    deliveries, _ = await service.list_deliveries(
        workspace_id=ws_id,
        channel="webhook",
        limit=limit,
    )
    # Filter by destination matching endpoint URL
    matching = [d for d in deliveries if d.destination == ep.url]
    return [NotificationDeliveryResponse.model_validate(d) for d in matching]


# -----------------------------------------------------------------------------
# 3. Notification Preferences Router (/api/notification-preferences)
# -----------------------------------------------------------------------------
preferences_router = APIRouter(prefix="/notification-preferences", tags=["Notification Preferences"])


@preferences_router.get("", response_model=NotificationPreferenceResponse)
async def get_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_workspace_id: Optional[str] = Header(None),
):
    """
    Get notification channel preferences for the authenticated user and workspace.
    """
    ws_id = _resolve_workspace_id(current_user, header_ws_id=x_workspace_id)
    service = NotificationService(db)
    prefs = await service.get_preferences(workspace_id=ws_id, user_id=current_user.id)
    pref_items = [
        NotificationPreferenceItem(
            event_type=p.event_type,
            channel=p.channel,
            enabled=p.enabled,
        )
        for p in prefs
    ]
    return NotificationPreferenceResponse(
        workspace_id=ws_id,
        user_id=current_user.id,
        preferences=pref_items,
    )


@preferences_router.put("", response_model=NotificationPreferenceResponse)
async def update_preferences(
    payload: NotificationPreferenceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_workspace_id: Optional[str] = Header(None),
):
    """
    Update notification channel preferences.
    """
    ws_id = _resolve_workspace_id(current_user, header_ws_id=x_workspace_id)
    service = NotificationService(db)
    updated = await service.update_preferences(
        workspace_id=ws_id,
        preferences=[item.model_dump() for item in payload.preferences],
        user_id=current_user.id,
    )
    pref_items = [
        NotificationPreferenceItem(
            event_type=p.event_type,
            channel=p.channel,
            enabled=p.enabled,
        )
        for p in updated
    ]
    return NotificationPreferenceResponse(
        workspace_id=ws_id,
        user_id=current_user.id,
        preferences=pref_items,
    )


# -----------------------------------------------------------------------------
# 4. Notification Deliveries Router (/api/notification-deliveries)
# -----------------------------------------------------------------------------
deliveries_router = APIRouter(prefix="/notification-deliveries", tags=["Notification Deliveries"])


@deliveries_router.get("", response_model=NotificationDeliveryListResponse)
async def list_notification_deliveries(
    notification_id: Optional[UUID] = Query(None, description="Filter by notification ID"),
    channel: Optional[str] = Query(None, description="Filter by channel: in_app, webhook, email"),
    status: Optional[str] = Query(None, description="Filter by delivery status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_workspace_id: Optional[str] = Header(None),
):
    """
    List delivery audit records for the workspace.
    """
    ws_id = _resolve_workspace_id(current_user, header_ws_id=x_workspace_id)
    service = NotificationService(db)
    items, total = await service.list_deliveries(
        workspace_id=ws_id,
        notification_id=notification_id,
        channel=channel,
        status=status,
        limit=limit,
        offset=offset,
    )
    return NotificationDeliveryListResponse(
        deliveries=[NotificationDeliveryResponse.model_validate(d) for d in items],
        total=total,
    )


@deliveries_router.get("/{delivery_id}", response_model=NotificationDeliveryResponse)
async def get_notification_delivery(
    delivery_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_workspace_id: Optional[str] = Header(None),
):
    """
    Get detailed audit record for a specific delivery.
    """
    ws_id = _resolve_workspace_id(current_user, header_ws_id=x_workspace_id)
    service = NotificationService(db)
    deliv = await service.get_delivery(delivery_id=delivery_id, workspace_id=ws_id)
    return NotificationDeliveryResponse.model_validate(deliv)


# Default router export for backward compatibility
router = notifications_router
