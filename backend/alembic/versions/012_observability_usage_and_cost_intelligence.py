"""Observability, usage, trace events and cost intelligence schema

Revision ID: 012_observability_usage_and_cost_intelligence
Revises: 011_evaluation_and_verification_engine
Create Date: 2026-09-30 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from backend.app.db.models.guid import GUID

# revision identifiers, used by Alembic.
revision: str = "012_observability_usage_and_cost_intelligence"
down_revision: Union[str, None] = "011_evaluation_and_verification_engine"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create run_telemetry table
    op.create_table(
        "run_telemetry",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("run_id", GUID(), nullable=False),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("task_id", GUID(), nullable=False),
        sa.Column("project_id", GUID(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="running"),
        sa.Column("provider", sa.String(length=100), nullable=True),
        sa.Column("planner_model", sa.String(length=100), nullable=True),
        sa.Column("generation_model", sa.String(length=100), nullable=True),
        sa.Column("evaluator_model", sa.String(length=100), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_cost", sa.Float(), nullable=True),
        sa.Column("retrieval_calls", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("retrieval_results", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tool_calls", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tools_used", sa.JSON(), nullable=True),
        sa.Column("execution_steps", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("planner_duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("retrieval_duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tool_duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("generation_duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("evaluation_duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("revision_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("evaluation_status", sa.String(length=50), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message_safe", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id", name="uq_run_telemetry_run_id"),
    )
    op.create_index(op.f("ix_run_telemetry_id"), "run_telemetry", ["id"], unique=False)
    op.create_index(op.f("ix_run_telemetry_run_id"), "run_telemetry", ["run_id"], unique=True)
    op.create_index(op.f("ix_run_telemetry_workspace_id"), "run_telemetry", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_run_telemetry_task_id"), "run_telemetry", ["task_id"], unique=False)
    op.create_index(op.f("ix_run_telemetry_project_id"), "run_telemetry", ["project_id"], unique=False)
    op.create_index(op.f("ix_run_telemetry_status"), "run_telemetry", ["status"], unique=False)
    op.create_index(op.f("ix_run_telemetry_provider"), "run_telemetry", ["provider"], unique=False)
    op.create_index(op.f("ix_run_telemetry_generation_model"), "run_telemetry", ["generation_model"], unique=False)
    op.create_index(op.f("ix_run_telemetry_created_at"), "run_telemetry", ["created_at"], unique=False)
    op.create_index("ix_run_telemetry_workspace_created", "run_telemetry", ["workspace_id", "created_at"], unique=False)
    op.create_index("ix_run_telemetry_workspace_status", "run_telemetry", ["workspace_id", "status"], unique=False)
    op.create_index("ix_run_telemetry_workspace_model", "run_telemetry", ["workspace_id", "generation_model"], unique=False)
    op.create_index("ix_run_telemetry_workspace_provider", "run_telemetry", ["workspace_id", "provider"], unique=False)

    # 2. Create execution_trace_events table
    op.create_table(
        "execution_trace_events",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("run_id", GUID(), nullable=False),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("step_type", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="completed"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column("provider", sa.String(length=100), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_execution_trace_events_id"), "execution_trace_events", ["id"], unique=False)
    op.create_index(op.f("ix_execution_trace_events_run_id"), "execution_trace_events", ["run_id"], unique=False)
    op.create_index(op.f("ix_execution_trace_events_workspace_id"), "execution_trace_events", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_execution_trace_events_event_type"), "execution_trace_events", ["event_type"], unique=False)
    op.create_index(op.f("ix_execution_trace_events_status"), "execution_trace_events", ["status"], unique=False)
    op.create_index(op.f("ix_execution_trace_events_model"), "execution_trace_events", ["model"], unique=False)
    op.create_index(op.f("ix_execution_trace_events_provider"), "execution_trace_events", ["provider"], unique=False)
    op.create_index(op.f("ix_execution_trace_events_created_at"), "execution_trace_events", ["created_at"], unique=False)
    op.create_index("ix_trace_events_run_seq", "execution_trace_events", ["run_id", "sequence_number"], unique=False)
    op.create_index("ix_trace_events_workspace_created", "execution_trace_events", ["workspace_id", "created_at"], unique=False)

    # 3. Create usage_records table
    op.create_table(
        "usage_records",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("run_id", GUID(), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("operation", sa.String(length=50), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cached_input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_cost", sa.Float(), nullable=True),
        sa.Column("usage_source", sa.String(length=50), nullable=False, server_default="provider"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_usage_records_id"), "usage_records", ["id"], unique=False)
    op.create_index(op.f("ix_usage_records_workspace_id"), "usage_records", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_usage_records_run_id"), "usage_records", ["run_id"], unique=False)
    op.create_index(op.f("ix_usage_records_provider"), "usage_records", ["provider"], unique=False)
    op.create_index(op.f("ix_usage_records_model"), "usage_records", ["model"], unique=False)
    op.create_index(op.f("ix_usage_records_operation"), "usage_records", ["operation"], unique=False)
    op.create_index(op.f("ix_usage_records_created_at"), "usage_records", ["created_at"], unique=False)
    op.create_index("ix_usage_records_workspace_created", "usage_records", ["workspace_id", "created_at"], unique=False)
    op.create_index("ix_usage_records_workspace_model", "usage_records", ["workspace_id", "model"], unique=False)
    op.create_index("ix_usage_records_workspace_provider", "usage_records", ["workspace_id", "provider"], unique=False)
    op.create_index("ix_usage_records_run_op", "usage_records", ["run_id", "operation"], unique=False)


def downgrade() -> None:
    op.drop_table("usage_records")
    op.drop_table("execution_trace_events")
    op.drop_table("run_telemetry")
