"""Retrieval router decision telemetry metadata for runs

Revision ID: 006_retrieval_router_observability
Revises: 005_documents_chunks_and_retrieval_telemetry
Create Date: 2026-09-28 17:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "006_retrieval_router_observability"
down_revision: Union[str, None] = "005_documents_chunks_and_retrieval_telemetry"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("runs") as batch_op:
        batch_op.add_column(sa.Column("retrieval_mode", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("retrieval_required", sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column("retrieval_strategy", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("retrieval_scope", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("retrieval_top_k", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("retrieval_reason", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("retrieval_confidence", sa.Float(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("runs") as batch_op:
        batch_op.drop_column("retrieval_confidence")
        batch_op.drop_column("retrieval_reason")
        batch_op.drop_column("retrieval_top_k")
        batch_op.drop_column("retrieval_scope")
        batch_op.drop_column("retrieval_strategy")
        batch_op.drop_column("retrieval_required")
        batch_op.drop_column("retrieval_mode")
