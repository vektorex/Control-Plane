"""Model router and intelligence metadata for tasks and runs

Revision ID: 010_model_router_and_intelligence
Revises: 009_llm_planner_and_agent_loop
Create Date: 2026-09-29 00:40:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "010_model_router_and_intelligence"
down_revision: Union[str, None] = "009_llm_planner_and_agent_loop"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.add_column(sa.Column("model_mode", sa.String(length=50), nullable=True, server_default="auto"))
        batch_op.add_column(sa.Column("preferred_model", sa.String(length=100), nullable=True))

    with op.batch_alter_table("runs") as batch_op:
        batch_op.add_column(sa.Column("estimated_cost", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("model_selection_reason", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("model_routing_policy", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("fallback_attempts", sa.Integer(), nullable=True, server_default="0"))


def downgrade() -> None:
    with op.batch_alter_table("runs") as batch_op:
        batch_op.drop_column("fallback_attempts")
        batch_op.drop_column("model_routing_policy")
        batch_op.drop_column("model_selection_reason")
        batch_op.drop_column("estimated_cost")

    with op.batch_alter_table("tasks") as batch_op:
        batch_op.drop_column("preferred_model")
        batch_op.drop_column("model_mode")
