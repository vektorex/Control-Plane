"""add_progressive_delivery

Revision ID: 20261008_add_progressive_delivery
Revises: 20261008_add_releases
Create Date: 2026-10-08 00:01:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20261008_add_progressive_delivery'
down_revision = '20261008_add_releases'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'progressive_rollouts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=True),
        sa.Column('release_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('strategy_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('current_stage_id', sa.String(length=36), nullable=True),
        sa.Column('target_scope', sa.JSON(), nullable=False),
        sa.Column('policy', sa.JSON(), nullable=False),
        sa.Column('created_by', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['release_id'], ['releases.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table(
        'rollout_plans',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('rollout_id', sa.String(length=36), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('stages', sa.JSON(), nullable=False),
        sa.Column('gate_policy', sa.JSON(), nullable=False),
        sa.Column('observation_policy', sa.JSON(), nullable=False),
        sa.Column('rollback_policy', sa.JSON(), nullable=False),
        sa.Column('is_immutable', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['rollout_id'], ['progressive_rollouts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'rollout_stages',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('rollout_id', sa.String(length=36), nullable=False),
        sa.Column('stage_order', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('target_percentage', sa.Integer(), nullable=True),
        sa.Column('target_scope', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('minimum_observation_seconds', sa.Integer(), nullable=False),
        sa.Column('gate_policy', sa.JSON(), nullable=False),
        sa.Column('health_snapshot', sa.JSON(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['rollout_id'], ['progressive_rollouts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'rollout_targets',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('rollout_id', sa.String(length=36), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', sa.String(length=36), nullable=False),
        sa.Column('release_id', sa.String(length=36), nullable=False),
        sa.Column('target_type', sa.String(length=50), nullable=False),
        sa.Column('target_id', sa.String(length=36), nullable=False),
        sa.Column('eligible', sa.Boolean(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['rollout_id'], ['progressive_rollouts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'rollout_cohorts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('rollout_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('selection_type', sa.String(length=50), nullable=False),
        sa.Column('selection_config', sa.JSON(), nullable=False),
        sa.Column('member_count', sa.Integer(), nullable=True),
        sa.Column('membership_snapshot', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['rollout_id'], ['progressive_rollouts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'rollout_health_snapshots',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('rollout_id', sa.String(length=36), nullable=False),
        sa.Column('stage_id', sa.String(length=36), nullable=False),
        sa.Column('observed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('signals', sa.JSON(), nullable=False),
        sa.Column('unknown_signals', sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['rollout_id'], ['progressive_rollouts.id'], ),
        sa.ForeignKeyConstraint(['stage_id'], ['rollout_stages.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'rollout_comparisons',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('rollout_id', sa.String(length=36), nullable=False),
        sa.Column('current_version', sa.String(length=50), nullable=False),
        sa.Column('candidate_version', sa.String(length=50), nullable=False),
        sa.Column('baseline_metrics', sa.JSON(), nullable=False),
        sa.Column('candidate_metrics', sa.JSON(), nullable=False),
        sa.Column('differences', sa.JSON(), nullable=False),
        sa.Column('evidence', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['rollout_id'], ['progressive_rollouts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'rollout_gates',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('rollout_id', sa.String(length=36), nullable=False),
        sa.Column('stage_id', sa.String(length=36), nullable=False),
        sa.Column('gate_type', sa.String(length=50), nullable=False),
        sa.Column('condition', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('evidence', sa.JSON(), nullable=True),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['rollout_id'], ['progressive_rollouts.id'], ),
        sa.ForeignKeyConstraint(['stage_id'], ['rollout_stages.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'rollout_evidence',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('rollout_id', sa.String(length=36), nullable=False),
        sa.Column('evidence_type', sa.String(length=50), nullable=False),
        sa.Column('source_id', sa.String(length=36), nullable=False),
        sa.Column('details', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['rollout_id'], ['progressive_rollouts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'rollout_timeline_events',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('rollout_id', sa.String(length=36), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('actor_type', sa.String(length=50), nullable=False),
        sa.Column('actor_id', sa.String(length=36), nullable=True),
        sa.Column('stage', sa.String(length=50), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('metadata_payload', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['rollout_id'], ['progressive_rollouts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'rollout_pauses',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('rollout_id', sa.String(length=36), nullable=False),
        sa.Column('reason', sa.String(length=100), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('requested_by', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['rollout_id'], ['progressive_rollouts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('rollout_pauses')
    op.drop_table('rollout_timeline_events')
    op.drop_table('rollout_evidence')
    op.drop_table('rollout_gates')
    op.drop_table('rollout_comparisons')
    op.drop_table('rollout_health_snapshots')
    op.drop_table('rollout_cohorts')
    op.drop_table('rollout_targets')
    op.drop_table('rollout_stages')
    op.drop_table('rollout_plans')
    op.drop_table('progressive_rollouts')
