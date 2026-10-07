"""add_releases

Revision ID: 20261008_add_releases
Revises: 20261008_add_changes
Create Date: 2026-10-08 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20261008_add_releases'
down_revision = '20261008_add_changes'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'releases',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('change_request_id', sa.String(length=36), nullable=False),
        sa.Column('release_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('source_environment', sa.String(length=50), nullable=False),
        sa.Column('target_environment', sa.String(length=50), nullable=False),
        sa.Column('requested_by', sa.String(length=36), nullable=False),
        sa.Column('release_plan_id', sa.String(length=36), nullable=True),
        sa.Column('current_stage', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['change_request_id'], ['change_requests.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table(
        'release_candidates',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('release_id', sa.String(length=36), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', sa.String(length=36), nullable=False),
        sa.Column('source_version', sa.String(length=50), nullable=False),
        sa.Column('target_version', sa.String(length=50), nullable=False),
        sa.Column('current_state_snapshot', sa.JSON(), nullable=False),
        sa.Column('proposed_state_snapshot', sa.JSON(), nullable=False),
        sa.Column('change_summary', sa.JSON(), nullable=False),
        sa.Column('impact_analysis_id', sa.String(length=36), nullable=False),
        sa.Column('decision_record_id', sa.String(length=36), nullable=False),
        sa.Column('candidate_status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['release_id'], ['releases.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table(
        'release_environments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('environment_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('governance_policy_reference', sa.String(length=255), nullable=True),
        sa.Column('requires_approval', sa.Boolean(), nullable=False),
        sa.Column('requires_evaluation', sa.Boolean(), nullable=False),
        sa.Column('requires_simulation', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'release_plans',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('release_id', sa.String(length=36), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('stages', sa.JSON(), nullable=False),
        sa.Column('preconditions', sa.JSON(), nullable=False),
        sa.Column('verification_requirements', sa.JSON(), nullable=False),
        sa.Column('rollback_requirements', sa.JSON(), nullable=False),
        sa.Column('created_by', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_immutable', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['release_id'], ['releases.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'release_stage_records',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('release_id', sa.String(length=36), nullable=False),
        sa.Column('stage_key', sa.String(length=50), nullable=False),
        sa.Column('stage_order', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('evidence', sa.JSON(), nullable=True),
        sa.Column('error', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['release_id'], ['releases.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'release_freezes',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('scope_type', sa.String(length=50), nullable=False),
        sa.Column('scope_id', sa.String(length=36), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('starts_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ends_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'release_locks',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', sa.String(length=36), nullable=False),
        sa.Column('release_id', sa.String(length=36), nullable=False),
        sa.Column('acquired_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('heartbeat_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['release_id'], ['releases.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'release_observations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('release_id', sa.String(length=36), nullable=False),
        sa.Column('observation_type', sa.String(length=50), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('value', sa.JSON(), nullable=False),
        sa.Column('observed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['release_id'], ['releases.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'release_verifications',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('release_id', sa.String(length=36), nullable=False),
        sa.Column('verification_type', sa.String(length=50), nullable=False),
        sa.Column('expected_state', sa.JSON(), nullable=False),
        sa.Column('observed_state', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('evidence', sa.JSON(), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['release_id'], ['releases.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'release_rollbacks',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('release_id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('strategy', sa.String(length=50), nullable=False),
        sa.Column('target_version', sa.String(length=50), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('requested_by', sa.String(length=36), nullable=False),
        sa.Column('approved_by', sa.String(length=36), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verification_status', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['release_id'], ['releases.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'release_evidence',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('release_id', sa.String(length=36), nullable=False),
        sa.Column('evidence_type', sa.String(length=50), nullable=False),
        sa.Column('source_id', sa.String(length=36), nullable=False),
        sa.Column('details', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['release_id'], ['releases.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'release_timeline_events',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('release_id', sa.String(length=36), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('actor_type', sa.String(length=50), nullable=False),
        sa.Column('actor_id', sa.String(length=36), nullable=True),
        sa.Column('stage', sa.String(length=50), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('metadata_payload', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['release_id'], ['releases.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('release_timeline_events')
    op.drop_table('release_evidence')
    op.drop_table('release_rollbacks')
    op.drop_table('release_verifications')
    op.drop_table('release_observations')
    op.drop_table('release_locks')
    op.drop_table('release_freezes')
    op.drop_table('release_stage_records')
    op.drop_table('release_plans')
    op.drop_table('release_environments')
    op.drop_table('release_candidates')
    op.drop_table('releases')
