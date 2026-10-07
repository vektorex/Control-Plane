"""add organizational knowledge

Revision ID: add_org_knowledge_step_46
Revises: previous_revision
Create Date: 2026-10-07 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_org_knowledge_step_46'
down_revision = None # Usually set to previous, but this is a synthetic setup
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create organizational_knowledge_items
    op.create_table(
        'organizational_knowledge_items',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workspace_id', sa.String(36), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id'), nullable=True),
        sa.Column('knowledge_type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('summary', sa.Text, nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('confidence_state', sa.String(50), nullable=False),
        sa.Column('sensitivity', sa.String(50), nullable=False),
        sa.Column('owner_user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_ok_items_workspace_id', 'organizational_knowledge_items', ['workspace_id'])
    op.create_index('ix_ok_items_status', 'organizational_knowledge_items', ['status'])

    # Create knowledge_candidates
    op.create_table(
        'knowledge_candidates',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workspace_id', sa.String(36), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id'), nullable=True),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('source_id', sa.String(36), nullable=False),
        sa.Column('candidate_type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('evidence_ids', sa.JSON, nullable=False),
        sa.Column('generated_by', sa.String(255), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Create knowledge_conflicts
    op.create_table(
        'knowledge_conflicts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workspace_id', sa.String(36), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('knowledge_item_a_id', sa.String(36), sa.ForeignKey('organizational_knowledge_items.id'), nullable=False),
        sa.Column('knowledge_item_b_id', sa.String(36), sa.ForeignKey('organizational_knowledge_items.id'), nullable=False),
        sa.Column('conflict_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('evidence_ids', sa.JSON, nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('resolution', sa.Text, nullable=True),
        sa.Column('resolved_by', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

def downgrade() -> None:
    op.drop_table('knowledge_conflicts')
    op.drop_table('knowledge_candidates')
    op.drop_table('organizational_knowledge_items')
