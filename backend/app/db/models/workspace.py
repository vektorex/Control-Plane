import uuid
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from backend.app.db.models.guid import GUID

if TYPE_CHECKING:
    from backend.app.db.models.user import User
    from backend.app.db.models.project import Project
    from backend.app.db.models.document import Document
    from backend.app.db.models.workflow import Workflow, WorkflowRun
    from backend.app.services.access_control.models import Organization, WorkspaceMember


class Workspace(Base):
    """
    Workspace entity representing an isolated multi-project organizational boundary owned by a User.
    Extended with Organization tenancy for Step 27.
    """
    __tablename__ = "workspaces"
    __table_args__ = (
        UniqueConstraint("owner_user_id", "slug", name="uq_workspace_owner_slug"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="active",
        server_default="active",
        index=True,
    )
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

    # Relationships
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="workspaces",
    )
    organization: Mapped[Optional["Organization"]] = relationship(
        "Organization",
        back_populates="workspaces",
        foreign_keys=[organization_id],
    )
    members: Mapped[List["WorkspaceMember"]] = relationship(
        "WorkspaceMember",
        back_populates="workspace",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    projects: Mapped[List["Project"]] = relationship(
        "Project",
        back_populates="workspace",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="desc(Project.created_at)",
    )
    documents: Mapped[List["Document"]] = relationship(
        "Document",
        back_populates="workspace",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="desc(Document.created_at)",
    )
    workflows: Mapped[List["Workflow"]] = relationship(
        "Workflow",
        back_populates="workspace",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="desc(Workflow.created_at)",
    )
    workflow_runs: Mapped[List["WorkflowRun"]] = relationship(
        "WorkflowRun",
        back_populates="workspace",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="desc(WorkflowRun.created_at)",
    )

    def __repr__(self) -> str:
        return f"<Workspace(id={self.id}, name='{self.name}', slug='{self.slug}', owner_user_id={self.owner_user_id}, org_id={self.organization_id})>"

