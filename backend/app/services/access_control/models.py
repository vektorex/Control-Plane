"""
SQLAlchemy ORM models for Step 27: Multi-Tenant Organizations, Teams, Roles & Access Control.
"""
import uuid
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from backend.app.db.models.guid import GUID
from backend.app.services.access_control.constants import (
    OrganizationStatus,
    MemberStatus,
    OrganizationRole,
    WorkspaceRole,
    ProjectRole,
)

if TYPE_CHECKING:
    from backend.app.db.models.user import User
    from backend.app.db.models.workspace import Workspace
    from backend.app.db.models.project import Project


class Organization(Base):
    """
    Top-level organizational tenant boundary.
    All workspaces, teams, and billing configurations are scoped to an Organization.
    """
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=OrganizationStatus.ACTIVE.value,
        server_default=OrganizationStatus.ACTIVE.value,
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
        foreign_keys=[owner_user_id],
        lazy="selectin",
    )
    members: Mapped[List["OrganizationMember"]] = relationship(
        "OrganizationMember",
        back_populates="organization",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="asc(OrganizationMember.created_at)",
    )
    invitations: Mapped[List["OrganizationInvitation"]] = relationship(
        "OrganizationInvitation",
        back_populates="organization",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="desc(OrganizationInvitation.created_at)",
    )
    workspaces: Mapped[List["Workspace"]] = relationship(
        "Workspace",
        back_populates="organization",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="desc(Workspace.created_at)",
    )

    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name='{self.name}', slug='{self.slug}', owner_user_id={self.owner_user_id})>"


class OrganizationMember(Base):
    """
    Membership record mapping a User to an Organization with a defined role.
    """
    __tablename__ = "organization_members"
    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_org_member_org_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=OrganizationRole.MEMBER.value,
        server_default=OrganizationRole.MEMBER.value,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=MemberStatus.ACTIVE.value,
        server_default=MemberStatus.ACTIVE.value,
        index=True,
    )
    joined_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="members",
    )
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<OrganizationMember(id={self.id}, org_id={self.organization_id}, user_id={self.user_id}, role='{self.role}')>"


class OrganizationInvitation(Base):
    """
    Invitation record for adding new members to an organization.
    Stores cryptographically hashed tokens, never plaintext.
    """
    __tablename__ = "organization_invitations"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=OrganizationRole.MEMBER.value,
        server_default=OrganizationRole.MEMBER.value,
    )
    token_hash: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    invited_by: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    accepted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="invitations",
    )
    inviter: Mapped["User"] = relationship(
        "User",
        foreign_keys=[invited_by],
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<OrganizationInvitation(id={self.id}, org_id={self.organization_id}, email='{self.email}', role='{self.role}')>"


class WorkspaceMember(Base):
    """
    Membership record mapping a User to a specific Workspace with a workspace role.
    """
    __tablename__ = "workspace_members"
    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="uq_ws_member_ws_user"),
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
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=WorkspaceRole.MEMBER.value,
        server_default=WorkspaceRole.MEMBER.value,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=MemberStatus.ACTIVE.value,
        server_default=MemberStatus.ACTIVE.value,
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
    workspace: Mapped["Workspace"] = relationship(
        "Workspace",
        back_populates="members",
    )
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<WorkspaceMember(id={self.id}, workspace_id={self.workspace_id}, user_id={self.user_id}, role='{self.role}')>"


class ProjectMember(Base):
    """
    Project-level membership record for fine-grained restricted access projects.
    """
    __tablename__ = "project_members"
    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="uq_proj_member_proj_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=ProjectRole.EDITOR.value,
        server_default=ProjectRole.EDITOR.value,
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
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="members",
    )
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<ProjectMember(id={self.id}, project_id={self.project_id}, user_id={self.user_id}, role='{self.role}')>"
