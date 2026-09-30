"""HITL Human-in-the-Loop system: intervention requests, approval decisions, human actions, workspace policies, notifications

Revision ID: 016_hitl_system
Revises: 015_memory_system
Create Date: 2026-09-30 03:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from backend.app.db.models.guid import GUID

# revision identifiers, used by Alembic.
revision: str = "016_hitl_system"
down_revision: Union[str, None] = "015_memory_system"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create human_intervention_requests table
    op.create_table(
        "human_intervention_requests",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("project_id", GUID(), nullable=True),
        sa.Column("workflow_id", GUID(), nullable=True),
        sa.Column("workflow_run_id", GUID(), nullable=True),
        sa.Column("run_id", GUID(), nullable=True),
        sa.Column("step_id", sa.String(length=100), nullable=True),
        sa.Column("requested_by", GUID(), nullable=True),
        sa.Column("assigned_to", GUID(), nullable=True),
        sa.Column("intervention_type", sa.String(length=50), nullable=False, server_default="approval"),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("priority", sa.String(length=50), nullable=False, server_default="normal"),
        sa.Column("requested_action", sa.String(length=100), nullable=False),
        sa.Column("input_snapshot", sa.JSON(), nullable=False),
        sa.Column("safe_context", sa.JSON(), nullable=False),
        sa.Column("available_actions", sa.JSON(), nullable=False),
        sa.Column("selected_action", sa.String(length=50), nullable=True),
        sa.Column("response_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflows.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["workflow_run_id"], ["workflow_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requested_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assigned_to"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_hitl_id", "human_intervention_requests", ["id"], unique=False)
    op.create_index("ix_hitl_workspace_id", "human_intervention_requests", ["workspace_id"], unique=False)
    op.create_index("ix_hitl_assigned_to", "human_intervention_requests", ["assigned_to"], unique=False)
    op.create_index("ix_hitl_status", "human_intervention_requests", ["status"], unique=False)
    op.create_index("ix_hitl_workflow_run_id", "human_intervention_requests", ["workflow_run_id"], unique=False)
    op.create_index("ix_hitl_created_at", "human_intervention_requests", ["created_at"], unique=False)
    op.create_index("ix_hitl_expires_at", "human_intervention_requests", ["expires_at"], unique=False)
    op.create_index("ix_hitl_ws_status", "human_intervention_requests", ["workspace_id", "status"], unique=False)
    op.create_index("ix_hitl_ws_assigned", "human_intervention_requests", ["workspace_id", "assigned_to", "status"], unique=False)
    op.create_index("ix_hitl_wf_run", "human_intervention_requests", ["workflow_run_id", "status"], unique=False)
    op.create_index("ix_hitl_expires", "human_intervention_requests", ["status", "expires_at"], unique=False)

    # 2. Create approval_decisions table
    op.create_table(
        "approval_decisions",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("intervention_id", GUID(), nullable=False),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("user_id", GUID(), nullable=False),
        sa.Column("decision", sa.String(length=50), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("edited_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["intervention_id"], ["human_intervention_requests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_approval_decisions_id", "approval_decisions", ["id"], unique=False)
    op.create_index("ix_approval_decisions_interv", "approval_decisions", ["intervention_id", "created_at"], unique=False)

    # 3. Create human_actions audit table
    op.create_table(
        "human_actions",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("intervention_id", GUID(), nullable=True),
        sa.Column("user_id", GUID(), nullable=False),
        sa.Column("action_type", sa.String(length=100), nullable=False),
        sa.Column("target_type", sa.String(length=100), nullable=False),
        sa.Column("target_id", sa.String(length=255), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["intervention_id"], ["human_intervention_requests.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_human_actions_id", "human_actions", ["id"], unique=False)
    op.create_index("ix_human_actions_ws_type", "human_actions", ["workspace_id", "action_type", "created_at"], unique=False)

    # 4. Create workspace_approval_policies table
    op.create_table(
        "workspace_approval_policies",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("require_tool_approval", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("require_connector_write_approval", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("require_destructive_approval", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("require_external_action_approval", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("require_evaluation_failure_review", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("max_auto_cost", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_id"),
    )
    op.create_index("ix_ws_approval_policies_id", "workspace_approval_policies", ["id"], unique=False)
    op.create_index("ix_ws_approval_policies_ws", "workspace_approval_policies", ["workspace_id"], unique=True)

    # 5. Create notifications table
    op.create_table(
        "notifications",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("user_id", GUID(), nullable=False),
        sa.Column("type", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("reference_type", sa.String(length=50), nullable=True),
        sa.Column("reference_id", sa.String(length=255), nullable=True),
        sa.Column("read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_id", "notifications", ["id"], unique=False)
    op.create_index("ix_notifications_user_read", "notifications", ["user_id", "read", "created_at"], unique=False)
    op.create_index("ix_notifications_ws_user", "notifications", ["workspace_id", "user_id"], unique=False)


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("workspace_approval_policies")
    op.drop_table("human_actions")
    op.drop_table("approval_decisions")
    op.drop_table("human_intervention_requests")
