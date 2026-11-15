import uuid
from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey, Boolean, Integer
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ReleaseOptimizationScenario(Base):
    __tablename__ = "release_optimization_scenarios"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), nullable=False, index=True)
    workspace_id = Column(String(36), nullable=False, index=True)
    project_id = Column(String(36), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    release_train_id = Column(String(36), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="draft")
    scenario_type = Column(String(50), nullable=False)
    base_snapshot_id = Column(String(36), nullable=True)
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

class ReleaseOptimizationScenarioVersion(Base):
    __tablename__ = "release_optimization_scenario_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scenario_id = Column(String(36), ForeignKey("release_optimization_scenarios.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False)
    input_snapshot = Column(JSON, nullable=False)
    constraint_snapshot = Column(JSON, nullable=False)
    release_snapshot = Column(JSON, nullable=False)
    planning_snapshot = Column(JSON, nullable=False)
    contract_snapshot = Column(JSON, nullable=False)
    governance_snapshot = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=_utcnow)

class OptimizationConstraint(Base):
    __tablename__ = "release_optimization_constraints"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scenario_id = Column(String(36), ForeignKey("release_optimization_scenarios.id", ondelete="CASCADE"), nullable=False)
    constraint_type = Column(String(50), nullable=False)
    source_system = Column(String(50), nullable=False)
    resource_id = Column(String(36), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(Integer, default=0)
    hard_constraint = Column(Boolean, default=True)
    active = Column(Boolean, default=True)
    evidence = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

class OptimizationCandidate(Base):
    __tablename__ = "release_optimization_candidates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scenario_id = Column(String(36), ForeignKey("release_optimization_scenarios.id", ondelete="CASCADE"), nullable=False)
    candidate_number = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="valid")
    sequence_hash = Column(String(64), nullable=False)
    constraint_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=_utcnow)

class OptimizationCandidateRelease(Base):
    __tablename__ = "release_optimization_candidate_releases"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id = Column(String(36), ForeignKey("release_optimization_candidates.id", ondelete="CASCADE"), nullable=False)
    release_id = Column(String(36), nullable=False)
    sequence_number = Column(Integer, nullable=False)
    wave_number = Column(Integer, nullable=True)
    planned_start = Column(DateTime, nullable=True)
    planned_end = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=False)
    reason = Column(Text, nullable=True)

class OptimizationCandidateWave(Base):
    __tablename__ = "release_optimization_candidate_waves"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id = Column(String(36), ForeignKey("release_optimization_candidates.id", ondelete="CASCADE"), nullable=False)
    wave_number = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)
    planned_start = Column(DateTime, nullable=True)
    planned_end = Column(DateTime, nullable=True)
    release_ids = Column(JSON, nullable=False)
    constraints = Column(JSON, nullable=True)
    status = Column(String(50), nullable=False)

class OptimizationComparison(Base):
    __tablename__ = "release_optimization_comparisons"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scenario_id = Column(String(36), ForeignKey("release_optimization_scenarios.id", ondelete="CASCADE"), nullable=False)
    candidate_a = Column(String(36), nullable=False)
    candidate_b = Column(String(36), nullable=False)
    differences = Column(JSON, nullable=False)
    constraint_changes = Column(JSON, nullable=False)
    schedule_changes = Column(JSON, nullable=False)
    wave_changes = Column(JSON, nullable=False)
    dependency_changes = Column(JSON, nullable=False)
    capacity_changes = Column(JSON, nullable=False)
    window_changes = Column(JSON, nullable=False)
    contract_changes = Column(JSON, nullable=False)
    approval_changes = Column(JSON, nullable=False)
    revalidation_changes = Column(JSON, nullable=False)
    evidence = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

class OptimizationBottleneck(Base):
    __tablename__ = "release_optimization_bottlenecks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scenario_id = Column(String(36), ForeignKey("release_optimization_scenarios.id", ondelete="CASCADE"), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(36), nullable=False)
    description = Column(Text, nullable=False)
    affected_release_ids = Column(JSON, nullable=False)
    evidence = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=_utcnow)

class OptimizationRecommendation(Base):
    __tablename__ = "release_optimization_recommendations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scenario_id = Column(String(36), ForeignKey("release_optimization_scenarios.id", ondelete="CASCADE"), nullable=False)
    reason = Column(Text, nullable=False)
    evidence = Column(JSON, nullable=False)
    affected_releases = Column(JSON, nullable=False)
    constraints = Column(JSON, nullable=False)
    confidence_basis = Column(Text, nullable=False)
    created_at = Column(DateTime, default=_utcnow)

class OptimizationRun(Base):
    __tablename__ = "release_optimization_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scenario_id = Column(String(36), ForeignKey("release_optimization_scenarios.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), nullable=False, default="queued")
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    candidate_count = Column(Integer, default=0)
    constraint_count = Column(Integer, default=0)
    finding_count = Column(Integer, default=0)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

class OptimizationSensitivity(Base):
    __tablename__ = "release_optimization_sensitivities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scenario_id = Column(String(36), ForeignKey("release_optimization_scenarios.id", ondelete="CASCADE"), nullable=False)
    variable_name = Column(String(100), nullable=False)
    thresholds = Column(JSON, nullable=False)
    evidence = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=_utcnow)
