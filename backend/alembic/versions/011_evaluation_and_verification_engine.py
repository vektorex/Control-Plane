"""Evaluation and verification engine schema and metadata for runs and tasks

Revision ID: 011_evaluation_and_verification_engine
Revises: 010_model_router_and_intelligence
Create Date: 2026-09-29 01:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from backend.app.db.models.guid import GUID

# revision identifiers, used by Alembic.
revision: str = "011_evaluation_and_verification_engine"
down_revision: Union[str, None] = "010_model_router_and_intelligence"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add evaluation metadata columns to tasks
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.add_column(sa.Column("evaluation_mode", sa.String(length=50), nullable=True, server_default="standard"))
        batch_op.add_column(sa.Column("strict_evaluation", sa.Boolean(), nullable=True, server_default="false"))
        batch_op.add_column(sa.Column("expected_format", sa.String(length=50), nullable=True))

    # 2. Add evaluation metadata columns to runs
    with op.batch_alter_table("runs") as batch_op:
        batch_op.add_column(sa.Column("evaluation_status", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("evaluation_mode", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("evaluation_duration_ms", sa.Integer(), nullable=True, server_default="0"))
        batch_op.add_column(sa.Column("evaluation_attempts", sa.Integer(), nullable=True, server_default="0"))
        batch_op.add_column(sa.Column("revision_attempts", sa.Integer(), nullable=True, server_default="0"))
        batch_op.add_column(sa.Column("evaluation_result", sa.JSON(), nullable=True))

    # 3. Create evaluation_runs table
    op.create_table(
        "evaluation_runs",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("run_id", GUID(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="passed"),
        sa.Column("evaluator_type", sa.String(length=100), nullable=False, server_default="engine"),
        sa.Column("recommendation", sa.String(length=50), nullable=False, server_default="accept"),
        sa.Column("mode", sa.String(length=50), nullable=False, server_default="standard"),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("raw_summary", sa.Text(), nullable=True),
        sa.Column("metadata_snapshot", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_evaluation_runs_id"), "evaluation_runs", ["id"], unique=False)
    op.create_index(op.f("ix_evaluation_runs_run_id"), "evaluation_runs", ["run_id"], unique=False)
    op.create_index(op.f("ix_evaluation_runs_status"), "evaluation_runs", ["status"], unique=False)
    op.create_index(op.f("ix_evaluation_runs_created_at"), "evaluation_runs", ["created_at"], unique=False)

    # 4. Create evaluation_findings table
    op.create_table(
        "evaluation_findings",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("evaluation_run_id", GUID(), nullable=False),
        sa.Column("check_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="passed"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("evidence_ids", sa.JSON(), nullable=True),
        sa.Column("metadata_snapshot", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["evaluation_run_id"], ["evaluation_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_evaluation_findings_id"), "evaluation_findings", ["id"], unique=False)
    op.create_index(op.f("ix_evaluation_findings_evaluation_run_id"), "evaluation_findings", ["evaluation_run_id"], unique=False)
    op.create_index(op.f("ix_evaluation_findings_check_type"), "evaluation_findings", ["check_type"], unique=False)
    op.create_index(op.f("ix_evaluation_findings_created_at"), "evaluation_findings", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_evaluation_findings_created_at"), table_name="evaluation_findings")
    op.drop_index(op.f("ix_evaluation_findings_check_type"), table_name="evaluation_findings")
    op.drop_index(op.f("ix_evaluation_findings_evaluation_run_id"), table_name="evaluation_findings")
    op.drop_index(op.f("ix_evaluation_findings_id"), table_name="evaluation_findings")
    op.drop_table("evaluation_findings")

    op.drop_index(op.f("ix_evaluation_runs_created_at"), table_name="evaluation_runs")
    op.drop_index(op.f("ix_evaluation_runs_status"), table_name="evaluation_runs")
    op.drop_index(op.f("ix_evaluation_runs_run_id"), table_name="evaluation_runs")
    op.drop_index(op.f("ix_evaluation_runs_id"), table_name="evaluation_runs")
    op.drop_table("evaluation_runs")

    with op.batch_alter_table("runs") as batch_op:
        batch_op.drop_column("evaluation_result")
        batch_op.drop_column("revision_attempts")
        batch_op.drop_column("evaluation_attempts")
        batch_op.drop_column("evaluation_duration_ms")
        batch_op.drop_column("evaluation_mode")
        batch_op.drop_column("evaluation_status")

    with op.batch_alter_table("tasks") as batch_op:
        batch_op.drop_column("expected_format")
        batch_op.drop_column("strict_evaluation")
        batch_op.drop_column("evaluation_mode")
