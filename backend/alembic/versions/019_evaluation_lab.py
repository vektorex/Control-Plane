"""AI Evaluation Lab: datasets, versions, cases, experiments, experiment runs

Revision ID: 019_evaluation_lab
Revises: 018_replay_system
Create Date: 2026-10-01 18:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from backend.app.db.models.guid import GUID

# revision identifiers, used by Alembic.
revision: str = "019_evaluation_lab"
down_revision: Union[str, None] = "018_replay_system"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. evaluation_datasets
    op.create_table(
        "evaluation_datasets",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("project_id", GUID(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="draft"),
        sa.Column("created_by", GUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_eval_datasets_id", "evaluation_datasets", ["id"], unique=False)
    op.create_index("ix_eval_datasets_workspace_id", "evaluation_datasets", ["workspace_id"], unique=False)
    op.create_index("ix_eval_datasets_project_id", "evaluation_datasets", ["project_id"], unique=False)
    op.create_index("ix_eval_datasets_status", "evaluation_datasets", ["status"], unique=False)
    op.create_index("ix_eval_datasets_created_at", "evaluation_datasets", ["created_at"], unique=False)

    # 2. evaluation_dataset_versions
    op.create_table(
        "evaluation_dataset_versions",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("dataset_id", GUID(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_by", GUID(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["dataset_id"], ["evaluation_datasets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dataset_id", "version", name="uq_dataset_id_version"),
    )
    op.create_index("ix_eval_dataset_versions_id", "evaluation_dataset_versions", ["id"], unique=False)
    op.create_index("ix_eval_dataset_versions_dataset_id", "evaluation_dataset_versions", ["dataset_id"], unique=False)
    op.create_index("ix_eval_dataset_versions_created_at", "evaluation_dataset_versions", ["created_at"], unique=False)

    # 3. evaluation_cases
    op.create_table(
        "evaluation_cases",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("dataset_version_id", GUID(), nullable=False),
        sa.Column("case_key", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("input_data", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("expected_output", sa.Text(), nullable=True),
        sa.Column("expected_context", sa.JSON(), nullable=True),
        sa.Column("expected_sources", sa.JSON(), nullable=True),
        sa.Column("assertions", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["dataset_version_id"], ["evaluation_dataset_versions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dataset_version_id", "case_key", name="uq_version_case_key"),
    )
    op.create_index("ix_eval_cases_id", "evaluation_cases", ["id"], unique=False)
    op.create_index("ix_eval_cases_version_id", "evaluation_cases", ["dataset_version_id"], unique=False)
    op.create_index("ix_eval_cases_case_key", "evaluation_cases", ["case_key"], unique=False)
    op.create_index("ix_eval_cases_created_at", "evaluation_cases", ["created_at"], unique=False)

    # 4. evaluation_experiments
    op.create_table(
        "evaluation_experiments",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("project_id", GUID(), nullable=True),
        sa.Column("dataset_version_id", GUID(), nullable=False),
        sa.Column("target_type", sa.String(length=50), nullable=False),
        sa.Column("target_configuration", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="draft"),
        sa.Column("created_by", GUID(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["dataset_version_id"], ["evaluation_dataset_versions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_eval_experiments_id", "evaluation_experiments", ["id"], unique=False)
    op.create_index("ix_eval_experiments_workspace_id", "evaluation_experiments", ["workspace_id"], unique=False)
    op.create_index("ix_eval_experiments_dataset_version_id", "evaluation_experiments", ["dataset_version_id"], unique=False)
    op.create_index("ix_eval_experiments_status", "evaluation_experiments", ["status"], unique=False)
    op.create_index("ix_eval_experiments_created_at", "evaluation_experiments", ["created_at"], unique=False)

    # 5. evaluation_experiment_runs
    op.create_table(
        "evaluation_experiment_runs",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("experiment_id", GUID(), nullable=False),
        sa.Column("case_id", GUID(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="queued"),
        sa.Column("input_snapshot", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("output_snapshot", sa.JSON(), nullable=True),
        sa.Column("evaluation_result", sa.JSON(), nullable=True),
        sa.Column("run_id", GUID(), nullable=True),
        sa.Column("workflow_run_id", GUID(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("estimated_cost", sa.Float(), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["experiment_id"], ["evaluation_experiments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["case_id"], ["evaluation_cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["workflow_run_id"], ["workflow_runs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_eval_exp_runs_id", "evaluation_experiment_runs", ["id"], unique=False)
    op.create_index("ix_eval_exp_runs_experiment_id", "evaluation_experiment_runs", ["experiment_id"], unique=False)
    op.create_index("ix_eval_exp_runs_case_id", "evaluation_experiment_runs", ["case_id"], unique=False)
    op.create_index("ix_eval_exp_runs_status", "evaluation_experiment_runs", ["status"], unique=False)
    op.create_index("ix_eval_exp_runs_created_at", "evaluation_experiment_runs", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_table("evaluation_experiment_runs")
    op.drop_table("evaluation_experiments")
    op.drop_table("evaluation_cases")
    op.drop_table("evaluation_dataset_versions")
    op.drop_table("evaluation_datasets")
