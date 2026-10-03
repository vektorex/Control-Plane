"""
SQLAlchemy Models for Step 37: Public API, Developer Platform & SDK Layer.
"""
from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    BigInteger,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from backend.app.db.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DeveloperApplication(Base):
    """
    Developer application representing an external client or integration.
    Belongs strictly to one organization.
    """
    __tablename__ = "developer_applications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="active", index=True)  # active, suspended, revoked
    environment = Column(String(50), nullable=False, default="development", index=True)  # development, staging, production
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    # Relationships
    credentials = relationship("APICredential", back_populates="application", cascade="all, delete-orphan")
    quotas = relationship("APIQuota", back_populates="application", cascade="all, delete-orphan")
    webhooks = relationship("WebhookSubscription", back_populates="application", cascade="all, delete-orphan")
    approvals = relationship("ApplicationApproval", back_populates="application", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_developer_applications_org_env", "organization_id", "environment"),
    )


class APICredential(Base):
    """
    Scoped API key / signed credential belonging to a DeveloperApplication.
    Plaintext key is NEVER stored; only key_prefix and key_hash are stored.
    """
    __tablename__ = "api_credentials"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id = Column(String(36), ForeignKey("developer_applications.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    key_prefix = Column(String(32), nullable=False, index=True)  # e.g., awl_dev_xxxx
    key_hash = Column(String(128), nullable=False, unique=True, index=True)  # SHA-256 hash of secret
    credential_type = Column(String(50), nullable=False, default="api_key")  # api_key, signed_key
    environment = Column(String(50), nullable=False, default="development", index=True)
    status = Column(String(50), nullable=False, default="active", index=True)  # active, rotated, revoked, expired
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True, index=True)
    last_used_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    created_by = Column(String(36), nullable=True)

    # Relationships
    application = relationship("DeveloperApplication", back_populates="credentials")
    scopes = relationship("APIScopeAssignment", back_populates="credential", cascade="all, delete-orphan")
    resource_scopes = relationship("APIResourceScope", back_populates="credential", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_api_credentials_app_status", "application_id", "status"),
    )


class APIScopeAssignment(Base):
    """
    Assigned permission scope for an API credential (e.g., tasks:run, workflows:read).
    """
    __tablename__ = "api_scope_assignments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    credential_id = Column(String(36), ForeignKey("api_credentials.id", ondelete="CASCADE"), nullable=False, index=True)
    scope = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    credential = relationship("APICredential", back_populates="scopes")

    __table_args__ = (
        Index("ix_api_scope_assignments_cred_scope", "credential_id", "scope", unique=True),
    )


class APIResourceScope(Base):
    """
    Boundary constraining an API credential to a specific workspace or project.
    """
    __tablename__ = "api_resource_scopes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    credential_id = Column(String(36), ForeignKey("api_credentials.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_scope_type = Column(String(50), nullable=False, default="organization")  # organization, workspace, project
    workspace_id = Column(String(36), nullable=True, index=True)
    project_id = Column(String(36), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    credential = relationship("APICredential", back_populates="resource_scopes")


class APIQuota(Base):
    """
    Volumetric quotas per application (requests, task_runs, tokens, etc.).
    """
    __tablename__ = "api_quotas"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id = Column(String(36), ForeignKey("developer_applications.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False)  # requests, task_runs, workflow_runs, tokens, artifact_bytes, execution_seconds
    limit = Column(BigInteger, nullable=False)
    period = Column(String(50), nullable=False, default="minute")  # minute, hour, day, month
    enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    application = relationship("DeveloperApplication", back_populates="quotas")

    __table_args__ = (
        Index("ix_api_quotas_app_resource", "application_id", "resource_type", unique=True),
    )


class APIIdempotencyRecord(Base):
    """
    Prevents duplicate executions for public mutation requests via Idempotency-Key.
    """
    __tablename__ = "api_idempotency_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), nullable=False, index=True)
    application_id = Column(String(36), nullable=False, index=True)
    credential_id = Column(String(36), nullable=False, index=True)
    endpoint = Column(String(255), nullable=False)
    idempotency_key = Column(String(255), nullable=False, index=True)
    request_fingerprint = Column(String(128), nullable=False)
    response_reference = Column(Text, nullable=True)  # JSON-encoded response body
    status_code = Column(Integer, nullable=False, default=200)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)

    __table_args__ = (
        Index("ix_idempotency_app_key", "application_id", "idempotency_key", unique=True),
    )


class APIUsageRecord(Base):
    """
    Aggregated usage and latency telemetry for API requests.
    Never stores API keys, Authorization headers, or plaintext credentials.
    """
    __tablename__ = "api_usage_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), nullable=False, index=True)
    application_id = Column(String(36), nullable=False, index=True)
    credential_id = Column(String(36), nullable=False, index=True)
    endpoint = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer, nullable=False)
    request_bytes = Column(Integer, default=0, nullable=False)
    response_bytes = Column(Integer, default=0, nullable=False)
    latency_ms = Column(Float, default=0.0, nullable=False)
    tokens = Column(Integer, nullable=True)
    cost = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=_utcnow, nullable=False, index=True)
    request_id = Column(String(64), nullable=False, index=True)
    run_id = Column(String(36), nullable=True)

    __table_args__ = (
        Index("ix_api_usage_org_timestamp", "organization_id", "timestamp"),
        Index("ix_api_usage_app_timestamp", "application_id", "timestamp"),
    )


class WebhookSubscription(Base):
    """
    Developer webhook endpoint subscription for asynchronous event notifications.
    """
    __tablename__ = "webhook_subscriptions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id = Column(String(36), ForeignKey("developer_applications.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(String(36), nullable=False, index=True)
    url = Column(String(1024), nullable=False)
    status = Column(String(50), nullable=False, default="active", index=True)  # active, suspended, failed
    events = Column(JSON, nullable=False, default=list)  # list of subscribed event names
    secret_hash = Column(String(128), nullable=False)  # SHA-256 hash of webhook signing secret
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)
    last_delivery_at = Column(DateTime, nullable=True)
    failure_count = Column(Integer, default=0, nullable=False)

    application = relationship("DeveloperApplication", back_populates="webhooks")

    __table_args__ = (
        Index("ix_webhook_subs_app_status", "application_id", "status"),
    )


class ApplicationApproval(Base):
    """
    Human-in-the-loop approval record for elevated or production developer applications.
    """
    __tablename__ = "application_approvals"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id = Column(String(36), ForeignKey("developer_applications.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(String(36), nullable=False, index=True)
    requested_environment = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default="pending", index=True)  # pending, approved, rejected, revoked
    requested_by = Column(String(36), nullable=False)
    reviewed_by = Column(String(36), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    application = relationship("DeveloperApplication", back_populates="approvals")


class APIEnvironmentConfig(Base):
    """
    Organization-level environment controls (approval requirements, default rate limits).
    """
    __tablename__ = "api_environment_configs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), nullable=False, index=True)
    environment = Column(String(50), nullable=False)  # development, staging, production
    require_approval = Column(Boolean, default=False, nullable=False)
    default_rate_limit_rpm = Column(Integer, default=120, nullable=False)
    default_rate_limit_rph = Column(Integer, default=5000, nullable=False)
    max_payload_bytes = Column(Integer, default=10485760, nullable=False)  # 10MB
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    __table_args__ = (
        Index("ix_env_configs_org_env", "organization_id", "environment", unique=True),
    )
