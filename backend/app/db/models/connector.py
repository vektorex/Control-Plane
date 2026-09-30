import uuid
from datetime import datetime
from typing import Any, Dict, Optional, TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from backend.app.db.models.guid import GUID

if TYPE_CHECKING:
    from backend.app.db.models.workspace import Workspace
    from backend.app.db.models.user import User


class Credential(Base):
    """
    Encrypted credential storage record for external connectors.
    Never stores plaintext secrets. Scoped to a workspace and optionally a user.
    """
    __tablename__ = "credentials"

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
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    connector_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    credential_type: Mapped[str] = mapped_column(String(50), nullable=False, default="pat")
    encrypted_secret: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint("workspace_id", "connector_name", name="uq_credentials_workspace_connector"),
        Index("ix_credentials_ws_conn", "workspace_id", "connector_name"),
    )

    def __repr__(self) -> str:
        return f"<Credential(id={self.id}, workspace_id={self.workspace_id}, connector_name='{self.connector_name}', type='{self.credential_type}')>"


class ConnectorPermission(Base):
    """
    Workspace-scoped operation-level permissions for connectors.
    """
    __tablename__ = "connector_permissions"

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
    connector_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    operation: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    permission_level: Mapped[str] = mapped_column(String(50), nullable=False, default="read")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("workspace_id", "connector_name", "operation", name="uq_connector_permissions_ws_conn_op"),
        Index("ix_connector_permissions_ws_conn", "workspace_id", "connector_name"),
    )

    def __repr__(self) -> str:
        return f"<ConnectorPermission(id={self.id}, workspace_id={self.workspace_id}, connector='{self.connector_name}', op='{self.operation}', level='{self.permission_level}', enabled={self.enabled})>"
