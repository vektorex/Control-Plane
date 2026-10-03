"""
SQLAlchemy ORM models for Step 34: AI Security Operations, Threat Detection & Incident Response Layer.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

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
)
from sqlalchemy.orm import relationship as orm_relationship

from backend.app.db.database import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid_str() -> str:
    return str(uuid.uuid4())


class SecuritySignal(Base):
    """
    Normalized security detection signal emitted by deterministic detectors.
    Never stores raw secrets or unredacted passwords/tokens.
    """
    __tablename__ = "security_signals"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    organization_id = Column(String(36), nullable=False, index=True)
    workspace_id = Column(String(36), nullable=True, index=True)
    project_id = Column(String(36), nullable=True, index=True)

    signal_type = Column(String(100), nullable=False, index=True)
    source_type = Column(String(100), nullable=False, index=True)
    source_id = Column(String(255), nullable=True)

    actor_type = Column(String(50), nullable=True)
    actor_id = Column(String(255), nullable=True, index=True)

    resource_type = Column(String(100), nullable=True, index=True)
    resource_id = Column(String(255), nullable=True, index=True)

    severity = Column(String(32), nullable=False, default="low", index=True)
    confidence = Column(Float, nullable=False, default=1.0)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=_utc_now, index=True)

    request_id = Column(String(255), nullable=True, index=True)
    correlation_id = Column(String(255), nullable=True, index=True)
    causation_id = Column(String(255), nullable=True, index=True)

    metadata_payload = Column("metadata", JSON, nullable=False, default=dict)
    status = Column(String(50), nullable=False, default="new", index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)

    # Relationships
    incident_associations = orm_relationship(
        "IncidentSignal",
        back_populates="signal",
        cascade="all, delete-orphan",
    )


class SecurityIncident(Base):
    """
    Correlated security incident aggregating multiple security signals across a tenant.
    """
    __tablename__ = "security_incidents"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    organization_id = Column(String(36), nullable=False, index=True)
    workspace_id = Column(String(36), nullable=True, index=True)
    project_id = Column(String(36), nullable=True, index=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False, default="unknown", index=True)
    severity = Column(String(32), nullable=False, default="medium", index=True)
    status = Column(String(50), nullable=False, default="open", index=True)

    detected_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    first_seen_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    last_seen_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)

    assigned_to = Column(String(255), nullable=True)
    resolved_by = Column(String(255), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_summary = Column(Text, nullable=True)

    metadata_payload = Column("metadata", JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now, onupdate=_utc_now)

    # Relationships
    signals = orm_relationship(
        "IncidentSignal",
        back_populates="incident",
        cascade="all, delete-orphan",
    )
    timeline_events = orm_relationship(
        "IncidentTimelineEvent",
        back_populates="incident",
        cascade="all, delete-orphan",
        order_by="asc(IncidentTimelineEvent.timestamp)",
    )
    containment_actions = orm_relationship(
        "ContainmentAction",
        back_populates="incident",
        cascade="all, delete-orphan",
        order_by="desc(ContainmentAction.requested_at)",
    )


class IncidentSignal(Base):
    """
    Join model linking a SecurityIncident to a SecuritySignal with an explicit relationship type.
    """
    __tablename__ = "incident_signals"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    incident_id = Column(String(36), ForeignKey("security_incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    signal_id = Column(String(36), ForeignKey("security_signals.id", ondelete="CASCADE"), nullable=False, index=True)
    relationship = Column(String(50), nullable=False, default="related")  # trigger, supporting, related, duplicate, follow_up
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)

    # Relationships
    incident = orm_relationship("SecurityIncident", back_populates="signals")
    signal = orm_relationship("SecuritySignal", back_populates="incident_associations")


class IncidentTimelineEvent(Base):
    """
    Append-only timeline audit record for an incident.
    Never stores raw passwords or secrets in summaries.
    """
    __tablename__ = "incident_timeline_events"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    incident_id = Column(String(36), ForeignKey("security_incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=_utc_now, index=True)

    event_type = Column(String(100), nullable=False, index=True)
    source_type = Column(String(100), nullable=False)
    source_id = Column(String(255), nullable=True)

    actor_type = Column(String(50), nullable=True)
    actor_id = Column(String(255), nullable=True)

    summary = Column(Text, nullable=False)
    metadata_payload = Column("metadata", JSON, nullable=False, default=dict)

    # Relationships
    incident = orm_relationship("SecurityIncident", back_populates="timeline_events")


class SecurityIndicator(Base):
    """
    Security indicator (fingerprint/hash) for suspicious requests, actors, webhooks, or artifacts.
    Never stores plaintext secrets.
    """
    __tablename__ = "security_indicators"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    organization_id = Column(String(36), nullable=False, index=True)
    indicator_type = Column(String(100), nullable=False, index=True)
    value_hash = Column(String(64), nullable=False, index=True)  # SHA-256
    value_display = Column(String(255), nullable=False)
    source = Column(String(100), nullable=False)
    confidence = Column(Float, nullable=False, default=1.0)

    first_seen_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    last_seen_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    status = Column(String(50), nullable=False, default="active", index=True)
    metadata_payload = Column("metadata", JSON, nullable=False, default=dict)


class SecurityPlaybook(Base):
    """
    Automated or semi-automated response playbook with actions drawn strictly from a fixed allowlist.
    """
    __tablename__ = "security_playbooks"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    organization_id = Column(String(36), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    trigger_conditions = Column(JSON, nullable=False, default=dict)
    actions = Column(JSON, nullable=False, default=list)
    enabled = Column(Boolean, nullable=False, default=True)

    created_by = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now, onupdate=_utc_now)


class ContainmentAction(Base):
    """
    Deterministic containment action taken in response to a security incident.
    Integrates with Step 18 HITL when human approval is required.
    """
    __tablename__ = "containment_actions"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    incident_id = Column(String(36), ForeignKey("security_incidents.id", ondelete="CASCADE"), nullable=False, index=True)

    action_type = Column(String(100), nullable=False, index=True)
    target_type = Column(String(100), nullable=False)
    target_id = Column(String(255), nullable=False)

    status = Column(String(50), nullable=False, default="requested", index=True)
    requested_by = Column(String(255), nullable=False)
    approved_by = Column(String(255), nullable=True)

    requested_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    result = Column(JSON, nullable=False, default=dict)
    reason = Column(Text, nullable=False)

    # Relationships
    incident = orm_relationship("SecurityIncident", back_populates="containment_actions")
