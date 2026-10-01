"""AI Gateway: workspace model policies

Revision ID: 017_ai_gateway
Revises: 016_hitl_system
Create Date: 2026-09-30 04:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from backend.app.db.models.guid import GUID

# revision identifiers, used by Alembic.
revision: str = "017_ai_gateway"
down_revision: Union[str, None] = "016_hitl_system"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "workspace_model_policies",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("allowed_providers", sa.JSON(), nullable=False),
        sa.Column("allowed_models", sa.JSON(), nullable=False),
        sa.Column("default_model", sa.String(length=255), nullable=True),
        sa.Column("max_tokens_per_request", sa.Integer(), nullable=True, server_default="4096"),
        sa.Column("max_requests_per_run", sa.Integer(), nullable=True, server_default="50"),
        sa.Column("max_concurrent_requests", sa.Integer(), nullable=True, server_default="10"),
        sa.Column("fallback_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_id", name="uq_workspace_model_policies_workspace_id"),
    )
    op.create_index("ix_ws_model_policies_id", "workspace_model_policies", ["id"], unique=False)
    op.create_index("ix_ws_model_policies_ws", "workspace_model_policies", ["workspace_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_ws_model_policies_ws", table_name="workspace_model_policies")
    op.drop_index("ix_ws_model_policies_id", table_name="workspace_model_policies")
    op.drop_table("workspace_model_policies")
