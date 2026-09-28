import uuid
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from backend.app.db.models.enums import TaskStatus
from backend.app.db.models.guid import GUID

if TYPE_CHECKING:
    from backend.app.db.models.project import Project
    from backend.app.db.models.run import Run
    from backend.app.db.models.context import TaskContext


class Task(Base):
    """
    Task entity representing an executable unit of work with instructions, context, status, and run history.
    """
    __tablename__ = "tasks"

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
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    context_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=TaskStatus.DRAFT.value,
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
        back_populates="tasks",
    )
    runs: Mapped[List["Run"]] = relationship(
        "Run",
        back_populates="task",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="desc(Run.created_at)",
    )
    contexts: Mapped[List["TaskContext"]] = relationship(
        "TaskContext",
        back_populates="task",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="desc(TaskContext.priority), desc(TaskContext.created_at)",
    )

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}', project_id={self.project_id})>"
