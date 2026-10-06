"""create simulations, simulation_versions, simulation_environments, simulation_scenarios, fault_profiles, fault_injections, simulation_runs, simulation_assertions, simulation_side_effects, simulation_suites, simulation_suite_scenarios, simulation_comparisons

Revision ID: 038
Revises: 037
Create Date: 2026-10-06 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

JSONB = sa.JSON().with_variant(postgresql.JSONB, "postgresql")

# revision identifiers, used by Alembic.
revision: str = '038'
down_revision: Union[str, None] = '037'
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None


def upgrade() -> None:
    # 1. simulations
    op.create_table(
        'simulations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=True),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('slug', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='draft'),
        sa.Column('simulation_type', sa.String(length=32), nullable=False, server_default='single_agent'),
        sa.Column('target_type', sa.String(length=32), nullable=False),
        sa.Column('target_id', sa.String(length=36), nullable=False),
        sa.Column('target_version_id', sa.String(length=36), nullable=True),
        sa.Column('current_version_id', sa.String(length=36), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workspace_id', 'slug', name='uq_simulations_ws_slug'),
    )
    op.create_index('ix_simulations_workspace_id', 'simulations', ['workspace_id'])
    op.create_index('ix_simulations_project_id', 'simulations', ['project_id'])
    op.create_index('ix_simulations_slug', 'simulations', ['slug'])
    op.create_index('ix_simulations_status', 'simulations', ['status'])
    op.create_index('ix_simulations_target_id', 'simulations', ['target_id'])
    op.create_index('ix_simulations_ws_status', 'simulations', ['workspace_id', 'status'])
    op.create_index('ix_simulations_target', 'simulations', ['target_type', 'target_id'])

    # 2. simulation_versions
    op.create_table(
        'simulation_versions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('simulation_id', sa.String(length=36), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('configuration', JSONB, nullable=False),
        sa.Column('environment_config', JSONB, nullable=False),
        sa.Column('scenario_config', JSONB, nullable=False),
        sa.Column('fault_config', JSONB, nullable=False),
        sa.Column('policy_overrides', JSONB, nullable=False),
        sa.Column('assertions', JSONB, nullable=False),
        sa.Column('created_by', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['simulation_id'], ['simulations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('simulation_id', 'version', name='uq_simulation_versions_sim_ver'),
    )
    op.create_index('ix_simulation_versions_simulation_id', 'simulation_versions', ['simulation_id'])

    # 3. simulation_environments
    op.create_table(
        'simulation_environments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('mode', sa.String(length=32), nullable=False, server_default='isolated'),
        sa.Column('config', JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_simulation_environments_workspace_id', 'simulation_environments', ['workspace_id'])
    op.create_index('ix_sim_env_ws_mode', 'simulation_environments', ['workspace_id', 'mode'])

    # 4. simulation_scenarios
    op.create_table(
        'simulation_scenarios',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('simulation_version_id', sa.String(length=36), nullable=True),
        sa.Column('suite_id', sa.String(length=36), nullable=True),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('scenario_type', sa.String(length=32), nullable=False, server_default='normal'),
        sa.Column('input', JSONB, nullable=False),
        sa.Column('context', JSONB, nullable=False),
        sa.Column('environment_state', JSONB, nullable=False),
        sa.Column('expected_behavior', JSONB, nullable=False),
        sa.Column('fault_configuration', JSONB, nullable=False),
        sa.Column('assertions', JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_simulation_scenarios_simulation_version_id', 'simulation_scenarios', ['simulation_version_id'])
    op.create_index('ix_simulation_scenarios_suite_id', 'simulation_scenarios', ['suite_id'])
    op.create_index('ix_simulation_scenarios_workspace_id', 'simulation_scenarios', ['workspace_id'])
    op.create_index('ix_sim_scen_ws_type', 'simulation_scenarios', ['workspace_id', 'scenario_type'])

    # 5. fault_profiles
    op.create_table(
        'fault_profiles',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('faults', JSONB, nullable=False),
        sa.Column('distribution_mode', sa.String(length=32), nullable=False, server_default='fixed'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_fault_profiles_workspace_id', 'fault_profiles', ['workspace_id'])

    # 6. simulation_runs
    op.create_table(
        'simulation_runs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('simulation_id', sa.String(length=36), nullable=False),
        sa.Column('simulation_version_id', sa.String(length=36), nullable=True),
        sa.Column('scenario_id', sa.String(length=36), nullable=True),
        sa.Column('suite_id', sa.String(length=36), nullable=True),
        sa.Column('seed', sa.Integer(), nullable=False, server_default='42'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='queued'),
        sa.Column('target_type', sa.String(length=32), nullable=False),
        sa.Column('target_id', sa.String(length=36), nullable=False),
        sa.Column('target_version_id', sa.String(length=36), nullable=True),
        sa.Column('environment_snapshot_id', sa.String(length=36), nullable=True),
        sa.Column('execution_snapshot_id', sa.String(length=36), nullable=True),
        sa.Column('policy_snapshot', JSONB, nullable=False),
        sa.Column('fault_snapshot', JSONB, nullable=False),
        sa.Column('output', JSONB, nullable=False),
        sa.Column('assertion_results', JSONB, nullable=False),
        sa.Column('side_effects', JSONB, nullable=False),
        sa.Column('events_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('tool_calls', JSONB, nullable=False),
        sa.Column('connector_calls', JSONB, nullable=False),
        sa.Column('delegations', JSONB, nullable=False),
        sa.Column('tokens', JSONB, nullable=False),
        sa.Column('cost', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('latency', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('reproducibility_metadata', JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['simulation_id'], ['simulations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_simulation_runs_simulation_id', 'simulation_runs', ['simulation_id'])
    op.create_index('ix_simulation_runs_simulation_version_id', 'simulation_runs', ['simulation_version_id'])
    op.create_index('ix_simulation_runs_scenario_id', 'simulation_runs', ['scenario_id'])
    op.create_index('ix_simulation_runs_suite_id', 'simulation_runs', ['suite_id'])
    op.create_index('ix_simulation_runs_status', 'simulation_runs', ['status'])
    op.create_index('ix_simulation_runs_target_id', 'simulation_runs', ['target_id'])
    op.create_index('ix_sim_runs_sim_status', 'simulation_runs', ['simulation_id', 'status'])
    op.create_index('ix_sim_runs_target', 'simulation_runs', ['target_type', 'target_id'])

    # 7. fault_injections
    op.create_table(
        'fault_injections',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('run_id', sa.String(length=36), nullable=False),
        sa.Column('fault_type', sa.String(length=64), nullable=False),
        sa.Column('target', sa.String(length=128), nullable=False),
        sa.Column('parameters', JSONB, nullable=False),
        sa.Column('trigger_condition', JSONB, nullable=False),
        sa.Column('injected_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('result', sa.String(length=64), nullable=False, server_default='injected'),
        sa.ForeignKeyConstraint(['run_id'], ['simulation_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_fault_injections_run_id', 'fault_injections', ['run_id'])

    # 8. simulation_assertions
    op.create_table(
        'simulation_assertions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('run_id', sa.String(length=36), nullable=False),
        sa.Column('assertion_type', sa.String(length=64), nullable=False),
        sa.Column('parameters', JSONB, nullable=False),
        sa.Column('expected', JSONB, nullable=True),
        sa.Column('actual', JSONB, nullable=True),
        sa.Column('passed', sa.Boolean(), nullable=False),
        sa.Column('severity', sa.String(length=32), nullable=False, server_default='error'),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['run_id'], ['simulation_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_simulation_assertions_run_id', 'simulation_assertions', ['run_id'])

    # 9. simulation_side_effects
    op.create_table(
        'simulation_side_effects',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('run_id', sa.String(length=36), nullable=False),
        sa.Column('intended_action', sa.String(length=128), nullable=False),
        sa.Column('actor', sa.String(length=128), nullable=False, server_default='agent'),
        sa.Column('target', sa.String(length=256), nullable=False),
        sa.Column('parameters', JSONB, nullable=False),
        sa.Column('policy_decision', sa.String(length=64), nullable=False, server_default='blocked'),
        sa.Column('would_require_approval', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('simulated_result', JSONB, nullable=False),
        sa.Column('intercepted_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['run_id'], ['simulation_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_simulation_side_effects_run_id', 'simulation_side_effects', ['run_id'])

    # 10. simulation_suites
    op.create_table(
        'simulation_suites',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=True),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('target_type', sa.String(length=32), nullable=False),
        sa.Column('target_id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='active'),
        sa.Column('created_by', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_simulation_suites_workspace_id', 'simulation_suites', ['workspace_id'])
    op.create_index('ix_simulation_suites_project_id', 'simulation_suites', ['project_id'])
    op.create_index('ix_simulation_suites_status', 'simulation_suites', ['status'])
    op.create_index('ix_simulation_suites_target_id', 'simulation_suites', ['target_id'])
    op.create_index('ix_sim_suites_ws_target', 'simulation_suites', ['workspace_id', 'target_type', 'target_id'])

    # 11. simulation_suite_scenarios
    op.create_table(
        'simulation_suite_scenarios',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('suite_id', sa.String(length=36), nullable=False),
        sa.Column('scenario_id', sa.String(length=36), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['suite_id'], ['simulation_suites.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_simulation_suite_scenarios_suite_id', 'simulation_suite_scenarios', ['suite_id'])
    op.create_index('ix_simulation_suite_scenarios_scenario_id', 'simulation_suite_scenarios', ['scenario_id'])

    # 12. simulation_comparisons
    op.create_table(
        'simulation_comparisons',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('baseline_run_id', sa.String(length=36), nullable=False),
        sa.Column('comparison_run_id', sa.String(length=36), nullable=False),
        sa.Column('factual_differences', JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_simulation_comparisons_workspace_id', 'simulation_comparisons', ['workspace_id'])
    op.create_index('ix_simulation_comparisons_baseline_run_id', 'simulation_comparisons', ['baseline_run_id'])
    op.create_index('ix_simulation_comparisons_comparison_run_id', 'simulation_comparisons', ['comparison_run_id'])
    op.create_index('ix_sim_comp_pair', 'simulation_comparisons', ['baseline_run_id', 'comparison_run_id'])


def downgrade() -> None:
    op.drop_table('simulation_comparisons')
    op.drop_table('simulation_suite_scenarios')
    op.drop_table('simulation_suites')
    op.drop_table('simulation_side_effects')
    op.drop_table('simulation_assertions')
    op.drop_table('fault_injections')
    op.drop_table('simulation_runs')
    op.drop_table('fault_profiles')
    op.drop_table('simulation_scenarios')
    op.drop_table('simulation_environments')
    op.drop_table('simulation_versions')
    op.drop_table('simulations')
