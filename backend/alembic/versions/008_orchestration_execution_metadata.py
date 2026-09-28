"""Orchestration execution metadata for runs

Revision ID: 008_orchestration_execution_metadata
Revises: 007_tool_execution_metadata
Create Date: 2026-09-28 23:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "008_orchestration_execution_metadata"
down_revision: Union[str, None] = "007_tool_execution_metadata"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("runs") as batch_op:
        batch_op.add_column(sa.Column("execution_plan", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("execution_steps", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("orchestration_duration_ms", sa.Integer(), nullable=True, server_default="0"))
        batch_op.add_column(sa.Column("retrieval_strategies", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("final_model", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("step_count", sa.Integer(), nullable=True, server_default="0"))
        batch_op.add_column(sa.Column("failed_step", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("runs") as batch_op:
        batch_op.drop_column("failed_step")
        batch_op.drop_column("step_count")
        batch_op.drop_column("final_model")
        batch_op.drop_column("retrieval_strategies")
        batch_op.drop_column("orchestration_duration_ms")
        batch_op.drop_column("execution_steps")
        batch_op.drop_column("execution_plan")
