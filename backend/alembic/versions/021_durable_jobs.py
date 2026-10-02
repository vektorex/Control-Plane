"""Step 24: Durable Background Job System

Revision ID: 021_durable_jobs
Revises: 020_workflow_triggers
Create Date: 2026-10-02 23:20:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from backend.app.db.models.guid import GUID

# revision identifiers, used by Alembic.
revision: str = "021_durable_jobs"
down_revision: Union[str, None] = "020_workflow_triggers"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. jobs
    op.create_table(
        "jobs",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("project_id", GUID(), nullable=True),
        sa.Column("job_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="queued"),
        sa.Column("priority", sa.String(length=20), nullable=False, server_default="normal"),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("available_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("lease_owner", sa.String(length=100), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
        sa.Column("parent_job_id", GUID(), nullable=True),
        sa.Column("progress", sa.JSON(), nullable=False),
        sa.Column("created_by", GUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["parent_job_id"], ["jobs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_jobs_id", "jobs", ["id"], unique=False)
    op.create_index("ix_jobs_workspace_id", "jobs", ["workspace_id"], unique=False)
    op.create_index("ix_jobs_project_id", "jobs", ["project_id"], unique=False)
    op.create_index("ix_jobs_job_type", "jobs", ["job_type"], unique=False)
    op.create_index("ix_jobs_status", "jobs", ["status"], unique=False)
    op.create_index("ix_jobs_priority", "jobs", ["priority"], unique=False)
    op.create_index("ix_jobs_available_at", "jobs", ["available_at"], unique=False)
    op.create_index("ix_jobs_lease_owner", "jobs", ["lease_owner"], unique=False)
    op.create_index("ix_jobs_lease_expires_at", "jobs", ["lease_expires_at"], unique=False)
    op.create_index("ix_jobs_idempotency_key", "jobs", ["idempotency_key"], unique=False)
    op.create_index("ix_jobs_parent_job_id", "jobs", ["parent_job_id"], unique=False)
    op.create_index("ix_jobs_created_at", "jobs", ["created_at"], unique=False)
    op.create_index("ix_jobs_ws_status", "jobs", ["workspace_id", "status"], unique=False)
    op.create_index("ix_jobs_claim", "jobs", ["status", "available_at", "priority"], unique=False)
    op.create_index("ix_jobs_lease_recovery", "jobs", ["status", "lease_expires_at"], unique=False)
    op.create_index("ix_jobs_ws_idemp", "jobs", ["workspace_id", "idempotency_key"], unique=False)
    op.create_index("ix_jobs_created", "jobs", ["workspace_id", "created_at"], unique=False)

    # 2. job_events
    op.create_table(
        "job_events",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("job_id", GUID(), nullable=False),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_events_id", "job_events", ["id"], unique=False)
    op.create_index("ix_job_events_job_id", "job_events", ["job_id"], unique=False)
    op.create_index("ix_job_events_workspace_id", "job_events", ["workspace_id"], unique=False)
    op.create_index("ix_job_events_event_type", "job_events", ["event_type"], unique=False)
    op.create_index("ix_job_events_created_at", "job_events", ["created_at"], unique=False)
    op.create_index("ix_job_events_job_created", "job_events", ["job_id", "created_at"], unique=False)
    op.create_index("ix_job_events_ws_type", "job_events", ["workspace_id", "event_type"], unique=False)

    # 3. Add job_id reference to trigger_runs
    op.add_column("trigger_runs", sa.Column("job_id", GUID(), nullable=True))
    op.create_index("ix_trigger_runs_job_id", "trigger_runs", ["job_id"], unique=False)
    op.create_foreign_key(
        "fk_trigger_runs_job_id",
        "trigger_runs",
        "jobs",
        ["job_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_trigger_runs_job_id", "trigger_runs", type_="foreignkey")
    op.drop_index("ix_trigger_runs_job_id", "trigger_runs")
    op.drop_column("trigger_runs", "job_id")
    op.drop_table("job_events")
    op.drop_table("jobs")
