"""Task execution fields and Run persistence extensions

Revision ID: 003_task_execution_and_run_persistence
Revises: 002_user_and_workspace_ownership
Create Date: 2026-09-27 14:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "003_task_execution_and_run_persistence"
down_revision: Union[str, None] = "002_user_and_workspace_ownership"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add instructions and context_text to tasks
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.add_column(sa.Column("instructions", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("context_text", sa.Text(), nullable=True))

    # 2. Add input_snapshot, output_content, and started_at to runs
    with op.batch_alter_table("runs") as batch_op:
        batch_op.add_column(sa.Column("input_snapshot", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("output_content", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.create_index(op.f("ix_runs_created_at"), ["created_at"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("runs") as batch_op:
        batch_op.drop_index(op.f("ix_runs_created_at"))
        batch_op.drop_column("started_at")
        batch_op.drop_column("output_content")
        batch_op.drop_column("input_snapshot")

    with op.batch_alter_table("tasks") as batch_op:
        batch_op.drop_column("context_text")
        batch_op.drop_column("instructions")
