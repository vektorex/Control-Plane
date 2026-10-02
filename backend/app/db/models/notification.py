"""
SQLAlchemy models for Step 25: Notifications & External Delivery Layer.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, func, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from backend.app.db.models.guid import GUID

if TYPE_CHECKING:
    from backend.app.db.models.workspace import Workspace
    from backend.app.db.models.project import Project
    from backend.app.db.models.user import User


class Notification(Base):
    """
    Unified notification entity representing completed AI work, workflow events,
    approvals, failures, evaluation reports, and safe system events.
    """
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    # Severity: info, success, warning, error, critical
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="info", index=True)

    # Status: unread, read, archived
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="unread", index=True)

    source_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    source_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", lazy="selectin")
    project: Mapped[Optional["Project"]] = relationship("Project", lazy="selectin")
    user: Mapped[Optional["User"]] = relationship("User", lazy="selectin")
    deliveries: Mapped[List["NotificationDelivery"]] = relationship(
        "NotificationDelivery",
        back_populates="notification",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="NotificationDelivery.created_at.asc()",
    )

    __table_args__ = (
        Index("ix_notifications_ws_user_status", "workspace_id", "user_id", "status"),
        Index("ix_notifications_ws_created", "workspace_id", "created_at"),
        Index("ix_notifications_ws_event_type", "workspace_id", "event_type"),
    )

    def __init__(self, **kwargs):
        # Support backwards-compatible argument names from legacy HITL notifications
        if "type" in kwargs and "event_type" not in kwargs:
            kwargs["event_type"] = kwargs.pop("type")
        if "message" in kwargs and "body" not in kwargs:
            kwargs["body"] = kwargs.pop("message")
        if "reference_type" in kwargs and "source_type" not in kwargs:
            kwargs["source_type"] = kwargs.pop("reference_type")
        if "reference_id" in kwargs and "source_id" not in kwargs:
            kwargs["source_id"] = str(kwargs.pop("reference_id")) if kwargs.get("reference_id") is not None else None
        if "read" in kwargs and "status" not in kwargs:
            kwargs["status"] = "read" if kwargs.pop("read") else "unread"
        super().__init__(**kwargs)
        if getattr(self, "status", None) is None:
            self.status = "unread"
        if getattr(self, "severity", None) is None:
            self.severity = "info"
        if getattr(self, "metadata_json", None) is None:
            self.metadata_json = {}
        now = datetime.now(timezone.utc)
        if getattr(self, "created_at", None) is None:
            self.created_at = now
        if getattr(self, "updated_at", None) is None:
            self.updated_at = now

    # Backwards-compatible properties
    @property
    def type(self) -> str:
        return self.event_type

    @type.setter
    def type(self, val: str) -> None:
        self.event_type = val

    @property
    def message(self) -> str:
        return self.body

    @message.setter
    def message(self, val: str) -> None:
        self.body = val

    @property
    def read(self) -> bool:
        return self.status == "read"

    @read.setter
    def read(self, val: bool) -> None:
        self.status = "read" if val else "unread"
        if val and not self.read_at:
            self.read_at = datetime.now(timezone.utc)

    @property
    def reference_type(self) -> Optional[str]:
        return self.source_type

    @reference_type.setter
    def reference_type(self, val: Optional[str]) -> None:
        self.source_type = val

    @property
    def reference_id(self) -> Optional[str]:
        return self.source_id

    @reference_id.setter
    def reference_id(self, val: Optional[str]) -> None:
        self.source_id = str(val) if val is not None else None


class NotificationDelivery(Base):
    """
    Tracks external delivery of a notification across specific channels
    (in_app, webhook, email) with retry history and status tracking.
    """
    __tablename__ = "notification_deliveries"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    notification_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("notifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # in_app, webhook, email
    channel: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Webhook URL, email address, or in_app recipient user_id
    destination: Mapped[str] = mapped_column(String(500), nullable=False)

    # queued, sending, sent, retrying, failed, cancelled
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="queued", index=True)

    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)

    provider_message_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    notification: Mapped["Notification"] = relationship("Notification", back_populates="deliveries")

    __table_args__ = (
        Index("ix_delivery_status_sched", "status", "scheduled_at"),
        Index("ix_delivery_idempotency", "notification_id", "channel", "destination"),
        Index("ix_delivery_workspace_channel", "workspace_id", "channel", "status"),
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if getattr(self, "status", None) is None:
            self.status = "queued"
        if getattr(self, "attempt_count", None) is None:
            self.attempt_count = 0
        if getattr(self, "max_attempts", None) is None:
            self.max_attempts = 3
        now = datetime.now(timezone.utc)
        if getattr(self, "scheduled_at", None) is None:
            self.scheduled_at = now
        if getattr(self, "created_at", None) is None:
            self.created_at = now
        if getattr(self, "updated_at", None) is None:
            self.updated_at = now


class WebhookEndpoint(Base):
    """
    Configured outbound webhook destination with HMAC signing secret and event subscription.
    """
    __tablename__ = "webhook_endpoints"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)

    # Secret used for HMAC-SHA256 signature (stored securely, never exposed in full API responses)
    secret_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    # List of subscribed event types (or ["*"] for all events)
    subscribed_events: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=lambda: ["*"])

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    last_success_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_failure_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_webhook_workspace_active", "workspace_id", "active"),
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if getattr(self, "active", None) is None:
            self.active = True
        if getattr(self, "subscribed_events", None) is None:
            self.subscribed_events = ["*"]
        now = datetime.now(timezone.utc)
        if getattr(self, "created_at", None) is None:
            self.created_at = now
        if getattr(self, "updated_at", None) is None:
            self.updated_at = now


class NotificationPreference(Base):
    """
    Workspace and user preferences configuring enabled channels per event type.
    """
    __tablename__ = "notification_preferences"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Specific event_type (e.g. 'workflow.completed') or '*' for global preference
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # in_app, webhook, email
    channel: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "user_id",
            "event_type",
            "channel",
            name="uq_notification_preference",
        ),
        Index("ix_notif_pref_lookup", "workspace_id", "user_id", "event_type"),
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if getattr(self, "enabled", None) is None:
            self.enabled = True
        now = datetime.now(timezone.utc)
        if getattr(self, "created_at", None) is None:
            self.created_at = now
        if getattr(self, "updated_at", None) is None:
            self.updated_at = now
