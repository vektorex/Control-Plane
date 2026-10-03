"""create disaster recovery, backup, restore, continuity, and exercises tables

Revision ID: 033
Revises: 032
Create Date: 2026-10-03 23:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '033'
down_revision: Union[str, None] = '032'
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None


def upgrade() -> None:
    # 1. backup_resources
    op.create_table(
        'backup_resources',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=True),
        sa.Column('project_id', sa.String(length=36), nullable=True),
        sa.Column('resource_type', sa.String(length=100), nullable=False),
        sa.Column('resource_id', sa.String(length=255), nullable=False),
        sa.Column('classification', sa.String(length=50), nullable=False, server_default='internal'),
        sa.Column('backup_required', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('backup_strategy', sa.String(length=50), nullable=False, server_default='logical_export'),
        sa.Column('dependency_policy', sa.String(length=50), nullable=False, server_default='required'),
        sa.Column('retention_policy_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_backup_resources_org_id', 'backup_resources', ['organization_id'])
    op.create_index('ix_backup_resources_workspace_id', 'backup_resources', ['workspace_id'])
    op.create_index('ix_backup_resources_res_type', 'backup_resources', ['resource_type'])
    op.create_index('ix_backup_resources_res_id', 'backup_resources', ['resource_id'])

    # 2. backup_policies
    op.create_table(
        'backup_policies',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('resource_type', sa.String(length=100), nullable=False, server_default='all'),
        sa.Column('frequency', sa.String(length=50), nullable=False, server_default='daily'),
        sa.Column('retention_days', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('strategy', sa.String(length=50), nullable=False, server_default='logical_export'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('verification_frequency', sa.String(length=50), nullable=False, server_default='after_backup'),
        sa.Column('created_by', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_backup_policies_org_id', 'backup_policies', ['organization_id'])
    op.create_index('ix_backup_policies_workspace_id', 'backup_policies', ['workspace_id'])

    # 3. backup_runs
    op.create_table(
        'backup_runs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=True),
        sa.Column('policy_id', sa.String(length=36), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='planned'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resource_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('byte_estimate', sa.Integer(), nullable=True),
        sa.Column('backup_version', sa.String(length=50), nullable=False, server_default='1.0'),
        sa.Column('manifest_id', sa.String(length=36), nullable=True),
        sa.Column('classification', sa.String(length=50), nullable=False, server_default='internal'),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['policy_id'], ['backup_policies.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_backup_runs_org_id', 'backup_runs', ['organization_id'])
    op.create_index('ix_backup_runs_workspace_id', 'backup_runs', ['workspace_id'])
    op.create_index('ix_backup_runs_status', 'backup_runs', ['status'])
    op.create_index('ix_backup_runs_created_at', 'backup_runs', ['created_at'])

    # 4. backup_manifests
    op.create_table(
        'backup_manifests',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('backup_run_id', sa.String(length=36), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False, server_default='1.0'),
        sa.Column('format', sa.String(length=50), nullable=False, server_default='json_logical'),
        sa.Column('resource_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('manifest_hash', sa.String(length=64), nullable=False),
        sa.Column('previous_manifest_hash', sa.String(length=64), nullable=True),
        sa.Column('storage_reference', sa.String(length=512), nullable=False),
        sa.Column('encryption_metadata', sa.JSON(), nullable=False),
        sa.Column('verification_status', sa.String(length=50), nullable=False, server_default='unverified'),
        sa.Column('resources_metadata', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['backup_run_id'], ['backup_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_backup_manifests_run_id', 'backup_manifests', ['backup_run_id'], unique=True)

    # 5. backup_verifications
    op.create_table(
        'backup_verifications',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('backup_run_id', sa.String(length=36), nullable=False),
        sa.Column('verification_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('details', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['backup_run_id'], ['backup_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_backup_verifications_run_id', 'backup_verifications', ['backup_run_id'])
    op.create_index('ix_backup_verifications_status', 'backup_verifications', ['status'])

    # 6. restore_plans
    op.create_table(
        'restore_plans',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=True),
        sa.Column('backup_run_id', sa.String(length=36), nullable=False),
        sa.Column('target_environment', sa.String(length=50), nullable=False, server_default='sandbox'),
        sa.Column('scope', sa.JSON(), nullable=False),
        sa.Column('mode', sa.String(length=50), nullable=False, server_default='dry_run'),
        sa.Column('conflict_policy', sa.String(length=50), nullable=False, server_default='skip_existing'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='planned'),
        sa.Column('approval_id', sa.String(length=36), nullable=True),
        sa.Column('approved_by', sa.String(length=255), nullable=True),
        sa.Column('blast_radius_summary', sa.JSON(), nullable=False),
        sa.Column('created_by', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['backup_run_id'], ['backup_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_restore_plans_org_id', 'restore_plans', ['organization_id'])
    op.create_index('ix_restore_plans_run_id', 'restore_plans', ['backup_run_id'])
    op.create_index('ix_restore_plans_status', 'restore_plans', ['status'])

    # 7. restore_runs
    op.create_table(
        'restore_runs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('restore_plan_id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='planned'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resource_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('restored_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('skipped_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('execution_log', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['restore_plan_id'], ['restore_plans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_restore_runs_plan_id', 'restore_runs', ['restore_plan_id'])
    op.create_index('ix_restore_runs_status', 'restore_runs', ['status'])

    # 8. recovery_objectives
    op.create_table(
        'recovery_objectives',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=True),
        sa.Column('resource_type', sa.String(length=100), nullable=False),
        sa.Column('resource_scope', sa.String(length=255), nullable=False, server_default='all'),
        sa.Column('rto_seconds', sa.Integer(), nullable=False),
        sa.Column('rpo_seconds', sa.Integer(), nullable=False),
        sa.Column('priority', sa.String(length=50), nullable=False, server_default='tier_1'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_recovery_objectives_org_id', 'recovery_objectives', ['organization_id'])
    op.create_index('ix_recovery_objectives_res_type', 'recovery_objectives', ['resource_type'])

    # 9. recovery_readiness
    op.create_table(
        'recovery_readiness',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=True),
        sa.Column('resource_type', sa.String(length=100), nullable=False),
        sa.Column('backup_status', sa.String(length=50), nullable=False, server_default='unknown'),
        sa.Column('verification_status', sa.String(length=50), nullable=False, server_default='unknown'),
        sa.Column('restore_test_status', sa.String(length=50), nullable=False, server_default='unknown'),
        sa.Column('last_successful_backup', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_successful_verification', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_successful_restore_test', sa.DateTime(timezone=True), nullable=True),
        sa.Column('observed_backup_age_seconds', sa.Integer(), nullable=True),
        sa.Column('estimated_restore_duration_seconds', sa.Integer(), nullable=True),
        sa.Column('overall_status', sa.String(length=50), nullable=False, server_default='unknown'),
        sa.Column('known_blockers', sa.JSON(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_recovery_readiness_org_id', 'recovery_readiness', ['organization_id'])
    op.create_index('ix_recovery_readiness_res_type', 'recovery_readiness', ['resource_type'])
    op.create_index('ix_recovery_readiness_status', 'recovery_readiness', ['overall_status'])

    # 10. continuity_plans
    op.create_table(
        'continuity_plans',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('critical_services', sa.JSON(), nullable=False),
        sa.Column('dependencies', sa.JSON(), nullable=False),
        sa.Column('fallback_modes', sa.JSON(), nullable=False),
        sa.Column('communication_plan', sa.JSON(), nullable=False),
        sa.Column('recovery_order', sa.JSON(), nullable=False),
        sa.Column('owner_id', sa.String(length=255), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_continuity_plans_org_id', 'continuity_plans', ['organization_id'])

    # 11. recovery_exercises
    op.create_table(
        'recovery_exercises',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('environment', sa.String(length=50), nullable=False, server_default='sandbox'),
        sa.Column('scope', sa.JSON(), nullable=False),
        sa.Column('scenario', sa.String(length=100), nullable=False),
        sa.Column('expected_recovery', sa.Text(), nullable=False),
        sa.Column('abort_conditions', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='planned'),
        sa.Column('created_by', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_recovery_exercises_org_id', 'recovery_exercises', ['organization_id'])
    op.create_index('ix_recovery_exercises_status', 'recovery_exercises', ['status'])

    # 12. recovery_exercise_observations
    op.create_table(
        'recovery_exercise_observations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('exercise_id', sa.String(length=36), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metric', sa.String(length=100), nullable=False),
        sa.Column('value', sa.String(length=255), nullable=False),
        sa.Column('expected_value', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='passed'),
        sa.Column('details', sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['exercise_id'], ['recovery_exercises.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_recovery_exercise_obs_ex_id', 'recovery_exercise_observations', ['exercise_id'])


def downgrade() -> None:
    op.drop_table('recovery_exercise_observations')
    op.drop_table('recovery_exercises')
    op.drop_table('continuity_plans')
    op.drop_table('recovery_readiness')
    op.drop_table('recovery_objectives')
    op.drop_table('restore_runs')
    op.drop_table('restore_plans')
    op.drop_table('backup_verifications')
    op.drop_table('backup_manifests')
    op.drop_table('backup_runs')
    op.drop_table('backup_policies')
    op.drop_table('backup_resources')
