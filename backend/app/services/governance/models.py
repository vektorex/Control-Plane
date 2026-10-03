"""
SQLAlchemy models for Step 32: AI Governance, Policy Control Plane, and Safety Guardrails.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base
from backend.app.db.models.guid import GUID
from backend.app.services.governance.constants import (
    PolicyScope,
    PolicyStatus,
    PolicyVersionStatus,
    BudgetReservationStatus,
    GovernanceDecisionType,
)


class GovernancePolicy(Base):
    """
    Governance policy definition. Policies are versioned; active version is immutable.
    Multi-tenant scoped to organization, optionally workspace and project.
    """
    __tablename__ = "governance_policies"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    workspace_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), nullable=True, index=True)
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=PolicyStatus.ACTIVE.value,
        index=True,
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100, index=True)
    scope: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=PolicyScope.WORKSPACE.value,
        index=True,
    )
    active_version_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), nullable=True, index=True)
    created_by: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False)
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

    __table_args__ = (
        Index("ix_gov_policy_org_scope_status", "organization_id", "scope", "status"),
        Index("ix_gov_policy_workspace_status", "workspace_id", "status", "priority"),
        Index("ix_gov_policy_project_status", "project_id", "status"),
    )


class GovernancePolicyVersion(Base):
    """
    Immutable versioned snapshot of a GovernancePolicy's rules.
    Active versions are sealed; only draft versions can be edited.
    """
    __tablename__ = "governance_policy_versions"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    policy_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    rules: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=PolicyVersionStatus.DRAFT.value,
        index=True,
    )
    change_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    activated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    deactivated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("policy_id", "version_number", name="uq_policy_version_number"),
        Index("ix_gov_policy_ver_status", "policy_id", "status"),
    )


class BudgetPolicy(Base):
    """
    Cost and budget constraints for organization, workspace, and project.
    """
    __tablename__ = "budget_policies"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    workspace_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), nullable=True, index=True)
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), nullable=True, index=True)
    daily_limit_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    monthly_limit_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    per_run_limit_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    per_user_daily_limit_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    soft_threshold_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.80)
    hard_threshold_pct: Mapped[float] = mapped_column(Float, nullable=False, default=1.00)
    on_soft_breach: Mapped[str] = mapped_column(String(32), nullable=False, default="warn")
    on_hard_breach: Mapped[str] = mapped_column(String(32), nullable=False, default="deny")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_budget_policy_workspace", "workspace_id", "is_active"),
        Index("ix_budget_policy_project", "project_id", "is_active"),
    )


class BudgetReservation(Base):
    """
    Tracks active budget reservations before execution.
    Prevents concurrent runs from exceeding hard limits.
    """
    __tablename__ = "budget_reservations"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), nullable=True, index=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), nullable=True, index=True)
    run_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), nullable=True, index=True)
    job_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), nullable=True, index=True)
    reserved_amount_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    actual_amount_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=BudgetReservationStatus.PENDING.value,
        index=True,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    settled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_budget_reservation_active", "workspace_id", "status", "expires_at"),
        Index("ix_budget_reservation_run", "run_id", "status"),
    )


class GovernanceDecisionLog(Base):
    """
    Audit log of governance decisions for observability and compliance.
    Never stores secrets or sensitive request content.
    """
    __tablename__ = "governance_decisions"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    workspace_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), nullable=True, index=True)
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), nullable=True, index=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), nullable=True, index=True)
    enforcement_point: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    decision: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    reasons: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    matched_policy_ids: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    policy_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    constraints: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    required_approvals: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    required_verifications: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    evaluation_latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        Index("ix_gov_decision_workspace_decision", "workspace_id", "decision", "created_at"),
        Index("ix_gov_decision_enforcement", "enforcement_point", "decision", "created_at"),
    )
