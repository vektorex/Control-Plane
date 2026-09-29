"""Workflow System schema

Revision ID: 013_workflow_system
Revises: 012_observability_usage_and_cost_intelligence
Create Date: 2026-09-30 00:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from backend.app.db.models.guid import GUID

# revision identifiers, used by Alembic.
revision: str = "013_workflow_system"
down_revision: Union[str, None] = "012_observability_usage_and_cost_intelligence"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create workflows table
    op.create_table(
        "workflows",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("project_id", GUID(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="draft"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("input_schema", sa.JSON(), nullable=False),
        sa.Column("output_schema", sa.JSON(), nullable=True),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("created_by", GUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_workflows_id", "workflows", ["id"], unique=False)
    op.create_index("ix_workflows_workspace_id", "workflows", ["workspace_id"], unique=False)
    op.create_index("ix_workflows_project_id", "workflows", ["project_id"], unique=False)
    op.create_index("ix_workflows_slug", "workflows", ["slug"], unique=False)
    op.create_index("ix_workflows_status", "workflows", ["status"], unique=False)
    op.create_index("ix_workflows_created_at", "workflows", ["created_at"], unique=False)
    op.create_index("ix_workflows_ws_slug", "workflows", ["workspace_id", "slug"], unique=True)
    op.create_index("ix_workflows_ws_status", "workflows", ["workspace_id", "status"], unique=False)

    # 2. Create workflow_steps table
    op.create_table(
        "workflow_steps",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("workflow_id", GUID(), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("step_type", sa.String(length=50), nullable=False),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflows.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_workflow_steps_id", "workflow_steps", ["id"], unique=False)
    op.create_index("ix_workflow_steps_workflow_id", "workflow_steps", ["workflow_id"], unique=False)
    op.create_index("ix_workflow_steps_step_type", "workflow_steps", ["step_type"], unique=False)
    op.create_index("ix_workflow_steps_order", "workflow_steps", ["workflow_id", "step_order"], unique=False)

    # 3. Create workflow_versions table
    op.create_table(
        "workflow_versions",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("workflow_id", GUID(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("definition", sa.JSON(), nullable=False),
        sa.Column("created_by", GUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflows.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_workflow_versions_id", "workflow_versions", ["id"], unique=False)
    op.create_index("ix_workflow_versions_workflow_id", "workflow_versions", ["workflow_id"], unique=False)
    op.create_index("ix_workflow_versions_version", "workflow_versions", ["version"], unique=False)
    op.create_index("ix_workflow_versions_created_at", "workflow_versions", ["created_at"], unique=False)
    op.create_index("ix_workflow_versions_wf_v", "workflow_versions", ["workflow_id", "version"], unique=True)

    # 4. Create workflow_runs table
    op.create_table(
        "workflow_runs",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("workflow_id", GUID(), nullable=False),
        sa.Column("workflow_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("project_id", GUID(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("input_data", sa.JSON(), nullable=False),
        sa.Column("output_data", sa.JSON(), nullable=True),
        sa.Column("execution_state", sa.JSON(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflows.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_workflow_runs_id", "workflow_runs", ["id"], unique=False)
    op.create_index("ix_workflow_runs_workflow_id", "workflow_runs", ["workflow_id"], unique=False)
    op.create_index("ix_workflow_runs_workspace_id", "workflow_runs", ["workspace_id"], unique=False)
    op.create_index("ix_workflow_runs_project_id", "workflow_runs", ["project_id"], unique=False)
    op.create_index("ix_workflow_runs_status", "workflow_runs", ["status"], unique=False)
    op.create_index("ix_workflow_runs_created_at", "workflow_runs", ["created_at"], unique=False)
    op.create_index("ix_workflow_runs_ws_wf", "workflow_runs", ["workspace_id", "workflow_id"], unique=False)
    op.create_index("ix_workflow_runs_ws_status", "workflow_runs", ["workspace_id", "status"], unique=False)


def downgrade() -> None:
    op.drop_table("workflow_runs")
    op.drop_table("workflow_versions")
    op.drop_table("workflow_steps")
    op.drop_table("workflows")
