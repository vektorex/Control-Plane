"""add_changes

Revision ID: 20261008_add_changes
Revises: add_intent_step_50
Create Date: 2026-10-08 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20261008_add_changes'
down_revision = '20261008_add_intent'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'change_requests',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('change_type', sa.String(length=50), nullable=False),
        sa.Column('subject_type', sa.String(length=50), nullable=False),
        sa.Column('subject_id', sa.String(length=36), nullable=False),
        sa.Column('requested_by', sa.String(length=36), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('scope', sa.JSON(), nullable=False),
        sa.Column('proposed_change', sa.JSON(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('expected_benefit', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_change_requests_org', 'change_requests', ['organization_id'], unique=False)
    op.create_index('ix_change_requests_workspace', 'change_requests', ['workspace_id'], unique=False)
    op.create_index('ix_change_requests_subject', 'change_requests', ['subject_type', 'subject_id'], unique=False)

    op.create_table(
        'change_affected_resources',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('change_request_id', sa.String(length=36), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', sa.String(length=36), nullable=False),
        sa.Column('relationship_type', sa.String(length=50), nullable=False),
        sa.Column('impact_state', sa.String(length=50), nullable=False),
        sa.Column('impact_reason', sa.Text(), nullable=True),
        sa.Column('source_evidence', sa.JSON(), nullable=False),
        sa.Column('severity', sa.String(length=50), nullable=False),
        sa.Column('confidence_state', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['change_request_id'], ['change_requests.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table(
        'change_risks',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('change_request_id', sa.String(length=36), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('evidence', sa.JSON(), nullable=False),
        sa.Column('affected_resource', sa.String(length=100), nullable=True),
        sa.Column('mitigation', sa.Text(), nullable=True),
        sa.Column('blocking', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['change_request_id'], ['change_requests.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'change_revalidation_requirements',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('change_request_id', sa.String(length=36), nullable=False),
        sa.Column('requirement_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('affected_resource', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['change_request_id'], ['change_requests.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'change_evidence',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('change_request_id', sa.String(length=36), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('source_id', sa.String(length=36), nullable=False),
        sa.Column('source_version', sa.String(length=50), nullable=True),
        sa.Column('relationship', sa.String(length=100), nullable=False),
        sa.Column('observed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['change_request_id'], ['change_requests.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'change_analysis_records',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('change_request_id', sa.String(length=36), nullable=False),
        sa.Column('analysis_snapshot', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['change_request_id'], ['change_requests.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'change_rollback_analysis',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('change_request_id', sa.String(length=36), nullable=False),
        sa.Column('resource', sa.String(length=100), nullable=False),
        sa.Column('current_version', sa.String(length=50), nullable=True),
        sa.Column('previous_version', sa.String(length=50), nullable=True),
        sa.Column('rollback_possible', sa.Boolean(), nullable=False),
        sa.Column('rollback_dependencies', sa.JSON(), nullable=False),
        sa.Column('rollback_constraints', sa.JSON(), nullable=False),
        sa.Column('rollback_requirements', sa.JSON(), nullable=False),
        sa.Column('rollback_limitations', sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['change_request_id'], ['change_requests.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('change_rollback_analysis')
    op.drop_table('change_analysis_records')
    op.drop_table('change_evidence')
    op.drop_table('change_revalidation_requirements')
    op.drop_table('change_risks')
    op.drop_table('change_affected_resources')
    op.drop_table('change_requests')
