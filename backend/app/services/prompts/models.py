"""
SQLAlchemy models for Step 28: Prompt Management, Versioning, Release, and Experimentation.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from backend.app.db.models.guid import GUID

if TYPE_CHECKING:
    from backend.app.db.models.user import User
    from backend.app.db.models.workspace import Workspace
    from backend.app.db.models.project import Project
    from backend.app.services.access_control.models import Organization


class Prompt(Base):
    """
    Centralized Prompt asset entity scoped to an Organization, Workspace, and optional Project.
    """
    __tablename__ = "prompts"

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
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    prompt_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="instruction",
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="active",
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    archived_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    versions: Mapped[List["PromptVersion"]] = relationship(
        "PromptVersion",
        back_populates="prompt",
        cascade="all, delete-orphan",
        order_by="PromptVersion.version_number",
    )
    releases: Mapped[List["PromptRelease"]] = relationship(
        "PromptRelease",
        back_populates="prompt",
        cascade="all, delete-orphan",
        order_by="desc(PromptRelease.released_at)",
    )
    experiments: Mapped[List["PromptExperiment"]] = relationship(
        "PromptExperiment",
        back_populates="prompt",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_prompts_org_ws_key", "organization_id", "workspace_id", "key"),
        Index("ix_prompts_ws_status", "workspace_id", "status"),
        Index("ix_prompts_ws_type", "workspace_id", "prompt_type"),
    )


class PromptVersion(Base):
    """
    Immutable version of a prompt. Published versions cannot be altered.
    """
    __tablename__ = "prompt_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    prompt_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="draft",
        index=True,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    variable_schema: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
    model_requirements: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    execution_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    change_summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    content_hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )

    # Relationships
    prompt: Mapped["Prompt"] = relationship(
        "Prompt",
        back_populates="versions",
    )

    __table_args__ = (
        UniqueConstraint("prompt_id", "version_number", name="uq_prompt_id_version_number"),
        Index("ix_prompt_versions_prompt_status", "prompt_id", "status"),
        Index("ix_prompt_versions_prompt_hash", "prompt_id", "content_hash"),
    )


class PromptRelease(Base):
    """
    Binding of a prompt version to a deployment environment (development, staging, production).
    Historical records are immutable; promotions/rollbacks insert new release records and supersede past ones.
    """
    __tablename__ = "prompt_releases"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    prompt_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    environment: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    version_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("prompt_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="active",
        index=True,
    )
    released_by: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    released_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    previous_version_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("prompt_versions.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    prompt: Mapped["Prompt"] = relationship(
        "Prompt",
        back_populates="releases",
    )
    version: Mapped["PromptVersion"] = relationship(
        "PromptVersion",
        foreign_keys=[version_id],
    )
    previous_version: Mapped[Optional["PromptVersion"]] = relationship(
        "PromptVersion",
        foreign_keys=[previous_version_id],
    )

    __table_args__ = (
        Index("ix_prompt_releases_env_status", "prompt_id", "environment", "status"),
    )


class PromptExperiment(Base):
    """
    Controlled A/B prompt experiment comparing variants with deterministic traffic assignment.
    """
    __tablename__ = "prompt_experiments"

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
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    prompt_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="draft",
        index=True,
    )
    allocation_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="user_id",
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    prompt: Mapped["Prompt"] = relationship(
        "Prompt",
        back_populates="experiments",
    )
    variants: Mapped[List["PromptExperimentVariant"]] = relationship(
        "PromptExperimentVariant",
        back_populates="experiment",
        cascade="all, delete-orphan",
        order_by="PromptExperimentVariant.label",
    )
    assignments: Mapped[List["PromptExperimentAssignment"]] = relationship(
        "PromptExperimentAssignment",
        back_populates="experiment",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_prompt_exp_ws_status", "workspace_id", "status"),
        Index("ix_prompt_exp_prompt_status", "prompt_id", "status"),
    )


class PromptExperimentVariant(Base):
    """
    A single variant arm in a prompt experiment (e.g. A, B, C) with relative traffic weight.
    """
    __tablename__ = "prompt_experiment_variants"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("prompt_experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    prompt_version_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("prompt_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    label: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    allocation_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    experiment: Mapped["PromptExperiment"] = relationship(
        "PromptExperiment",
        back_populates="variants",
    )
    version: Mapped["PromptVersion"] = relationship(
        "PromptVersion",
    )

    __table_args__ = (
        UniqueConstraint("experiment_id", "prompt_version_id", name="uq_exp_prompt_version"),
        UniqueConstraint("experiment_id", "label", name="uq_exp_variant_label"),
    )


class PromptExperimentAssignment(Base):
    """
    Persisted deterministic variant assignment for a given allocation key in an experiment.
    Guarantees sticky assignment across repeat invocations.
    """
    __tablename__ = "prompt_experiment_assignments"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("prompt_experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    variant_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("prompt_experiment_variants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    allocation_key_value: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    assigned_version_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("prompt_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    experiment: Mapped["PromptExperiment"] = relationship(
        "PromptExperiment",
        back_populates="assignments",
    )
    variant: Mapped["PromptExperimentVariant"] = relationship(
        "PromptExperimentVariant",
    )
    version: Mapped["PromptVersion"] = relationship(
        "PromptVersion",
    )

    __table_args__ = (
        UniqueConstraint("experiment_id", "allocation_key_value", name="uq_exp_alloc_key"),
    )
