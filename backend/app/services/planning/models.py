"""
SQLAlchemy models for Step 44:
AI Work Planning, Capacity & Resource Optimization Layer.
"""
from datetime import datetime, timezone
import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from backend.app.db.base import Base


def _gen_uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class WorkPlan(Base):
    """
    Work Plan representing an evidence-backed execution sequence aligned with objectives and outcomes.
    """
    __tablename__ = "work_plans"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    workspace_id = Column(String(36), nullable=False, index=True)
    project_id = Column(String(36), nullable=True, index=True)
    objective_id = Column(String(36), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(
        String(32),
        nullable=False,
        default="draft",
        index=True,
    )  # draft, proposed, approved, active, paused, completed, cancelled, archived
    planning_mode = Column(
        String(32),
        nullable=False,
        default="assisted",
    )  # manual, assisted, optimized
    planning_horizon_start = Column(DateTime(timezone=True), nullable=True)
    planning_horizon_end = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    # Relationships
    versions = relationship("WorkPlanVersion", back_populates="work_plan", cascade="all, delete-orphan", order_by="desc(WorkPlanVersion.version)")
    scenarios = relationship("PlanningScenario", back_populates="work_plan", cascade="all, delete-orphan")
    recommendations = relationship("PlanningRecommendation", back_populates="work_plan", cascade="all, delete-orphan")
    staleness_records = relationship("PlanStalenessRecord", back_populates="work_plan", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_work_plans_ws_status", "workspace_id", "status"),
    )


class WorkPlanVersion(Base):
    """
    Immutable published snapshot of a Work Plan. Published versions cannot be altered.
    """
    __tablename__ = "work_plan_versions"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    work_plan_id = Column(String(36), ForeignKey("work_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    plan_snapshot = Column(JSON, nullable=False, default=dict)
    constraint_snapshot = Column(JSON, nullable=False, default=dict)
    capacity_snapshot = Column(JSON, nullable=False, default=dict)
    resource_snapshot = Column(JSON, nullable=False, default=dict)
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, index=True)
    published_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    work_plan = relationship("WorkPlan", back_populates="versions")
    items = relationship("PlanningItem", back_populates="version", cascade="all, delete-orphan")
    dependencies = relationship("PlanningDependency", back_populates="version", cascade="all, delete-orphan")
    constraints = relationship("PlanningConstraint", back_populates="version", cascade="all, delete-orphan")
    candidates = relationship("ScheduleCandidate", back_populates="version", cascade="all, delete-orphan")
    blockers = relationship("PlanningBlocker", back_populates="version", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("work_plan_id", "version", name="uq_work_plan_version"),
    )


class PlanningItem(Base):
    """
    Item within a work plan version referencing existing work (tasks, workflows, agents, etc.).
    """
    __tablename__ = "planning_items"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    work_plan_version_id = Column(String(36), ForeignKey("work_plan_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_type = Column(String(64), nullable=False, index=True)  # task, workflow, agent_run, etc.
    resource_id = Column(String(64), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String(32), nullable=False, default="medium")
    estimated_duration = Column(Integer, nullable=True)  # in minutes
    estimated_cost = Column(Float, nullable=True)
    required_capabilities = Column(JSON, nullable=False, default=list)  # list of strings
    status = Column(String(32), nullable=False, default="planned", index=True)
    planned_start = Column(DateTime(timezone=True), nullable=True)
    planned_end = Column(DateTime(timezone=True), nullable=True)
    actual_start = Column(DateTime(timezone=True), nullable=True)
    actual_end = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    # Relationships
    version = relationship("WorkPlanVersion", back_populates="items")
    blockers = relationship("PlanningBlocker", back_populates="planning_item")
    reservations = relationship("CapacityReservation", back_populates="planning_item")


class PlanningDependency(Base):
    """
    Precedence and dependency link between two planning items.
    """
    __tablename__ = "planning_dependencies"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    work_plan_version_id = Column(String(36), ForeignKey("work_plan_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    predecessor_item_id = Column(String(36), ForeignKey("planning_items.id", ondelete="CASCADE"), nullable=False, index=True)
    successor_item_id = Column(String(36), ForeignKey("planning_items.id", ondelete="CASCADE"), nullable=False, index=True)
    dependency_type = Column(String(32), nullable=False, default="finish_to_start")  # finish_to_start, start_to_start, etc.
    lag = Column(Integer, nullable=False, default=0)  # minutes
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    # Relationships
    version = relationship("WorkPlanVersion", back_populates="dependencies")
    predecessor = relationship("PlanningItem", foreign_keys=[predecessor_item_id])
    successor = relationship("PlanningItem", foreign_keys=[successor_item_id])


class WorkResource(Base):
    """
    Resource reference (human, agent, workflow, tool, connector, system) available for planning.
    Does not duplicate existing User or Agent records.
    """
    __tablename__ = "work_resources"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    workspace_id = Column(String(36), nullable=False, index=True)
    project_id = Column(String(36), nullable=True, index=True)
    resource_type = Column(String(32), nullable=False, index=True)  # human, agent, agent_team, workflow, tool, connector, system
    resource_ref = Column(String(64), nullable=False, index=True)  # user_id, agent_id, etc.
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(32), nullable=False, default="active", index=True)  # active, inactive, paused, decommissioned
    capabilities = Column(JSON, nullable=False, default=list)  # list of tags
    availability_policy = Column(JSON, nullable=False, default=dict)  # limits, constraints
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    # Relationships
    availabilities = relationship("ResourceAvailability", back_populates="resource", cascade="all, delete-orphan")
    snapshots = relationship("CapacitySnapshot", back_populates="resource", cascade="all, delete-orphan")
    reservations = relationship("CapacityReservation", back_populates="resource", cascade="all, delete-orphan")


class ResourceAvailability(Base):
    """
    Time window availability for a resource.
    Never fabricated. If unknown, it must be marked unknown.
    """
    __tablename__ = "resource_availability"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    resource_id = Column(String(36), ForeignKey("work_resources.id", ondelete="CASCADE"), nullable=False, index=True)
    start_at = Column(DateTime(timezone=True), nullable=False, index=True)
    end_at = Column(DateTime(timezone=True), nullable=False, index=True)
    capacity_units = Column(Float, nullable=False, default=1.0)
    reserved_units = Column(Float, nullable=False, default=0.0)
    source = Column(String(32), nullable=False, default="manual")  # manual, calendar, system, policy, derived, unknown
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    # Relationships
    resource = relationship("WorkResource", back_populates="availabilities")


class CapacitySnapshot(Base):
    """
    Historical or calculated snapshot of capacity for a given period.
    """
    __tablename__ = "capacity_snapshots"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    workspace_id = Column(String(36), nullable=False, index=True)
    project_id = Column(String(36), nullable=True)
    resource_id = Column(String(36), ForeignKey("work_resources.id", ondelete="CASCADE"), nullable=False, index=True)
    snapshot_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False, index=True)
    available_units = Column(Float, nullable=False, default=0.0)
    reserved_units = Column(Float, nullable=False, default=0.0)
    allocated_units = Column(Float, nullable=False, default=0.0)
    remaining_units = Column(Float, nullable=False, default=0.0)
    source = Column(String(32), nullable=False, default="system")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    # Relationships
    resource = relationship("WorkResource", back_populates="snapshots")


class CapacityReservation(Base):
    """
    Expirable, authorized capacity reservation for a planning item.
    """
    __tablename__ = "capacity_reservations"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    resource_id = Column(String(36), ForeignKey("work_resources.id", ondelete="CASCADE"), nullable=False, index=True)
    planning_item_id = Column(String(36), ForeignKey("planning_items.id", ondelete="SET NULL"), nullable=True, index=True)
    start_at = Column(DateTime(timezone=True), nullable=False, index=True)
    end_at = Column(DateTime(timezone=True), nullable=False, index=True)
    units = Column(Float, nullable=False, default=1.0)
    status = Column(String(32), nullable=False, default="proposed", index=True)  # proposed, reserved, released, expired, cancelled
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    # Relationships
    resource = relationship("WorkResource", back_populates="reservations")
    planning_item = relationship("PlanningItem", back_populates="reservations")


class PlanningConstraint(Base):
    """
    Hard or soft constraint bounding the work plan.
    Hard constraints cannot be bypassed by optimization.
    """
    __tablename__ = "planning_constraints"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    work_plan_version_id = Column(String(36), ForeignKey("work_plan_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    constraint_type = Column(String(32), nullable=False, index=True)  # deadline, dependency, capacity, budget, approval, etc.
    configuration = Column(JSON, nullable=False, default=dict)
    priority = Column(Integer, nullable=False, default=1)
    hard_constraint = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    # Relationships
    version = relationship("WorkPlanVersion", back_populates="constraints")


class ScheduleCandidate(Base):
    """
    Generated candidate schedule for a work plan version. Multi-dimensional comparison, no single aggregate score.
    """
    __tablename__ = "schedule_candidates"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    work_plan_version_id = Column(String(36), ForeignKey("work_plan_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    schedule = Column(JSON, nullable=False, default=dict)
    assumptions = Column(JSON, nullable=False, default=list)
    constraint_results = Column(JSON, nullable=False, default=dict)
    resource_allocations = Column(JSON, nullable=False, default=dict)
    estimated_duration = Column(Float, nullable=True)  # minutes
    estimated_cost = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    # Relationships
    version = relationship("WorkPlanVersion", back_populates="candidates")


class PlanningBlocker(Base):
    """
    Identified execution blocker with evidence.
    """
    __tablename__ = "planning_blockers"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    work_plan_version_id = Column(String(36), ForeignKey("work_plan_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    planning_item_id = Column(String(36), ForeignKey("planning_items.id", ondelete="SET NULL"), nullable=True, index=True)
    type = Column(String(32), nullable=False)  # dependency, capacity, approval, permission, resource, deadline, etc.
    description = Column(Text, nullable=False)
    severity = Column(String(32), nullable=False, default="medium")  # low, medium, high, critical
    evidence_ids = Column(JSON, nullable=False, default=list)
    status = Column(String(32), nullable=False, default="open", index=True)  # open, resolved, ignored, superseded
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    version = relationship("WorkPlanVersion", back_populates="blockers")
    planning_item = relationship("PlanningItem", back_populates="blockers")


class PlanningScenario(Base):
    """
    Isolated What-If planning scenario that never alters production plans.
    """
    __tablename__ = "planning_scenarios"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    workspace_id = Column(String(36), nullable=False, index=True)
    work_plan_id = Column(String(36), ForeignKey("work_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    modifications = Column(JSON, nullable=False, default=dict)  # changes to simulate
    simulation_results = Column(JSON, nullable=False, default=dict)
    comparison = Column(JSON, nullable=False, default=dict)
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    # Relationships
    work_plan = relationship("WorkPlan", back_populates="scenarios")


class PlanningRecommendation(Base):
    """
    Advisory recommendation for optimizing or unblocking a work plan.
    Does not execute privileged actions autonomously.
    """
    __tablename__ = "planning_recommendations"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    workspace_id = Column(String(36), nullable=False, index=True)
    work_plan_id = Column(String(36), ForeignKey("work_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    recommendation_type = Column(String(64), nullable=False)  # move_task, split_task, etc.
    description = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    evidence_ids = Column(JSON, nullable=False, default=list)
    affected_resources = Column(JSON, nullable=False, default=list)
    affected_items = Column(JSON, nullable=False, default=list)
    risk = Column(Text, nullable=True)
    assumptions = Column(JSON, nullable=False, default=list)
    status = Column(String(32), nullable=False, default="proposed", index=True)  # proposed, accepted, rejected, dismissed
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    # Relationships
    work_plan = relationship("WorkPlan", back_populates="recommendations")


class PlanStalenessRecord(Base):
    """
    Records detection of stale state in a plan. Prevents silent execution of stale plans.
    """
    __tablename__ = "plan_staleness_records"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    work_plan_id = Column(String(36), ForeignKey("work_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    reason = Column(Text, nullable=False)
    detected_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    is_stale = Column(Boolean, nullable=False, default=True, index=True)

    # Relationships
    work_plan = relationship("WorkPlan", back_populates="staleness_records")
