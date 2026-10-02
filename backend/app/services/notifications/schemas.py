"""
Pydantic schemas for Step 25: Notifications & External Delivery Layer.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: uuid.UUID
    workspace_id: uuid.UUID
    project_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    event_type: str
    title: str
    body: str
    severity: str = "info"
    status: str = "unread"
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    read_at: Optional[datetime] = None

    # Convenience properties for backward compatibility
    @computed_field
    @property
    def read(self) -> bool:
        return self.status == "read"

    @computed_field
    @property
    def type(self) -> str:
        return self.event_type

    @computed_field
    @property
    def message(self) -> str:
        return self.body


class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    total: int
    unread_count: int


class UnreadCountResponse(BaseModel):
    unread_count: int
    workspace_id: uuid.UUID


class WebhookEndpointCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str = Field(min_length=1, max_length=100)
    url: str = Field(min_length=1, max_length=1000)
    subscribed_events: List[str] = Field(default_factory=lambda: ["*"])
    active: bool = True

    @field_validator("url")
    @classmethod
    def validate_url_syntax(cls, v: str) -> str:
        v = v.strip()
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("Webhook URL must start with http:// or https://")
        return v


class WebhookEndpointUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    url: Optional[str] = Field(default=None, min_length=1, max_length=1000)
    subscribed_events: Optional[List[str]] = None
    active: Optional[bool] = None

    @field_validator("url")
    @classmethod
    def validate_url_syntax(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("Webhook URL must start with http:// or https://")
        return v


class WebhookEndpointResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    url: str
    active: bool
    subscribed_events: List[str]
    created_at: datetime
    updated_at: datetime
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None


class WebhookEndpointWithSecretResponse(WebhookEndpointResponse):
    """Returned only once upon creation or secret rotation."""
    secret: str


class WebhookTestResponse(BaseModel):
    success: bool
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    latency_ms: Optional[int] = None
    endpoint_id: uuid.UUID


class NotificationPreferenceItem(BaseModel):
    event_type: str
    channel: str
    enabled: bool = True


class NotificationPreferenceUpdate(BaseModel):
    preferences: List[NotificationPreferenceItem]


class NotificationPreferenceResponse(BaseModel):
    workspace_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    preferences: List[NotificationPreferenceItem]


class NotificationDeliveryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: uuid.UUID
    notification_id: uuid.UUID
    workspace_id: uuid.UUID
    channel: str
    destination: str
    status: str
    attempt_count: int
    max_attempts: int
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    scheduled_at: datetime
    sent_at: Optional[datetime] = None
    created_at: datetime


class NotificationDeliveryListResponse(BaseModel):
    deliveries: List[NotificationDeliveryResponse]
    total: int


class NotificationFilterParams(BaseModel):
    unread_only: bool = False
    severity: Optional[str] = None
    event_type: Optional[str] = None
    source_type: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    limit: int = 50
    offset: int = 0
