"""LLM planner and agent loop metadata for runs

Revision ID: 009_llm_planner_and_agent_loop
Revises: 008_orchestration_execution_metadata
Create Date: 2026-09-29 00:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "009_llm_planner_and_agent_loop"
down_revision: Union[str, None] = "008_orchestration_execution_metadata"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("runs") as batch_op:
        batch_op.add_column(sa.Column("planner_mode", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("planner_model", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("repair_count", sa.Integer(), nullable=True, server_default="0"))
        batch_op.add_column(sa.Column("iteration_count", sa.Integer(), nullable=True, server_default="1"))
        batch_op.add_column(sa.Column("completion_evaluation", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("runs") as batch_op:
        batch_op.drop_column("completion_evaluation")
        batch_op.drop_column("iteration_count")
        batch_op.drop_column("repair_count")
        batch_op.drop_column("planner_model")
        batch_op.drop_column("planner_mode")
