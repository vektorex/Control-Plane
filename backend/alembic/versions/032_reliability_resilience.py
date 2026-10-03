"""create reliability, resilience, and chaos tables

Revision ID: 032
Revises: 031
Create Date: 2026-10-03 22:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '032'
down_revision: Union[str, None] = '031'
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None


def upgrade() -> None:
    # 1. reliability_components
    op.create_table(
        'reliability_components',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=True),
        sa.Column('component_type', sa.String(length=50), nullable=False),
        sa.Column('component_name', sa.String(length=255), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('health_status', sa.String(length=50), nullable=False, server_default='healthy'),
        sa.Column('last_heartbeat_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_success_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_failure_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failure_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('success_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('metadata', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_reliability_components_org_id', 'reliability_components', ['organization_id'])
    op.create_index('ix_reliability_components_comp_type', 'reliability_components', ['component_type'])
    op.create_index('ix_reliability_components_comp_name', 'reliability_components', ['component_name'])
    op.create_index('ix_reliability_components_status', 'reliability_components', ['status'])
    op.create_index('ix_reliability_components_health_status', 'reliability_components', ['health_status'])

    # 2. dependency_health
    op.create_table(
        'dependency_health',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('component_id', sa.String(length=36), nullable=False),
        sa.Column('check_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='healthy'),
        sa.Column('latency_ms', sa.Float(), nullable=True),
        sa.Column('error_type', sa.String(length=100), nullable=True),
        sa.Column('checked_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['component_id'], ['reliability_components.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_dependency_health_comp_id', 'dependency_health', ['component_id'])
    op.create_index('ix_dependency_health_check_type', 'dependency_health', ['check_type'])
    op.create_index('ix_dependency_health_status', 'dependency_health', ['status'])
    op.create_index('ix_dependency_health_checked_at', 'dependency_health', ['checked_at'])

    # 3. execution_checkpoints
    op.create_table(
        'execution_checkpoints',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('run_id', sa.String(length=255), nullable=False),
        sa.Column('workflow_run_id', sa.String(length=255), nullable=True),
        sa.Column('job_id', sa.String(length=255), nullable=True),
        sa.Column('step_id', sa.String(length=255), nullable=True),
        sa.Column('sequence_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('checkpoint_type', sa.String(length=50), nullable=False),
        sa.Column('state_snapshot', sa.JSON(), nullable=False),
        sa.Column('input_fingerprint', sa.String(length=64), nullable=False),
        sa.Column('context_fingerprint', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_execution_checkpoints_org_id', 'execution_checkpoints', ['organization_id'])
    op.create_index('ix_execution_checkpoints_ws_id', 'execution_checkpoints', ['workspace_id'])
    op.create_index('ix_execution_checkpoints_proj_id', 'execution_checkpoints', ['project_id'])
    op.create_index('ix_execution_checkpoints_run_id', 'execution_checkpoints', ['run_id'])
    op.create_index('ix_execution_checkpoints_wf_run_id', 'execution_checkpoints', ['workflow_run_id'])
    op.create_index('ix_execution_checkpoints_job_id', 'execution_checkpoints', ['job_id'])
    op.create_index('ix_execution_checkpoints_type', 'execution_checkpoints', ['checkpoint_type'])
    op.create_index('ix_execution_checkpoints_created_at', 'execution_checkpoints', ['created_at'])

    # 4. reliability_objectives
    op.create_table(
        'reliability_objectives',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=True),
        sa.Column('component_type', sa.String(length=50), nullable=False),
        sa.Column('component_name', sa.String(length=255), nullable=False),
        sa.Column('metric', sa.String(length=50), nullable=False),
        sa.Column('target', sa.Float(), nullable=False),
        sa.Column('window', sa.String(length=50), nullable=False, server_default='30d'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_reliability_objectives_org_id', 'reliability_objectives', ['organization_id'])
    op.create_index('ix_reliability_objectives_comp_type', 'reliability_objectives', ['component_type'])
    op.create_index('ix_reliability_objectives_comp_name', 'reliability_objectives', ['component_name'])

    # 5. reliability_budgets
    op.create_table(
        'reliability_budgets',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('component', sa.String(length=255), nullable=False),
        sa.Column('metric', sa.String(length=50), nullable=False),
        sa.Column('window', sa.String(length=50), nullable=False, server_default='30d'),
        sa.Column('allowed_failure_amount', sa.Float(), nullable=False),
        sa.Column('current_failure_amount', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_reliability_budgets_org_id', 'reliability_budgets', ['organization_id'])
    op.create_index('ix_reliability_budgets_comp', 'reliability_budgets', ['component'])

    # 6. chaos_experiments
    op.create_table(
        'chaos_experiments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('environment', sa.String(length=50), nullable=False, server_default='test'),
        sa.Column('target_type', sa.String(length=100), nullable=False),
        sa.Column('target_id', sa.String(length=255), nullable=False),
        sa.Column('failure_type', sa.String(length=100), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('expected_behavior', sa.Text(), nullable=False),
        sa.Column('abort_conditions', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='planned'),
        sa.Column('created_by', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_chaos_experiments_org_id', 'chaos_experiments', ['organization_id'])
    op.create_index('ix_chaos_experiments_env', 'chaos_experiments', ['environment'])
    op.create_index('ix_chaos_experiments_status', 'chaos_experiments', ['status'])

    # 7. chaos_runs
    op.create_table(
        'chaos_runs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('experiment_id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='running'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('outcome', sa.Text(), nullable=True),
        sa.Column('error_summary', sa.Text(), nullable=True),
        sa.Column('logs', sa.JSON(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['experiment_id'], ['chaos_experiments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_chaos_runs_exp_id', 'chaos_runs', ['experiment_id'])
    op.create_index('ix_chaos_runs_status', 'chaos_runs', ['status'])

    # 8. chaos_observations
    op.create_table(
        'chaos_observations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('experiment_id', sa.String(length=36), nullable=False),
        sa.Column('run_id', sa.String(length=36), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metric', sa.String(length=100), nullable=False),
        sa.Column('value', sa.Float(), nullable=True),
        sa.Column('expected_value', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='matched'),
        sa.Column('metadata', sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['experiment_id'], ['chaos_experiments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['run_id'], ['chaos_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_chaos_observations_exp_id', 'chaos_observations', ['experiment_id'])
    op.create_index('ix_chaos_observations_run_id', 'chaos_observations', ['run_id'])
    op.create_index('ix_chaos_observations_timestamp', 'chaos_observations', ['timestamp'])


def downgrade() -> None:
    op.drop_table('chaos_observations')
    op.drop_table('chaos_runs')
    op.drop_table('chaos_experiments')
    op.drop_table('reliability_budgets')
    op.drop_table('reliability_objectives')
    op.drop_table('execution_checkpoints')
    op.drop_table('dependency_health')
    op.drop_table('reliability_components')
