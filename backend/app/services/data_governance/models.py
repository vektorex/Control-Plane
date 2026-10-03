"""
SQLAlchemy models for Step 33: Data Governance, Privacy & Compliance Evidence Layer.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from backend.app.db.database import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid_str() -> str:
    return str(uuid.uuid4())


class DataAsset(Base):
    """
    Logical representation of data controlled by the platform across all subsystems.
    Never stores plaintext secrets.
    """
    __tablename__ = "data_assets"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    organization_id = Column(String(36), nullable=False, index=True)
    workspace_id = Column(String(36), nullable=True, index=True)
    project_id = Column(String(36), nullable=True, index=True)

    asset_type = Column(String(50), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    data_classification = Column(String(32), nullable=False, default="internal", index=True)
    owner_type = Column(String(50), nullable=False, default="user")
    owner_id = Column(String(36), nullable=False, index=True)

    source_type = Column(String(50), nullable=False, default="direct")
    source_id = Column(String(255), nullable=True)
    storage_location = Column(String(255), nullable=False, default="logical:db")

    contains_personal_data = Column(Boolean, default=False, nullable=False)
    contains_sensitive_data = Column(Boolean, default=False, nullable=False)
    contains_secrets = Column(Boolean, default=False, nullable=False)

    retention_policy_id = Column(String(36), nullable=True, index=True)
    status = Column(String(32), nullable=False, default="active", index=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now, onupdate=_utc_now, server_default=func.now())
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    classifications = relationship("ClassificationRecord", back_populates="asset", cascade="all, delete-orphan")
    findings = relationship("DataFinding", back_populates="asset", cascade="all, delete-orphan")


class ClassificationRecord(Base):
    """
    Historical record of classification determinations and audits for a DataAsset.
    """
    __tablename__ = "classification_records"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    asset_id = Column(String(36), ForeignKey("data_assets.id", ondelete="CASCADE"), nullable=False, index=True)
    classification = Column(String(32), nullable=False, index=True)
    reason = Column(Text, nullable=True)
    detected_by = Column(String(50), nullable=False)  # manual, rule, system, connector, artifact_analysis, user_confirmed
    confidence = Column(Float, default=1.0, nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now, onupdate=_utc_now, server_default=func.now())
    reviewed_by = Column(String(36), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    asset = relationship("DataAsset", back_populates="classifications")


class DataFinding(Base):
    """
    Deterministic privacy/PII/secret finding for an asset.
    Stores fingerprint and masked preview ONLY; never stores raw secrets.
    """
    __tablename__ = "data_findings"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    asset_id = Column(String(36), ForeignKey("data_assets.id", ondelete="CASCADE"), nullable=False, index=True)
    finding_type = Column(String(50), nullable=False, index=True)
    location = Column(String(255), nullable=True)
    redaction_strategy = Column(String(50), nullable=False, default="mask")
    confidence = Column(Float, default=1.0, nullable=False)
    fingerprint = Column(String(64), nullable=False)
    preview = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now, server_default=func.now())

    asset = relationship("DataAsset", back_populates="findings")


class DataLineageEdge(Base):
    """
    Directed edge in the data lineage graph. Stores identifiers and metadata only.
    """
    __tablename__ = "data_lineage_edges"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    organization_id = Column(String(36), nullable=False, index=True)
    source_asset_id = Column(String(36), nullable=False, index=True)
    target_asset_id = Column(String(36), nullable=False, index=True)

    relationship_type = Column(String(50), nullable=False)  # derived_from, copied_from, embedded_from, etc.
    transformation_type = Column(String(50), nullable=False)  # direct, chunked, embedded, summarized, etc.

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now, server_default=func.now())
    created_by = Column(String(36), nullable=True)
    edge_metadata = Column("metadata", JSON, nullable=True)


class RetentionPolicy(Base):
    """
    Policy governing how long resources are kept and what action is taken at expiry.
    """
    __tablename__ = "retention_policies"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    organization_id = Column(String(36), nullable=False, index=True)
    workspace_id = Column(String(36), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    resource_type = Column(String(50), nullable=False, index=True)
    retention_days = Column(Integer, nullable=True)
    action = Column(String(32), nullable=False, default="retain")  # retain, archive, anonymize, delete
    grace_period_days = Column(Integer, nullable=False, default=7)
    enabled = Column(Boolean, default=True, nullable=False)

    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now, onupdate=_utc_now, server_default=func.now())


class DeletionRequest(Base):
    """
    Controlled deletion request audited through governance and dependency verification.
    """
    __tablename__ = "deletion_requests"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    organization_id = Column(String(36), nullable=False, index=True)
    workspace_id = Column(String(36), nullable=True, index=True)
    requested_by = Column(String(36), nullable=False)

    scope_type = Column(String(50), nullable=False)  # asset, resource, workspace, user
    scope_id = Column(String(255), nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String(32), nullable=False, default="requested", index=True)  # requested, awaiting_approval, approved, processing, completed, failed, cancelled, blocked

    requested_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now, server_default=func.now())
    approved_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    verification_status = Column(String(32), nullable=False, default="pending")
    verification_summary = Column(Text, nullable=True)
    error = Column(Text, nullable=True)


class ExportRequest(Base):
    """
    Export job request tracking sanitization, artifact storage, and expiration.
    """
    __tablename__ = "export_requests"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    organization_id = Column(String(36), nullable=False, index=True)
    workspace_id = Column(String(36), nullable=True, index=True)
    requested_by = Column(String(36), nullable=False)

    scope_type = Column(String(50), nullable=False)
    scope_id = Column(String(255), nullable=False)
    format = Column(String(16), nullable=False, default="json")  # json, jsonl, csv
    status = Column(String(32), nullable=False, default="requested", index=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now, server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    artifact_id = Column(String(36), nullable=True)
    manifest = Column(JSON, nullable=True)


class PrivacyRequest(Base):
    """
    Platform privacy workflow requests (access, export, deletion, correction, restriction).
    """
    __tablename__ = "privacy_requests"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    organization_id = Column(String(36), nullable=False, index=True)
    workspace_id = Column(String(36), nullable=True, index=True)
    requester_user_id = Column(String(36), nullable=False, index=True)

    request_type = Column(String(32), nullable=False)  # access, export, deletion, correction, restriction
    scope = Column(String(255), nullable=False, default="user")
    status = Column(String(32), nullable=False, default="pending", index=True)  # pending, in_review, processing, completed, rejected
    verification_status = Column(String(32), nullable=False, default="unverified")

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now, onupdate=_utc_now, server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)


class LegalHold(Base):
    """
    Protective hold that strictly blocks destructive lifecycle operations for covered assets.
    """
    __tablename__ = "legal_holds"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    organization_id = Column(String(36), nullable=False, index=True)
    workspace_id = Column(String(36), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String(32), nullable=False, default="active", index=True)  # active, released

    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now, server_default=func.now())
    released_at = Column(DateTime(timezone=True), nullable=True)

    assets = relationship("LegalHoldAsset", back_populates="legal_hold", cascade="all, delete-orphan")


class LegalHoldAsset(Base):
    """
    Association between a LegalHold and a DataAsset.
    """
    __tablename__ = "legal_hold_assets"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    legal_hold_id = Column(String(36), ForeignKey("legal_holds.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_id = Column(String(36), ForeignKey("data_assets.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now, server_default=func.now())

    legal_hold = relationship("LegalHold", back_populates="assets")


class ComplianceEvidence(Base):
    """
    Tamper-evident, hash-chained record of governance decisions and compliance events.
    """
    __tablename__ = "compliance_evidence"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    organization_id = Column(String(36), nullable=False, index=True)
    workspace_id = Column(String(36), nullable=True, index=True)

    evidence_type = Column(String(50), nullable=False, index=True)
    subject_type = Column(String(50), nullable=False)
    subject_id = Column(String(255), nullable=False, index=True)
    action = Column(String(50), nullable=False)
    result = Column(String(50), nullable=False)

    policy_version_id = Column(String(36), nullable=True)
    governance_decision_id = Column(String(36), nullable=True, index=True)
    actor_type = Column(String(50), nullable=False)
    actor_id = Column(String(36), nullable=True)

    timestamp = Column(DateTime(timezone=True), nullable=False, default=_utc_now, server_default=func.now(), index=True)
    evidence_hash = Column(String(64), nullable=False, unique=True, index=True)
    previous_evidence_hash = Column(String(64), nullable=True)
    evidence_metadata = Column("metadata", JSON, nullable=True)


class DataAccessRecord(Base):
    """
    Audited high-level application data access event.
    """
    __tablename__ = "data_access_records"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    organization_id = Column(String(36), nullable=False, index=True)
    workspace_id = Column(String(36), nullable=True, index=True)
    asset_id = Column(String(36), nullable=False, index=True)

    actor_type = Column(String(50), nullable=False)
    actor_id = Column(String(36), nullable=False, index=True)
    action = Column(String(50), nullable=False)  # read, create, update, delete, export, share, execute
    result = Column(String(50), nullable=False)  # allowed, denied, approval_required

    timestamp = Column(DateTime(timezone=True), nullable=False, default=_utc_now, server_default=func.now(), index=True)
    request_id = Column(String(64), nullable=True)
    correlation_id = Column(String(64), nullable=True)
