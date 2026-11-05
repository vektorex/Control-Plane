from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean, ForeignKey, Integer
from sqlalchemy.sql import func
from backend.app.db.base import Base

class Release(Base):
    __tablename__ = "releases"

    id = Column(String(36), primary_key=True, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    change_request_id = Column(String(36), ForeignKey("change_requests.id"), nullable=False, index=True)

    release_type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)

    source_environment = Column(String(50), nullable=False)
    target_environment = Column(String(50), nullable=False)

    requested_by = Column(String(36), nullable=False)
    release_plan_id = Column(String(36), nullable=True)
    current_stage = Column(String(50), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

class ReleaseCandidate(Base):
    __tablename__ = "release_candidates"

    id = Column(String(36), primary_key=True, index=True)
    release_id = Column(String(36), ForeignKey("releases.id"), nullable=False, index=True)

    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(36), nullable=False)

    source_version = Column(String(50), nullable=False)
    target_version = Column(String(50), nullable=False)

    current_state_snapshot = Column(JSON, nullable=False)
    proposed_state_snapshot = Column(JSON, nullable=False)
    change_summary = Column(JSON, nullable=False)

    impact_analysis_id = Column(String(36), nullable=False)
    decision_record_id = Column(String(36), nullable=False)

    candidate_status = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class ReleaseEnvironment(Base):
    __tablename__ = "release_environments"

    id = Column(String(36), primary_key=True, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    environment_type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)

    governance_policy_reference = Column(String(255), nullable=True)

    requires_approval = Column(Boolean, nullable=False, default=False)
    requires_evaluation = Column(Boolean, nullable=False, default=False)
    requires_simulation = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class ReleasePlan(Base):
    __tablename__ = "release_plans"

    id = Column(String(36), primary_key=True, index=True)
    release_id = Column(String(36), ForeignKey("releases.id"), nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)

    stages = Column(JSON, nullable=False)
    preconditions = Column(JSON, nullable=False)
    verification_requirements = Column(JSON, nullable=False)
    rollback_requirements = Column(JSON, nullable=False)

    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_immutable = Column(Boolean, nullable=False, default=False)

class ReleaseStageRecord(Base):
    __tablename__ = "release_stage_records"

    id = Column(String(36), primary_key=True, index=True)
    release_id = Column(String(36), ForeignKey("releases.id"), nullable=False, index=True)

    stage_key = Column(String(50), nullable=False)
    stage_order = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False)

    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    evidence = Column(JSON, nullable=True)
    error = Column(JSON, nullable=True)

class ReleaseFreeze(Base):
    __tablename__ = "release_freezes"

    id = Column(String(36), primary_key=True, index=True)
    scope_type = Column(String(50), nullable=False)
    scope_id = Column(String(36), nullable=False)

    reason = Column(Text, nullable=False)
    starts_at = Column(DateTime(timezone=True), nullable=False)
    ends_at = Column(DateTime(timezone=True), nullable=True)

    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    active = Column(Boolean, nullable=False, default=True)

class ReleaseLock(Base):
    __tablename__ = "release_locks"

    id = Column(String(36), primary_key=True, index=True)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(36), nullable=False)
    release_id = Column(String(36), ForeignKey("releases.id"), nullable=False)

    acquired_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    heartbeat_at = Column(DateTime(timezone=True), nullable=False)

class ReleaseObservation(Base):
    __tablename__ = "release_observations"

    id = Column(String(36), primary_key=True, index=True)
    release_id = Column(String(36), ForeignKey("releases.id"), nullable=False, index=True)

    observation_type = Column(String(50), nullable=False)
    source = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)
    value = Column(JSON, nullable=False)

    observed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class ReleaseVerification(Base):
    __tablename__ = "release_verifications"

    id = Column(String(36), primary_key=True, index=True)
    release_id = Column(String(36), ForeignKey("releases.id"), nullable=False, index=True)

    verification_type = Column(String(50), nullable=False)
    expected_state = Column(JSON, nullable=False)
    observed_state = Column(JSON, nullable=False)

    status = Column(String(50), nullable=False)
    evidence = Column(JSON, nullable=True)

    verified_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class ReleaseRollback(Base):
    __tablename__ = "release_rollbacks"

    id = Column(String(36), primary_key=True, index=True)
    release_id = Column(String(36), ForeignKey("releases.id"), nullable=False, index=True)

    status = Column(String(50), nullable=False)
    strategy = Column(String(50), nullable=False)

    target_version = Column(String(50), nullable=False)
    reason = Column(Text, nullable=False)

    requested_by = Column(String(36), nullable=False)
    approved_by = Column(String(36), nullable=True)

    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    verification_status = Column(String(50), nullable=True)

class ReleaseEvidence(Base):
    __tablename__ = "release_evidence"

    id = Column(String(36), primary_key=True, index=True)
    release_id = Column(String(36), ForeignKey("releases.id"), nullable=False, index=True)

    evidence_type = Column(String(50), nullable=False)
    source_id = Column(String(36), nullable=False)
    details = Column(JSON, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class ReleaseTimelineEvent(Base):
    __tablename__ = "release_timeline_events"

    id = Column(String(36), primary_key=True, index=True)
    release_id = Column(String(36), ForeignKey("releases.id"), nullable=False, index=True)

    event_type = Column(String(50), nullable=False)
    actor_type = Column(String(50), nullable=False)
    actor_id = Column(String(36), nullable=True)

    stage = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)

    metadata_payload = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
