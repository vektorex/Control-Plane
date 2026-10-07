from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean, ForeignKey, Integer
from sqlalchemy.sql import func
from app.db.base import Base

class ProgressiveRollout(Base):
    __tablename__ = "progressive_rollouts"

    id = Column(String(36), primary_key=True, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True, index=True)

    release_id = Column(String(36), ForeignKey("releases.id"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    strategy_type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)

    current_stage_id = Column(String(36), nullable=True)

    target_scope = Column(JSON, nullable=False)
    policy = Column(JSON, nullable=False)

    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

class RolloutPlan(Base):
    __tablename__ = "rollout_plans"
    
    id = Column(String(36), primary_key=True, index=True)
    rollout_id = Column(String(36), ForeignKey("progressive_rollouts.id"), nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    
    stages = Column(JSON, nullable=False)
    gate_policy = Column(JSON, nullable=False)
    observation_policy = Column(JSON, nullable=False)
    rollback_policy = Column(JSON, nullable=False)
    
    is_immutable = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class RolloutStage(Base):
    __tablename__ = "rollout_stages"

    id = Column(String(36), primary_key=True, index=True)
    rollout_id = Column(String(36), ForeignKey("progressive_rollouts.id"), nullable=False, index=True)

    stage_order = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)

    target_percentage = Column(Integer, nullable=True)
    target_scope = Column(JSON, nullable=False)

    status = Column(String(50), nullable=False)

    minimum_observation_seconds = Column(Integer, nullable=False, default=0)
    gate_policy = Column(JSON, nullable=False)
    health_snapshot = Column(JSON, nullable=True)

    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

class RolloutTarget(Base):
    __tablename__ = "rollout_targets"

    id = Column(String(36), primary_key=True, index=True)
    rollout_id = Column(String(36), ForeignKey("progressive_rollouts.id"), nullable=False, index=True)

    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(36), nullable=False)
    release_id = Column(String(36), nullable=False)

    target_type = Column(String(50), nullable=False)
    target_id = Column(String(36), nullable=False)

    eligible = Column(Boolean, nullable=False, default=True)
    reason = Column(Text, nullable=True)
    status = Column(String(50), nullable=False)

class RolloutCohort(Base):
    __tablename__ = "rollout_cohorts"

    id = Column(String(36), primary_key=True, index=True)
    rollout_id = Column(String(36), ForeignKey("progressive_rollouts.id"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    selection_type = Column(String(50), nullable=False)
    selection_config = Column(JSON, nullable=False)

    member_count = Column(Integer, nullable=True)
    membership_snapshot = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class RolloutHealthSnapshot(Base):
    __tablename__ = "rollout_health_snapshots"

    id = Column(String(36), primary_key=True, index=True)
    rollout_id = Column(String(36), ForeignKey("progressive_rollouts.id"), nullable=False, index=True)
    stage_id = Column(String(36), ForeignKey("rollout_stages.id"), nullable=False, index=True)

    observed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    source = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)

    signals = Column(JSON, nullable=False)
    unknown_signals = Column(JSON, nullable=False)

class RolloutComparison(Base):
    __tablename__ = "rollout_comparisons"

    id = Column(String(36), primary_key=True, index=True)
    rollout_id = Column(String(36), ForeignKey("progressive_rollouts.id"), nullable=False, index=True)

    current_version = Column(String(50), nullable=False)
    candidate_version = Column(String(50), nullable=False)

    baseline_metrics = Column(JSON, nullable=False)
    candidate_metrics = Column(JSON, nullable=False)
    differences = Column(JSON, nullable=False)

    evidence = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class RolloutGate(Base):
    __tablename__ = "rollout_gates"

    id = Column(String(36), primary_key=True, index=True)
    rollout_id = Column(String(36), ForeignKey("progressive_rollouts.id"), nullable=False, index=True)
    stage_id = Column(String(36), ForeignKey("rollout_stages.id"), nullable=False, index=True)

    gate_type = Column(String(50), nullable=False)
    condition = Column(JSON, nullable=False)

    status = Column(String(50), nullable=False)
    source = Column(String(100), nullable=False)
    evidence = Column(JSON, nullable=True)

    evaluated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class RolloutEvidence(Base):
    __tablename__ = "rollout_evidence"

    id = Column(String(36), primary_key=True, index=True)
    rollout_id = Column(String(36), ForeignKey("progressive_rollouts.id"), nullable=False, index=True)

    evidence_type = Column(String(50), nullable=False)
    source_id = Column(String(36), nullable=False)
    details = Column(JSON, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class RolloutTimelineEvent(Base):
    __tablename__ = "rollout_timeline_events"

    id = Column(String(36), primary_key=True, index=True)
    rollout_id = Column(String(36), ForeignKey("progressive_rollouts.id"), nullable=False, index=True)

    event_type = Column(String(50), nullable=False)
    actor_type = Column(String(50), nullable=False)
    actor_id = Column(String(36), nullable=True)

    stage = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    metadata_payload = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class RolloutPause(Base):
    __tablename__ = "rollout_pauses"
    
    id = Column(String(36), primary_key=True, index=True)
    rollout_id = Column(String(36), ForeignKey("progressive_rollouts.id"), nullable=False, index=True)
    
    reason = Column(String(100), nullable=False)
    details = Column(Text, nullable=True)
    
    requested_by = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
