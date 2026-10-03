"""
SQLAlchemy models for Step 30: Multimodal AI and Unified Artifact Intelligence.
Defines persistent multi-tenant Artifacts, ArtifactParts, and ArtifactEvidence records.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from backend.app.db.guid import GUID


class Artifact(Base):
    """
    Core multimodal artifact entity representing an uploaded or generated media asset.
    Inherits organization, workspace, and project multi-tenant authorization boundaries.
    Binary data is never stored in PostgreSQL; it references the storage abstraction.
    """
    __tablename__ = "artifacts"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
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
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    artifact_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    mime_type: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    size_bytes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    storage_reference: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )
    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="uploaded",
        index=True,
    )
    metadata_: Mapped[Dict[str, Any]] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    parts: Mapped[List["ArtifactPart"]] = relationship(
        "ArtifactPart",
        back_populates="artifact",
        cascade="all, delete-orphan",
        order_by="ArtifactPart.sequence_number",
    )
    evidence: Mapped[List["ArtifactEvidence"]] = relationship(
        "ArtifactEvidence",
        back_populates="artifact",
        cascade="all, delete-orphan",
    )

    @property
    def metadata_json(self) -> Dict[str, Any]:
        return self.metadata_

    @metadata_json.setter
    def metadata_json(self, value: Dict[str, Any]) -> None:
        self.metadata_ = value

    def __init__(self, **kwargs: Any) -> None:
        if "metadata_json" in kwargs and "metadata_" not in kwargs:
            kwargs["metadata_"] = kwargs.pop("metadata_json")
        super().__init__(**kwargs)

    __table_args__ = (
        Index("ix_artifacts_org_ws", "organization_id", "workspace_id"),
        Index("ix_artifacts_ws_status", "workspace_id", "status"),
    )


class ArtifactPart(Base):
    """
    Normalized sub-element extracted from an Artifact (e.g. text page, table, image frame, transcript).
    Downstream context ingestion references these parts.
    """
    __tablename__ = "artifact_parts"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    artifact_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("artifacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    part_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    sequence_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    content_reference: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
    )
    text_content: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    metadata_: Mapped[Dict[str, Any]] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
    )
    content_hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
    )
    token_estimate: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    artifact: Mapped["Artifact"] = relationship(
        "Artifact",
        back_populates="parts",
    )

    @property
    def metadata_json(self) -> Dict[str, Any]:
        return self.metadata_

    @metadata_json.setter
    def metadata_json(self, value: Dict[str, Any]) -> None:
        self.metadata_ = value

    def __init__(self, **kwargs: Any) -> None:
        if "metadata_json" in kwargs and "metadata_" not in kwargs:
            kwargs["metadata_"] = kwargs.pop("metadata_json")
        super().__init__(**kwargs)

    __table_args__ = (
        Index("ix_artifact_parts_artifact_seq", "artifact_id", "sequence_number"),
    )


class ArtifactEvidence(Base):
    """
    Grounded evidence link connecting model claims or outputs back to concrete artifact coordinates.
    Stores page numbers, timestamps, spatial bounding regions, or raw text excerpts.
    """
    __tablename__ = "artifact_evidence"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    artifact_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("artifacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    part_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("artifact_parts.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    page: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    timestamp: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    region: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    source_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    metadata_: Mapped[Dict[str, Any]] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    artifact: Mapped["Artifact"] = relationship(
        "Artifact",
        back_populates="evidence",
    )

    __table_args__ = (
        Index("ix_artifact_evidence_artifact_part", "artifact_id", "part_id"),
    )
