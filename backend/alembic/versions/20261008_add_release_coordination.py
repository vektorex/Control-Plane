"""add_release_coordination

Revision ID: 20261008_add_release_coordination
Revises: 20261008_add_progressive_delivery
Create Date: 2026-10-08 00:02:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20261008_add_release_coordination'
down_revision = '20261008_add_progressive_delivery'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'release_portfolios',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('owner_id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table(
        'release_trains',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('portfolio_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('owner_id', sa.String(length=36), nullable=False),
        sa.Column('start_window', sa.DateTime(timezone=True), nullable=True),
        sa.Column('target_completion', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['portfolio_id'], ['release_portfolios.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'release_groups',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('release_train_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('purpose', sa.String(length=50), nullable=False),
        sa.Column('sequence_order', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['release_train_id'], ['release_trains.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'release_waves',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('release_train_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('sequence_number', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('planned_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('planned_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['release_train_id'], ['release_trains.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'release_sequences',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('release_train_id', sa.String(length=36), nullable=False),
        sa.Column('release_id', sa.String(length=36), nullable=False),
        sa.Column('wave_id', sa.String(length=36), nullable=True),
        sa.Column('sequence_number', sa.Integer(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['release_train_id'], ['release_trains.id'], ),
        sa.ForeignKeyConstraint(['release_id'], ['releases.id'], ),
        sa.ForeignKeyConstraint(['wave_id'], ['release_waves.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'release_wave_items',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('wave_id', sa.String(length=36), nullable=False),
        sa.Column('release_id', sa.String(length=36), nullable=False),
        sa.Column('sequence_order', sa.Integer(), nullable=False),
        sa.Column('required', sa.Boolean(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['wave_id'], ['release_waves.id'], ),
        sa.ForeignKeyConstraint(['release_id'], ['releases.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'release_dependencies',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('release_train_id', sa.String(length=36), nullable=False),
        sa.Column('source_release_id', sa.String(length=36), nullable=False),
        sa.Column('target_release_id', sa.String(length=36), nullable=False),
        sa.Column('dependency_type', sa.String(length=50), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['release_train_id'], ['release_trains.id'], ),
        sa.ForeignKeyConstraint(['source_release_id'], ['releases.id'], ),
        sa.ForeignKeyConstraint(['target_release_id'], ['releases.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'release_conflicts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('release_train_id', sa.String(length=36), nullable=False),
        sa.Column('release_a_id', sa.String(length=36), nullable=True),
        sa.Column('release_b_id', sa.String(length=36), nullable=True),
        sa.Column('conflict_type', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('evidence', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('resolution', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['release_train_id'], ['release_trains.id'], ),
        sa.ForeignKeyConstraint(['release_a_id'], ['releases.id'], ),
        sa.ForeignKeyConstraint(['release_b_id'], ['releases.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'change_windows',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('window_type', sa.String(length=50), nullable=False),
        sa.Column('starts_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ends_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('timezone', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('created_by', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'release_calendar_entries',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('release_train_id', sa.String(length=36), nullable=True),
        sa.Column('release_id', sa.String(length=36), nullable=True),
        sa.Column('rollout_id', sa.String(length=36), nullable=True),
        sa.Column('entry_type', sa.String(length=50), nullable=False),
        sa.Column('starts_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ends_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('environment', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['release_train_id'], ['release_trains.id'], ),
        sa.ForeignKeyConstraint(['release_id'], ['releases.id'], ),
        sa.ForeignKeyConstraint(['rollout_id'], ['progressive_rollouts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'coordination_decisions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('release_train_id', sa.String(length=36), nullable=False),
        sa.Column('decision_type', sa.String(length=50), nullable=False),
        sa.Column('decision', sa.JSON(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('evidence', sa.JSON(), nullable=False),
        sa.Column('created_by', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['release_train_id'], ['release_trains.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('coordination_decisions')
    op.drop_table('release_calendar_entries')
    op.drop_table('change_windows')
    op.drop_table('release_conflicts')
    op.drop_table('release_dependencies')
    op.drop_table('release_wave_items')
    op.drop_table('release_sequences')
    op.drop_table('release_waves')
    op.drop_table('release_groups')
    op.drop_table('release_trains')
    op.drop_table('release_portfolios')
