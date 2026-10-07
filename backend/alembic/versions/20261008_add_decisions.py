"""add decision intelligence

Revision ID: add_decision_intelligence_step_51
Revises: add_intent_solution_step_50
Create Date: 2026-10-08 00:20:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_decision_intelligence_step_51'
down_revision = 'add_intent_solution_step_50'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create decision_requests table
    op.create_table(
        'decision_requests',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('workspace_id', sa.String(36), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id'), nullable=True),
        sa.Column('subject_type', sa.String(50), nullable=False),
        sa.Column('subject_id', sa.String(36), nullable=False),
        sa.Column('decision_type', sa.String(50), nullable=False),
        sa.Column('requested_by', sa.String(36), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, default='requested'),
        sa.Column('context_snapshot', sa.JSON, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Create decision_evidence table
    op.create_table(
        'decision_evidence',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('decision_request_id', sa.String(36), sa.ForeignKey('decision_requests.id'), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('source_id', sa.String(36), nullable=False),
        sa.Column('source_version', sa.String(50), nullable=True),
        sa.Column('evidence_type', sa.String(50), nullable=False),
        sa.Column('claim', sa.Text, nullable=False),
        sa.Column('value', sa.JSON, nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('observed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('provenance', sa.JSON, nullable=False),
    )

    # Create decision_records table
    op.create_table(
        'decision_records',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('decision_request_id', sa.String(36), sa.ForeignKey('decision_requests.id'), nullable=False),
        sa.Column('decision', sa.String(50), nullable=False),
        sa.Column('state', sa.String(50), nullable=False),
        sa.Column('decision_version', sa.String(50), nullable=False),
        sa.Column('conditions', sa.JSON, nullable=False),
        sa.Column('blockers', sa.JSON, nullable=False),
        sa.Column('evidence_snapshot', sa.JSON, nullable=False),
        sa.Column('policy_snapshot', sa.JSON, nullable=False),
        sa.Column('explanation', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Create decision_required_actions table
    op.create_table(
        'decision_required_actions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('decision_request_id', sa.String(36), sa.ForeignKey('decision_requests.id'), nullable=False),
        sa.Column('action_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('source', sa.String(100), nullable=False),
        sa.Column('blocking', sa.Boolean, nullable=False, default=True),
        sa.Column('requires_user', sa.Boolean, nullable=False, default=True),
        sa.Column('requires_approval', sa.Boolean, nullable=False, default=False),
        sa.Column('status', sa.String(50), nullable=False, default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    op.create_index('ix_decision_requests_org', 'decision_requests', ['organization_id'])
    op.create_index('ix_decision_requests_workspace', 'decision_requests', ['workspace_id'])
    op.create_index('ix_decision_requests_subject', 'decision_requests', ['subject_type', 'subject_id'])

def downgrade() -> None:
    op.drop_index('ix_decision_requests_subject', table_name='decision_requests')
    op.drop_index('ix_decision_requests_workspace', table_name='decision_requests')
    op.drop_index('ix_decision_requests_org', table_name='decision_requests')
    
    op.drop_table('decision_required_actions')
    op.drop_table('decision_records')
    op.drop_table('decision_evidence')
    op.drop_table('decision_requests')
