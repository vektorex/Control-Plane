"""
SQLAlchemy Model for Step 31: Production-Grade Semantic Cache and Intelligent Reuse Layer.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base
from backend.app.db.models.guid import GUID
from backend.app.db.models.vector_type import VectorType
from backend.app.services.cache.constants import CacheNamespace, CacheStatus


class CacheEntry(Base):
    """
    Persisted cache record storing exact and semantic AI execution responses.
    Multi-tenant scoped with strict namespace isolation and cryptographic integrity hashes.
    """
    __tablename__ = "cache_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        nullable=False,
        index=True,
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        nullable=False,
        index=True,
    )
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        nullable=True,
        index=True,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        nullable=True,
        index=True,
    )
    namespace: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default=CacheNamespace.WORKSPACE.value,
        index=True,
    )
    cache_key: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )
    semantic_embedding: Mapped[Optional[List[float]]] = mapped_column(
        VectorType(1536),
        nullable=True,
    )
    normalized_request: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    request_fingerprint: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    response_content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    response_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    source_snapshot: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    prompt_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        nullable=True,
        index=True,
    )
    prompt_version_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        nullable=True,
        index=True,
    )
    model_id: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        index=True,
    )
    model_provider: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
    )
    execution_config_hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )
    context_hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )
    artifact_hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )
    graph_snapshot_hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )
    memory_snapshot_hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=CacheStatus.ACTIVE.value,
        index=True,
    )
    invalidation_reason: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    invalidated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    last_hit_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    hit_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    __table_args__ = (
        Index("ix_cache_entries_tenant", "organization_id", "workspace_id", "status"),
        Index("ix_cache_entries_lookup", "workspace_id", "namespace", "cache_key", "status"),
        Index("ix_cache_entries_expires", "status", "expires_at"),
        Index("ix_cache_entries_prompt_ver", "prompt_version_id", "status"),
        Index("ix_cache_entries_artifact", "artifact_hash", "status"),
    )
