import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from backend.app.db.models.guid import GUID
from backend.app.db.models.vector_type import VectorType

if TYPE_CHECKING:
    from backend.app.db.models.workspace import Workspace
    from backend.app.db.models.user import User
    from backend.app.db.models.project import Project


class Memory(Base):
    """
    A persistent structured knowledge item retained across tasks and workflows,
    explicitly scoped, categorized, and sanitized.
    """
    __tablename__ = "memories"

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
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    scope: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="user",
        index=True,
    )  # 'user', 'workspace', 'project'
    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # 'preference', 'project_context', 'workflow_context', 'technical_fact', 'instruction', 'reference', 'decision'
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
    )
    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="explicit_user",
    )  # 'explicit_user', 'task', 'workflow', 'document', 'connector', 'system'
    source_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    importance: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="medium",
    )  # 'low', 'medium', 'high'
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="active",
        index=True,
    )  # 'active', 'archived', 'expired'
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
        index=True,
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace")
    user: Mapped[Optional["User"]] = relationship("User")
    project: Mapped[Optional["Project"]] = relationship("Project")
    embedding: Mapped[Optional["MemoryEmbedding"]] = relationship(
        "MemoryEmbedding",
        back_populates="memory",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_memories_ws_user", "workspace_id", "user_id"),
        Index("ix_memories_ws_proj", "workspace_id", "project_id"),
        Index("ix_memories_ws_scope_status", "workspace_id", "scope", "status"),
        Index("ix_memories_ws_type_status", "workspace_id", "type", "status"),
    )

    def __repr__(self) -> str:
        return f"<Memory(id={self.id}, type='{self.type}', scope='{self.scope}', status='{self.status}', title='{self.title[:30]}')>"


class MemoryEmbedding(Base):
    """
    Vector representation of a persistent memory for semantic similarity retrieval.
    Reuses existing VectorType (pgvector in Postgres, JSON in SQLite).
    """
    __tablename__ = "memory_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    memory_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("memories.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    embedding: Mapped[Optional[List[float]]] = mapped_column(
        VectorType(dim=1536),
        nullable=True,
    )
    embedding_model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="text-embedding-3-small",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationship
    memory: Mapped["Memory"] = relationship("Memory", back_populates="embedding")

    def __repr__(self) -> str:
        return f"<MemoryEmbedding(id={self.id}, memory_id={self.memory_id}, model='{self.embedding_model}')>"


class MemoryConflict(Base):
    """
    Tracks detected factual or directive contradictions between two persistent memories.
    """
    __tablename__ = "memory_conflicts"

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
    memory_a_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("memories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    memory_b_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("memories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="unresolved",
        index=True,
    )  # 'unresolved', 'resolved', 'dismissed'
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    memory_a: Mapped["Memory"] = relationship("Memory", foreign_keys=[memory_a_id])
    memory_b: Mapped["Memory"] = relationship("Memory", foreign_keys=[memory_b_id])

    __table_args__ = (
        Index("ix_memory_conflicts_ws_status", "workspace_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<MemoryConflict(id={self.id}, a={self.memory_a_id}, b={self.memory_b_id}, status='{self.status}')>"


class MemorySuggestion(Base):
    """
    Candidate memory suggested by AI extractor/task execution that requires explicit user confirmation.
    """
    __tablename__ = "memory_suggestions"

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
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="preference",
    )
    scope: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="user",
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.8)
    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="task",
    )
    source_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    importance: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="medium",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
    )  # 'pending', 'accepted', 'rejected'
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace")
    user: Mapped[Optional["User"]] = relationship("User")
    project: Mapped[Optional["Project"]] = relationship("Project")

    __table_args__ = (
        Index("ix_memory_suggestions_ws_status", "workspace_id", "status"),
        Index("ix_memory_suggestions_ws_user", "workspace_id", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<MemorySuggestion(id={self.id}, title='{self.title[:30]}', status='{self.status}')>"


class UserMemorySettings(Base):
    """
    Per-user, per-workspace configuration for memory persistence and suggestions.
    Security and sanitization filtering cannot be disabled.
    """
    __tablename__ = "user_memory_settings"
    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="uq_user_memory_settings_ws_user"),
        Index("ix_user_memory_settings_ws_user", "workspace_id", "user_id"),
    )

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
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    memory_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    suggestions_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    default_retrieval_mode: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="auto",
    )  # 'auto', 'always', 'never'
    default_scope: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="user",
    )  # 'user', 'project', 'workspace'
    retention_preference: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="never",
    )  # 'never', '7_days', '30_days', '90_days'
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<UserMemorySettings(ws={self.workspace_id}, user={self.user_id}, enabled={self.memory_enabled})>"
