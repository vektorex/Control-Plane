"""TaskContext model and Run context telemetry metadata

Revision ID: 004_task_context_and_run_context_metadata
Revises: 003_task_execution_and_run_persistence
Create Date: 2026-09-28 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from backend.app.db.models.guid import GUID

# revision identifiers, used by Alembic.
revision: str = "004_task_context_and_run_context_metadata"
down_revision: Union[str, None] = "003_task_execution_and_run_persistence"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create task_contexts table
    op.create_table(
        "task_contexts",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("task_id", GUID(), nullable=False),
        sa.Column("source_type", sa.String(length=50), server_default="manual", nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("priority", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_task_contexts_id"), "task_contexts", ["id"], unique=False)
    op.create_index(op.f("ix_task_contexts_task_id"), "task_contexts", ["task_id"], unique=False)
    op.create_index(op.f("ix_task_contexts_source_type"), "task_contexts", ["source_type"], unique=False)
    op.create_index(op.f("ix_task_contexts_created_at"), "task_contexts", ["created_at"], unique=False)

    # 2. Add context telemetry columns to runs table
    with op.batch_alter_table("runs") as batch_op:
        batch_op.add_column(sa.Column("context_item_count", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("estimated_context_tokens", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("context_truncated", sa.Boolean(), server_default=sa.text("0"), nullable=True))
        batch_op.add_column(sa.Column("context_sources", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("runs") as batch_op:
        batch_op.drop_column("context_sources")
        batch_op.drop_column("context_truncated")
        batch_op.drop_column("estimated_context_tokens")
        batch_op.drop_column("context_item_count")

    op.drop_index(op.f("ix_task_contexts_created_at"), table_name="task_contexts")
    op.drop_index(op.f("ix_task_contexts_source_type"), table_name="task_contexts")
    op.drop_index(op.f("ix_task_contexts_task_id"), table_name="task_contexts")
    op.drop_index(op.f("ix_task_contexts_id"), table_name="task_contexts")
    op.drop_table("task_contexts")
