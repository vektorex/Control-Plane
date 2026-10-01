"""AI Execution Replay & Debugging Studio: replay runs

Revision ID: 018_replay_system
Revises: 017_ai_gateway
Create Date: 2026-10-01 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from backend.app.db.models.guid import GUID

# revision identifiers, used by Alembic.
revision: str = "018_replay_system"
down_revision: Union[str, None] = "017_ai_gateway"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "replay_runs",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("original_run_id", GUID(), nullable=False),
        sa.Column("original_workflow_run_id", GUID(), nullable=True),
        sa.Column("replay_mode", sa.String(length=50), nullable=False, server_default="dry_run"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="queued"),
        sa.Column("snapshot_version", sa.String(length=50), nullable=False, server_default="1.0"),
        sa.Column("dry_run", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("replay_output", sa.Text(), nullable=True),
        sa.Column("execution_steps", sa.JSON(), nullable=True),
        sa.Column("comparison_id", GUID(), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_by", GUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["original_run_id"], ["runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["original_workflow_run_id"], ["workflow_runs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_replay_runs_id", "replay_runs", ["id"], unique=False)
    op.create_index("ix_replay_runs_workspace_id", "replay_runs", ["workspace_id"], unique=False)
    op.create_index("ix_replay_runs_original_run_id", "replay_runs", ["original_run_id"], unique=False)
    op.create_index("ix_replay_runs_orig_wf_run_id", "replay_runs", ["original_workflow_run_id"], unique=False)
    op.create_index("ix_replay_runs_status", "replay_runs", ["status"], unique=False)
    op.create_index("ix_replay_runs_mode", "replay_runs", ["replay_mode"], unique=False)
    op.create_index("ix_replay_runs_created_at", "replay_runs", ["created_at"], unique=False)
    op.create_index("ix_replay_runs_ws_status", "replay_runs", ["workspace_id", "status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_replay_runs_ws_status", table_name="replay_runs")
    op.drop_index("ix_replay_runs_created_at", table_name="replay_runs")
    op.drop_index("ix_replay_runs_mode", table_name="replay_runs")
    op.drop_index("ix_replay_runs_status", table_name="replay_runs")
    op.drop_index("ix_replay_runs_orig_wf_run_id", table_name="replay_runs")
    op.drop_index("ix_replay_runs_original_run_id", table_name="replay_runs")
    op.drop_index("ix_replay_runs_workspace_id", table_name="replay_runs")
    op.drop_index("ix_replay_runs_id", table_name="replay_runs")
    op.drop_table("replay_runs")
