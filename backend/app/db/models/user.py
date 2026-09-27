import uuid
from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from backend.app.db.models.guid import GUID

if TYPE_CHECKING:
    from backend.app.db.models.workspace import Workspace


class User(Base):
    """
    User/Profile entity mapped to Supabase Auth identity for tenancy and resource ownership.
    """
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    auth_user_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        index=True,
        nullable=False,
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
    workspaces: Mapped[List["Workspace"]] = relationship(
        "Workspace",
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="desc(Workspace.created_at)",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', auth_user_id='{self.auth_user_id}')>"
