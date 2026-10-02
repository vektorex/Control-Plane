"""Step 23: Workflow Triggers and Trigger Runs

Revision ID: 020_workflow_triggers
Revises: 019_evaluation_lab
Create Date: 2026-10-01 22:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from backend.app.db.models.guid import GUID

# revision identifiers, used by Alembic.
revision: str = "020_workflow_triggers"
down_revision: Union[str, None] = "019_evaluation_lab"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. workflow_triggers
    op.create_table(
        "workflow_triggers",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("project_id", GUID(), nullable=True),
        sa.Column("workflow_id", GUID(), nullable=False),
        sa.Column("workflow_version", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("trigger_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("filter_configuration", sa.JSON(), nullable=True),
        sa.Column("retry_configuration", sa.JSON(), nullable=False),
        sa.Column("public_trigger_id", sa.String(length=100), nullable=True),
        sa.Column("webhook_secret_hash", sa.String(length=255), nullable=True),
        sa.Column("debounce_seconds", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("created_by", GUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_triggered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflows.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_trigger_id"),
    )
    op.create_index("ix_workflow_triggers_id", "workflow_triggers", ["id"], unique=False)
    op.create_index("ix_workflow_triggers_workspace_id", "workflow_triggers", ["workspace_id"], unique=False)
    op.create_index("ix_workflow_triggers_project_id", "workflow_triggers", ["project_id"], unique=False)
    op.create_index("ix_workflow_triggers_workflow_id", "workflow_triggers", ["workflow_id"], unique=False)
    op.create_index("ix_workflow_triggers_trigger_type", "workflow_triggers", ["trigger_type"], unique=False)
    op.create_index("ix_workflow_triggers_status", "workflow_triggers", ["status"], unique=False)
    op.create_index("ix_workflow_triggers_public_trigger_id", "workflow_triggers", ["public_trigger_id"], unique=True)
    op.create_index("ix_workflow_triggers_created_at", "workflow_triggers", ["created_at"], unique=False)
    op.create_index("ix_workflow_triggers_next_run_at", "workflow_triggers", ["next_run_at"], unique=False)
    op.create_index("ix_workflow_triggers_ws_wf", "workflow_triggers", ["workspace_id", "workflow_id"], unique=False)
    op.create_index("ix_workflow_triggers_ws_status", "workflow_triggers", ["workspace_id", "status"], unique=False)
    op.create_index("ix_workflow_triggers_next_run", "workflow_triggers", ["status", "next_run_at"], unique=False)

    # 2. trigger_runs
    op.create_table(
        "trigger_runs",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("trigger_id", GUID(), nullable=False),
        sa.Column("workflow_run_id", GUID(), nullable=True),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("event_id", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="received"),
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
        sa.Column("input_snapshot", sa.JSON(), nullable=False),
        sa.Column("filter_result", sa.JSON(), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["trigger_id"], ["workflow_triggers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workflow_run_id"], ["workflow_runs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trigger_runs_id", "trigger_runs", ["id"], unique=False)
    op.create_index("ix_trigger_runs_trigger_id", "trigger_runs", ["trigger_id"], unique=False)
    op.create_index("ix_trigger_runs_workflow_run_id", "trigger_runs", ["workflow_run_id"], unique=False)
    op.create_index("ix_trigger_runs_workspace_id", "trigger_runs", ["workspace_id"], unique=False)
    op.create_index("ix_trigger_runs_event_id", "trigger_runs", ["event_id"], unique=False)
    op.create_index("ix_trigger_runs_status", "trigger_runs", ["status"], unique=False)
    op.create_index("ix_trigger_runs_idempotency_key", "trigger_runs", ["idempotency_key"], unique=False)
    op.create_index("ix_trigger_runs_created_at", "trigger_runs", ["created_at"], unique=False)
    op.create_index("ix_trigger_runs_trig_status", "trigger_runs", ["trigger_id", "status"], unique=False)
    op.create_index("ix_trigger_runs_ws_created", "trigger_runs", ["workspace_id", "created_at"], unique=False)
    op.create_index("ix_trigger_runs_idempotency", "trigger_runs", ["trigger_id", "idempotency_key"], unique=False)


def downgrade() -> None:
    op.drop_table("trigger_runs")
    op.drop_table("workflow_triggers")
