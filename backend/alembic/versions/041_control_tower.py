"""create control_tower_views, attention_items, control_tower_snapshots, workstreams, workstream_members

Revision ID: 041
Revises: 040
Create Date: 2026-10-07 02:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

JSONB = sa.JSON().with_variant(postgresql.JSONB, "postgresql")

# revision identifiers, used by Alembic.
revision: str = '041'
down_revision: Union[str, None] = '040'
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None


def upgrade() -> None:
    # 1. control_tower_views
    op.create_table(
        'control_tower_views',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('configuration', JSONB, nullable=False, server_default='{}'),
        sa.Column('is_shared', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('shared_with_workspace', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_by', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_ct_views_workspace_id', 'control_tower_views', ['workspace_id'])
    op.create_index('ix_ct_views_project_id', 'control_tower_views', ['project_id'])
    op.create_index('ix_ct_views_created_by', 'control_tower_views', ['created_by'])
    op.create_index('ix_ct_views_workspace_user', 'control_tower_views', ['workspace_id', 'created_by'])

    # 2. attention_items
    op.create_table(
        'attention_items',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=True),
        sa.Column('source_type', sa.String(length=64), nullable=False),
        sa.Column('source_id', sa.String(length=36), nullable=False),
        sa.Column('attention_type', sa.String(length=64), nullable=False),
        sa.Column('severity', sa.String(length=16), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('evidence_ids', JSONB, nullable=False, server_default='[]'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='open'),
        sa.Column('acknowledged_by', sa.String(length=36), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'workspace_id', 'source_type', 'source_id', 'attention_type', 'status',
            name='uq_attention_dedup'
        ),
    )
    op.create_index('ix_attention_ws_id', 'attention_items', ['workspace_id'])
    op.create_index('ix_attention_project_id', 'attention_items', ['project_id'])
    op.create_index('ix_attention_source_type', 'attention_items', ['source_type'])
    op.create_index('ix_attention_source_id', 'attention_items', ['source_id'])
    op.create_index('ix_attention_attention_type', 'attention_items', ['attention_type'])
    op.create_index('ix_attention_severity', 'attention_items', ['severity'])
    op.create_index('ix_attention_status', 'attention_items', ['status'])
    op.create_index('ix_attention_ws_status', 'attention_items', ['workspace_id', 'status'])
    op.create_index('ix_attention_ws_severity', 'attention_items', ['workspace_id', 'severity'])
    op.create_index('ix_attention_source', 'attention_items', ['source_type', 'source_id'])
    op.create_index('ix_attention_created', 'attention_items', ['created_at'])

    # 3. control_tower_snapshots
    op.create_table(
        'control_tower_snapshots',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('source_watermarks', JSONB, nullable=False, server_default='{}'),
        sa.Column('summary', JSONB, nullable=False, server_default='{}'),
        sa.Column('partial_failures', JSONB, nullable=False, server_default='[]'),
        sa.Column('is_stale', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_snapshot_ws_id', 'control_tower_snapshots', ['workspace_id'])
    op.create_index('ix_snapshot_generated_at', 'control_tower_snapshots', ['generated_at'])
    op.create_index('ix_snapshot_ws_generated', 'control_tower_snapshots', ['workspace_id', 'generated_at'])

    # 4. workstreams
    op.create_table(
        'workstreams',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('configuration', JSONB, nullable=False, server_default='{}'),
        sa.Column('created_by', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_workstream_workspace_id', 'workstreams', ['workspace_id'])
    op.create_index('ix_workstream_project_id', 'workstreams', ['project_id'])

    # 5. workstream_members
    op.create_table(
        'workstream_members',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workstream_id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('member_id', sa.String(length=36), nullable=False),
        sa.Column('member_type', sa.String(length=32), nullable=False, server_default='user'),
        sa.Column('role', sa.String(length=32), nullable=False, server_default='member'),
        sa.Column('added_by', sa.String(length=36), nullable=False),
        sa.Column('added_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workstream_id', 'member_id', 'member_type', name='uq_workstream_member'),
    )
    op.create_index('ix_wsm_workstream_id', 'workstream_members', ['workstream_id'])
    op.create_index('ix_wsm_workspace_id', 'workstream_members', ['workspace_id'])


def downgrade() -> None:
    op.drop_table('workstream_members')
    op.drop_table('workstreams')
    op.drop_table('control_tower_snapshots')
    op.drop_table('attention_items')
    op.drop_table('control_tower_views')
