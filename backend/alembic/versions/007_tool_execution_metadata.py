"""Tool execution metadata for runs

Revision ID: 007_tool_execution_metadata
Revises: 006_retrieval_router_observability
Create Date: 2026-09-28 18:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "007_tool_execution_metadata"
down_revision: Union[str, None] = "006_retrieval_router_observability"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("runs") as batch_op:
        batch_op.add_column(sa.Column("tools_used", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("tool_call_count", sa.Integer(), nullable=True, server_default="0"))
        batch_op.add_column(sa.Column("tool_latency_ms", sa.Integer(), nullable=True, server_default="0"))
        batch_op.add_column(sa.Column("tool_errors", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("tool_executions", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("runs") as batch_op:
        batch_op.drop_column("tool_executions")
        batch_op.drop_column("tool_errors")
        batch_op.drop_column("tool_latency_ms")
        batch_op.drop_column("tool_call_count")
        batch_op.drop_column("tools_used")
