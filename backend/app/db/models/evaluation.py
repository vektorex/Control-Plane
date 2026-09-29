import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from backend.app.db.models.guid import GUID

if TYPE_CHECKING:
    from backend.app.db.models.run import Run


class EvaluationRun(Base):
    """
    EvaluationRun entity capturing evaluation attempts, engine outcomes,
    status recommendations, and duration for a Task Run output.
    """
    __tablename__ = "evaluation_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="passed",
        index=True,
    )
    evaluator_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="engine",
    )
    recommendation: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="accept",
    )
    mode: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="standard",
    )
    attempt: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    duration_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        default=0,
    )
    raw_summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    metadata_snapshot: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    run: Mapped["Run"] = relationship(
        "Run",
        back_populates="evaluation_runs",
    )
    findings: Mapped[List["EvaluationFinding"]] = relationship(
        "EvaluationFinding",
        back_populates="evaluation_run",
        cascade="all, delete-orphan",
        order_by="EvaluationFinding.created_at",
    )

    def __repr__(self) -> str:
        return f"<EvaluationRun(id={self.id}, run_id={self.run_id}, status='{self.status}', recommendation='{self.recommendation}')>"


class EvaluationFinding(Base):
    """
    EvaluationFinding entity storing structured individual verification checks
    (grounding, completeness, citation, format, safety) with confidence and evidence references.
    """
    __tablename__ = "evaluation_findings"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    evaluation_run_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("evaluation_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    check_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="passed",
    )
    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    evidence_ids: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True,
    )
    metadata_snapshot: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    evaluation_run: Mapped["EvaluationRun"] = relationship(
        "EvaluationRun",
        back_populates="findings",
    )

    def __repr__(self) -> str:
        return f"<EvaluationFinding(id={self.id}, check_type='{self.check_type}', status='{self.status}', confidence={self.confidence})>"
