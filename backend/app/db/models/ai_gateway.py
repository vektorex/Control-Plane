import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from backend.app.db.models.guid import GUID

if TYPE_CHECKING:
    from backend.app.db.models.workspace import Workspace


class WorkspaceModelPolicy(Base):
    """
    Workspace-level governance configuration for AI Gateway and Model Routing.
    Defines allowed providers, allowed models, defaults, token limits,
    and concurrency boundaries.
    """
    __tablename__ = "workspace_model_policies"

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
        unique=True,
        index=True,
    )
    allowed_providers: Mapped[List[str]] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: ["openai", "mock"],
    )
    allowed_models: Mapped[List[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,  # Empty list indicates all registered models under allowed providers
    )
    default_model: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    max_tokens_per_request: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        default=4096,
    )
    max_requests_per_run: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        default=50,
    )
    max_concurrent_requests: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        default=10,
    )
    fallback_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
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

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", lazy="selectin")

    __table_args__ = (
        Index("ix_ws_model_policies_ws", "workspace_id"),
    )
