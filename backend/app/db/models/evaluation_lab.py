import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from backend.app.db.models.guid import GUID

if TYPE_CHECKING:
    from backend.app.db.models.project import Project
    from backend.app.db.models.run import Run
    from backend.app.db.models.user import User
    from backend.app.db.models.workflow import WorkflowRun
    from backend.app.db.models.workspace import Workspace


class EvaluationDataset(Base):
    """
    EvaluationDataset entity representing a collection of test/evaluation cases.
    Datasets are versioned; once a dataset version is used by a completed experiment,
    it becomes permanently immutable to preserve reproducibility.
    """
    __tablename__ = "evaluation_datasets"

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
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="draft",
        index=True,
    )  # draft | active | archived
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="SET NULL"),
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
    workspace: Mapped["Workspace"] = relationship("Workspace")
    project: Mapped[Optional["Project"]] = relationship("Project")
    creator: Mapped[Optional["User"]] = relationship("User")
    versions: Mapped[List["EvaluationDatasetVersion"]] = relationship(
        "EvaluationDatasetVersion",
        back_populates="dataset",
        cascade="all, delete-orphan",
        order_by="EvaluationDatasetVersion.version.desc()",
    )


class EvaluationDatasetVersion(Base):
    """
    A fixed, immutable snapshot of evaluation cases.
    Completed experiments reference this version to guarantee deterministic evaluations.
    """
    __tablename__ = "evaluation_dataset_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("evaluation_datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    dataset: Mapped["EvaluationDataset"] = relationship(
        "EvaluationDataset",
        back_populates="versions",
    )
    creator: Mapped[Optional["User"]] = relationship("User")
    cases: Mapped[List["EvaluationCase"]] = relationship(
        "EvaluationCase",
        back_populates="dataset_version",
        cascade="all, delete-orphan",
        order_by="EvaluationCase.created_at.asc()",
    )
    experiments: Mapped[List["EvaluationExperiment"]] = relationship(
        "EvaluationExperiment",
        back_populates="dataset_version",
    )


class EvaluationCase(Base):
    """
    An individual evaluation case containing input payloads, expected outputs or context,
    and deterministic assertion rules.
    """
    __tablename__ = "evaluation_cases"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    dataset_version_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("evaluation_dataset_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    case_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    input_data: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    expected_output: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    expected_context: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    expected_sources: Mapped[Optional[List[Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    assertions: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    # Use case_metadata column to avoid collision with SQLAlchemy Base.metadata
    case_metadata: Mapped[Dict[str, Any]] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
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
    dataset_version: Mapped["EvaluationDatasetVersion"] = relationship(
        "EvaluationDatasetVersion",
        back_populates="cases",
    )
    runs: Mapped[List["EvaluationExperimentRun"]] = relationship(
        "EvaluationExperimentRun",
        back_populates="case",
        cascade="all, delete-orphan",
    )


class EvaluationExperiment(Base):
    """
    An evaluation experiment runs a fixed dataset version against an evaluation target
    (task, workflow, model, prompt, or replay snapshot) using the existing execution infrastructure.
    """
    __tablename__ = "evaluation_experiments"

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
    dataset_version_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("evaluation_dataset_versions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    target_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # task | workflow | workflow_version | model | prompt | replay_snapshot
    target_configuration: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="draft",
        index=True,
    )  # draft | queued | running | completed | failed | cancelled
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace")
    project: Mapped[Optional["Project"]] = relationship("Project")
    dataset_version: Mapped["EvaluationDatasetVersion"] = relationship(
        "EvaluationDatasetVersion",
        back_populates="experiments",
    )
    creator: Mapped[Optional["User"]] = relationship("User")
    runs: Mapped[List["EvaluationExperimentRun"]] = relationship(
        "EvaluationExperimentRun",
        back_populates="experiment",
        cascade="all, delete-orphan",
        order_by="EvaluationExperimentRun.created_at.asc()",
    )


class EvaluationExperimentRun(Base):
    """
    Execution outcome of an individual evaluation case within an experiment.
    Tracks input/output snapshots, assertion results, and existing EvaluationEngine findings.
    """
    __tablename__ = "evaluation_experiment_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("evaluation_experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("evaluation_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="queued",
        index=True,
    )  # queued | running | passed | failed | warning | error | cancelled
    input_snapshot: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    output_snapshot: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    evaluation_result: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )  # stores assertions outcomes and evaluation_findings
    run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    workflow_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("workflow_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    latency_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    input_tokens: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    output_tokens: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    estimated_cost: Mapped[Optional[float]] = mapped_column(
        Float,
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    experiment: Mapped["EvaluationExperiment"] = relationship(
        "EvaluationExperiment",
        back_populates="runs",
    )
    case: Mapped["EvaluationCase"] = relationship(
        "EvaluationCase",
        back_populates="runs",
    )
    run: Mapped[Optional["Run"]] = relationship("Run")
    workflow_run: Mapped[Optional["WorkflowRun"]] = relationship("WorkflowRun")
