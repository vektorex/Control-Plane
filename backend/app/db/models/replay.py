import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from backend.app.db.models.guid import GUID

if TYPE_CHECKING:
    from backend.app.db.models.run import Run
    from backend.app.db.models.user import User
    from backend.app.db.models.workspace import Workspace
    from backend.app.db.models.workflow import WorkflowRun


class ReplayRun(Base):
    """
    Execution record of an AI Replay simulation or re-execution.
    Maintains an immutable snapshot of the original execution configuration,
    tracks dry-run simulation vs live execution, records blocked side-effects,
    and supports factual diff comparison without mutating original run state.
    """
    __tablename__ = "replay_runs"

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
    original_run_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    original_workflow_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("workflow_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    replay_mode: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="dry_run",
        index=True,
    )  # inspect | dry_run | replay | compare
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="queued",
        index=True,
    )  # queued | running | completed | failed | cancelled
    snapshot_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="1.0",
    )
    dry_run: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    snapshot: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    replay_output: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    execution_steps: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSON,
        nullable=True,
    )
    comparison_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        nullable=True,
    )
    error_code: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    replay_metadata: Mapped[Dict[str, Any]] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", lazy="selectin")
    original_run: Mapped["Run"] = relationship("Run", lazy="selectin")
    original_workflow_run: Mapped[Optional["WorkflowRun"]] = relationship("WorkflowRun", lazy="selectin")
    creator: Mapped[Optional["User"]] = relationship("User", lazy="selectin")

    __table_args__ = (
        Index("ix_replay_runs_ws_status", "workspace_id", "status"),
        Index("ix_replay_runs_ws_orig", "workspace_id", "original_run_id"),
        Index("ix_replay_runs_created_at_desc", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ReplayRun(id={self.id}, original_run_id={self.original_run_id}, mode='{self.replay_mode}', status='{self.status}')>"
