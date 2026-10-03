"""create collaboration sessions, participants, presence, comments, annotations, and co-execution

Revision ID: 036
Revises: 035
Create Date: 2026-10-04 00:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

JSONB = sa.JSON().with_variant(postgresql.JSONB, "postgresql")

# revision identifiers, used by Alembic.
revision: str = '036'
down_revision: Union[str, None] = '035'
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None


def upgrade() -> None:
    # 1. collaboration_sessions
    op.create_table(
        'collaboration_sessions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=True),
        sa.Column('resource_type', sa.String(length=64), nullable=False),
        sa.Column('resource_id', sa.String(length=128), nullable=False),
        sa.Column('created_by', sa.String(length=36), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_collab_sessions_org', 'collaboration_sessions', ['organization_id'])
    op.create_index('ix_collab_sessions_ws', 'collaboration_sessions', ['workspace_id'])
    op.create_index('ix_collab_sessions_project', 'collaboration_sessions', ['project_id'])
    op.create_index('ix_collab_sessions_status', 'collaboration_sessions', ['status'])
    op.create_index('ix_collab_sessions_resource', 'collaboration_sessions', ['resource_type', 'resource_id'])

    # 2. collaboration_participants
    op.create_table(
        'collaboration_participants',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('role', sa.String(length=32), nullable=False, server_default='editor'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='active'),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('left_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['collaboration_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id', 'user_id', name='uq_collab_session_participant'),
    )
    op.create_index('ix_collab_participants_session', 'collaboration_participants', ['session_id'])
    op.create_index('ix_collab_participants_user', 'collaboration_participants', ['user_id'])
    op.create_index('ix_collab_participants_status', 'collaboration_participants', ['status'])

    # 3. presence_states
    op.create_table(
        'presence_states',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='active'),
        sa.Column('cursor_context', JSONB, nullable=True),
        sa.Column('active_resource', sa.String(length=128), nullable=True),
        sa.Column('last_heartbeat_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['collaboration_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id', 'user_id', name='uq_presence_session_user'),
    )
    op.create_index('ix_presence_session_id', 'presence_states', ['session_id'])
    op.create_index('ix_presence_user_id', 'presence_states', ['user_id'])
    op.create_index('ix_presence_last_heartbeat', 'presence_states', ['last_heartbeat_at'])

    # 4. collaboration_activities
    op.create_table(
        'collaboration_activities',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('actor_type', sa.String(length=32), nullable=False, server_default='user'),
        sa.Column('actor_id', sa.String(length=36), nullable=True),
        sa.Column('activity_type', sa.String(length=64), nullable=False),
        sa.Column('resource_type', sa.String(length=64), nullable=False),
        sa.Column('resource_id', sa.String(length=128), nullable=False),
        sa.Column('summary', sa.String(length=512), nullable=False),
        sa.Column('activity_metadata', JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['collaboration_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_collab_activity_session', 'collaboration_activities', ['session_id'])
    op.create_index('ix_collab_activity_type', 'collaboration_activities', ['activity_type'])
    op.create_index('ix_collab_activity_created', 'collaboration_activities', ['created_at'])

    # 5. collaboration_comments
    op.create_table(
        'collaboration_comments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('resource_type', sa.String(length=64), nullable=False),
        sa.Column('resource_id', sa.String(length=128), nullable=False),
        sa.Column('author_id', sa.String(length=36), nullable=False),
        sa.Column('author_type', sa.String(length=32), nullable=False, server_default='user'),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='active'),
        sa.Column('parent_comment_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['collaboration_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_comment_id'], ['collaboration_comments.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_collab_comments_session', 'collaboration_comments', ['session_id'])
    op.create_index('ix_collab_comments_resource', 'collaboration_comments', ['resource_type', 'resource_id'])
    op.create_index('ix_collab_comments_author', 'collaboration_comments', ['author_id'])
    op.create_index('ix_collab_comments_status', 'collaboration_comments', ['status'])

    # 6. comment_mentions
    op.create_table(
        'comment_mentions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('comment_id', sa.String(length=36), nullable=False),
        sa.Column('mentioned_user_id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('notified_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['comment_id'], ['collaboration_comments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_comment_mentions_comment', 'comment_mentions', ['comment_id'])
    op.create_index('ix_comment_mentions_user', 'comment_mentions', ['mentioned_user_id'])

    # 7. collaboration_assignments
    op.create_table(
        'collaboration_assignments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('resource_type', sa.String(length=64), nullable=False),
        sa.Column('resource_id', sa.String(length=128), nullable=False),
        sa.Column('assigned_to', sa.String(length=36), nullable=False),
        sa.Column('assigned_by', sa.String(length=36), nullable=False),
        sa.Column('assignment_type', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='pending'),
        sa.Column('due_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['collaboration_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_collab_assign_session', 'collaboration_assignments', ['session_id'])
    op.create_index('ix_collab_assign_user', 'collaboration_assignments', ['assigned_to'])
    op.create_index('ix_collab_assign_status', 'collaboration_assignments', ['status'])

    # 8. collaboration_annotations
    op.create_table(
        'collaboration_annotations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('resource_type', sa.String(length=64), nullable=False),
        sa.Column('resource_id', sa.String(length=128), nullable=False),
        sa.Column('author_id', sa.String(length=36), nullable=False),
        sa.Column('annotation_type', sa.String(length=64), nullable=False),
        sa.Column('target', JSONB, nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['collaboration_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_collab_annotations_session', 'collaboration_annotations', ['session_id'])
    op.create_index('ix_collab_annotations_resource', 'collaboration_annotations', ['resource_type', 'resource_id'])

    # 9. collaboration_decisions
    op.create_table(
        'collaboration_decisions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('resource_type', sa.String(length=64), nullable=False),
        sa.Column('resource_id', sa.String(length=128), nullable=False),
        sa.Column('decision_type', sa.String(length=64), nullable=False),
        sa.Column('decision', JSONB, nullable=False),
        sa.Column('created_by', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('supersedes_id', sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['collaboration_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_collab_decisions_session', 'collaboration_decisions', ['session_id'])

    # 10. co_execution_sessions
    op.create_table(
        'co_execution_sessions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('collaboration_session_id', sa.String(length=36), nullable=False),
        sa.Column('run_id', sa.String(length=36), nullable=True),
        sa.Column('workflow_run_id', sa.String(length=36), nullable=True),
        sa.Column('initiated_by', sa.String(length=36), nullable=False),
        sa.Column('mode', sa.String(length=64), nullable=False, server_default='human_assisted'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='planning'),
        sa.Column('context_config', JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['collaboration_session_id'], ['collaboration_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_co_exec_session', 'co_execution_sessions', ['collaboration_session_id'])
    op.create_index('ix_co_exec_run', 'co_execution_sessions', ['run_id'])
    op.create_index('ix_co_exec_status', 'co_execution_sessions', ['status'])

    # 11. collaboration_locks
    op.create_table(
        'collaboration_locks',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('resource_type', sa.String(length=64), nullable=False),
        sa.Column('resource_id', sa.String(length=128), nullable=False),
        sa.Column('owner_id', sa.String(length=36), nullable=False),
        sa.Column('acquired_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('resource_type', 'resource_id', name='uq_collab_lock_resource'),
    )
    op.create_index('ix_collab_lock_expires', 'collaboration_locks', ['expires_at'])

    # 12. collaboration_changes
    op.create_table(
        'collaboration_changes',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('resource_type', sa.String(length=64), nullable=False),
        sa.Column('resource_id', sa.String(length=128), nullable=False),
        sa.Column('actor_id', sa.String(length=36), nullable=False),
        sa.Column('change_type', sa.String(length=64), nullable=False),
        sa.Column('before_version', sa.Integer(), nullable=False),
        sa.Column('after_version', sa.Integer(), nullable=False),
        sa.Column('summary', sa.String(length=512), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['collaboration_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_collab_changes_session', 'collaboration_changes', ['session_id'])

    # 13. collaboration_conflicts
    op.create_table(
        'collaboration_conflicts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('resource_type', sa.String(length=64), nullable=False),
        sa.Column('resource_id', sa.String(length=128), nullable=False),
        sa.Column('base_version', sa.Integer(), nullable=False),
        sa.Column('current_version', sa.Integer(), nullable=False),
        sa.Column('incoming_version', sa.Integer(), nullable=False),
        sa.Column('actor_id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='open'),
        sa.Column('resolution_strategy', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['collaboration_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_collab_conflicts_session', 'collaboration_conflicts', ['session_id'])
    op.create_index('ix_collab_conflicts_status', 'collaboration_conflicts', ['status'])

    # 14. collaborative_states
    op.create_table(
        'collaborative_states',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('resource_type', sa.String(length=64), nullable=False),
        sa.Column('resource_id', sa.String(length=128), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('state', JSONB, nullable=False),
        sa.Column('updated_by', sa.String(length=36), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['collaboration_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id', 'resource_type', 'resource_id', name='uq_collab_state_session_resource'),
    )
    op.create_index('ix_collab_state_lookup', 'collaborative_states', ['session_id', 'resource_type', 'resource_id'])

    # 15. collaboration_snapshots
    op.create_table(
        'collaboration_snapshots',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('resource_type', sa.String(length=64), nullable=False),
        sa.Column('resource_id', sa.String(length=128), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('state_hash', sa.String(length=64), nullable=False),
        sa.Column('state', JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['collaboration_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_collab_snapshots_session', 'collaboration_snapshots', ['session_id'])


def downgrade() -> None:
    op.drop_table('collaboration_snapshots')
    op.drop_table('collaborative_states')
    op.drop_table('collaboration_conflicts')
    op.drop_table('collaboration_changes')
    op.drop_table('collaboration_locks')
    op.drop_table('co_execution_sessions')
    op.drop_table('collaboration_decisions')
    op.drop_table('collaboration_annotations')
    op.drop_table('collaboration_assignments')
    op.drop_table('comment_mentions')
    op.drop_table('collaboration_comments')
    op.drop_table('collaboration_activities')
    op.drop_table('presence_states')
    op.drop_table('collaboration_participants')
    op.drop_table('collaboration_sessions')
