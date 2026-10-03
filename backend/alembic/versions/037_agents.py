"""create agent, agent_versions, agent_runs, delegations, teams, team_versions, team_members, team_runs, agent_messages, agent_conflicts

Revision ID: 037
Revises: 036
Create Date: 2026-10-04 01:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

JSONB = sa.JSON().with_variant(postgresql.JSONB, "postgresql")

# revision identifiers, used by Alembic.
revision: str = '037'
down_revision: Union[str, None] = '036'
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None


def upgrade() -> None:
    # 1. agents
    op.create_table(
        'agents',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=True),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('slug', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('purpose', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='draft'),
        sa.Column('current_version_id', sa.String(length=36), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workspace_id', 'slug', name='uq_agents_ws_slug'),
    )
    op.create_index('ix_agents_workspace_id', 'agents', ['workspace_id'])
    op.create_index('ix_agents_project_id', 'agents', ['project_id'])
    op.create_index('ix_agents_slug', 'agents', ['slug'])
    op.create_index('ix_agents_status', 'agents', ['status'])
    op.create_index('ix_agents_ws_status', 'agents', ['workspace_id', 'status'])

    # 2. agent_versions
    op.create_table(
        'agent_versions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('agent_id', sa.String(length=36), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('instructions', sa.Text(), nullable=False),
        sa.Column('model_policy', JSONB, nullable=False),
        sa.Column('capability_policy', JSONB, nullable=False),
        sa.Column('memory_policy', JSONB, nullable=False),
        sa.Column('knowledge_policy', JSONB, nullable=False),
        sa.Column('execution_policy', JSONB, nullable=False),
        sa.Column('evaluation_policy', JSONB, nullable=False),
        sa.Column('approval_policy', JSONB, nullable=False),
        sa.Column('budget_policy', JSONB, nullable=False),
        sa.Column('configuration', JSONB, nullable=False),
        sa.Column('created_by', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deprecated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('agent_id', 'version', name='uq_agent_versions_agent_ver'),
    )
    op.create_index('ix_agent_versions_agent_id', 'agent_versions', ['agent_id'])

    # 3. agent_runs
    op.create_table(
        'agent_runs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('agent_id', sa.String(length=36), nullable=False),
        sa.Column('agent_version_id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=True),
        sa.Column('initiated_by', sa.String(length=36), nullable=False),
        sa.Column('parent_agent_run_id', sa.String(length=36), nullable=True),
        sa.Column('task_id', sa.String(length=36), nullable=True),
        sa.Column('workflow_run_id', sa.String(length=36), nullable=True),
        sa.Column('collaboration_session_id', sa.String(length=36), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='created'),
        sa.Column('input_snapshot', JSONB, nullable=False),
        sa.Column('output', JSONB, nullable=True),
        sa.Column('execution_state', JSONB, nullable=False),
        sa.Column('steps_executed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('delegations_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('tool_calls_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('connector_calls_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('tokens', JSONB, nullable=False),
        sa.Column('cost', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('latency', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error', JSONB, nullable=True),
        sa.Column('reproducibility_metadata', JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_version_id'], ['agent_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_agent_runs_agent_id', 'agent_runs', ['agent_id'])
    op.create_index('ix_agent_runs_agent_version_id', 'agent_runs', ['agent_version_id'])
    op.create_index('ix_agent_runs_workspace_id', 'agent_runs', ['workspace_id'])
    op.create_index('ix_agent_runs_project_id', 'agent_runs', ['project_id'])
    op.create_index('ix_agent_runs_parent_agent_run_id', 'agent_runs', ['parent_agent_run_id'])
    op.create_index('ix_agent_runs_task_id', 'agent_runs', ['task_id'])
    op.create_index('ix_agent_runs_workflow_run_id', 'agent_runs', ['workflow_run_id'])
    op.create_index('ix_agent_runs_collaboration_session_id', 'agent_runs', ['collaboration_session_id'])
    op.create_index('ix_agent_runs_status', 'agent_runs', ['status'])
    op.create_index('ix_agent_runs_created_at', 'agent_runs', ['created_at'])

    # 4. agent_delegations
    op.create_table(
        'agent_delegations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('parent_agent_run_id', sa.String(length=36), nullable=False),
        sa.Column('parent_agent_id', sa.String(length=36), nullable=False),
        sa.Column('child_agent_id', sa.String(length=36), nullable=False),
        sa.Column('child_agent_version_id', sa.String(length=36), nullable=False),
        sa.Column('child_agent_run_id', sa.String(length=36), nullable=True),
        sa.Column('reason', sa.String(length=512), nullable=False),
        sa.Column('task_snapshot', JSONB, nullable=False),
        sa.Column('allowed_capabilities', JSONB, nullable=False),
        sa.Column('budget_allocation', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('depth', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['parent_agent_run_id'], ['agent_runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['child_agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['child_agent_version_id'], ['agent_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_agent_delegations_parent_run', 'agent_delegations', ['parent_agent_run_id'])
    op.create_index('ix_agent_delegations_parent_agent', 'agent_delegations', ['parent_agent_id'])
    op.create_index('ix_agent_delegations_child_agent', 'agent_delegations', ['child_agent_id'])
    op.create_index('ix_agent_delegations_child_version', 'agent_delegations', ['child_agent_version_id'])
    op.create_index('ix_agent_delegations_child_run', 'agent_delegations', ['child_agent_run_id'])
    op.create_index('ix_agent_delegations_status', 'agent_delegations', ['status'])
    op.create_index('ix_agent_delegations_created_at', 'agent_delegations', ['created_at'])

    # 5. agent_teams
    op.create_table(
        'agent_teams',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=True),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('slug', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='draft'),
        sa.Column('current_version_id', sa.String(length=36), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workspace_id', 'slug', name='uq_agent_teams_ws_slug'),
    )
    op.create_index('ix_agent_teams_workspace_id', 'agent_teams', ['workspace_id'])
    op.create_index('ix_agent_teams_project_id', 'agent_teams', ['project_id'])
    op.create_index('ix_agent_teams_slug', 'agent_teams', ['slug'])
    op.create_index('ix_agent_teams_status', 'agent_teams', ['status'])
    op.create_index('ix_agent_teams_ws_status', 'agent_teams', ['workspace_id', 'status'])

    # 6. agent_team_versions
    op.create_table(
        'agent_team_versions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('team_id', sa.String(length=36), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('objective', sa.Text(), nullable=False),
        sa.Column('coordination_policy', JSONB, nullable=False),
        sa.Column('shared_context_policy', JSONB, nullable=False),
        sa.Column('approval_policy', JSONB, nullable=False),
        sa.Column('created_by', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['team_id'], ['agent_teams.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('team_id', 'version', name='uq_agent_team_versions_team_ver'),
    )
    op.create_index('ix_agent_team_versions_team_id', 'agent_team_versions', ['team_id'])

    # 7. agent_team_members
    op.create_table(
        'agent_team_members',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('team_version_id', sa.String(length=36), nullable=False),
        sa.Column('agent_id', sa.String(length=36), nullable=False),
        sa.Column('agent_version_id', sa.String(length=36), nullable=False),
        sa.Column('role', sa.String(length=64), nullable=False, server_default='specialist'),
        sa.Column('capabilities', JSONB, nullable=False),
        sa.Column('responsibilities', sa.Text(), nullable=False),
        sa.Column('limits', JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['team_version_id'], ['agent_team_versions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_version_id'], ['agent_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_agent_team_members_team_version_id', 'agent_team_members', ['team_version_id'])
    op.create_index('ix_agent_team_members_agent_id', 'agent_team_members', ['agent_id'])
    op.create_index('ix_agent_team_members_agent_version_id', 'agent_team_members', ['agent_version_id'])

    # 8. agent_team_runs
    op.create_table(
        'agent_team_runs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('team_id', sa.String(length=36), nullable=False),
        sa.Column('team_version_id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=True),
        sa.Column('initiated_by', sa.String(length=36), nullable=False),
        sa.Column('objective', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='created'),
        sa.Column('plan', JSONB, nullable=False),
        sa.Column('shared_context', JSONB, nullable=False),
        sa.Column('final_synthesis', JSONB, nullable=True),
        sa.Column('cost', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('latency', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error', JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['team_id'], ['agent_teams.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['team_version_id'], ['agent_team_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_agent_team_runs_team_id', 'agent_team_runs', ['team_id'])
    op.create_index('ix_agent_team_runs_team_version_id', 'agent_team_runs', ['team_version_id'])
    op.create_index('ix_agent_team_runs_workspace_id', 'agent_team_runs', ['workspace_id'])
    op.create_index('ix_agent_team_runs_project_id', 'agent_team_runs', ['project_id'])
    op.create_index('ix_agent_team_runs_status', 'agent_team_runs', ['status'])
    op.create_index('ix_agent_team_runs_created_at', 'agent_team_runs', ['created_at'])

    # 9. agent_messages
    op.create_table(
        'agent_messages',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('team_run_id', sa.String(length=36), nullable=False),
        sa.Column('sender_agent_id', sa.String(length=36), nullable=False),
        sa.Column('recipient_agent_id', sa.String(length=36), nullable=True),
        sa.Column('message_type', sa.String(length=64), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata', JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['team_run_id'], ['agent_team_runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sender_agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_agent_messages_team_run_id', 'agent_messages', ['team_run_id'])
    op.create_index('ix_agent_messages_sender_agent_id', 'agent_messages', ['sender_agent_id'])
    op.create_index('ix_agent_messages_recipient_agent_id', 'agent_messages', ['recipient_agent_id'])
    op.create_index('ix_agent_messages_message_type', 'agent_messages', ['message_type'])
    op.create_index('ix_agent_messages_created_at', 'agent_messages', ['created_at'])

    # 10. agent_conflicts
    op.create_table(
        'agent_conflicts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('team_run_id', sa.String(length=36), nullable=False),
        sa.Column('subject', sa.String(length=256), nullable=False),
        sa.Column('agent_a_id', sa.String(length=36), nullable=False),
        sa.Column('agent_b_id', sa.String(length=36), nullable=False),
        sa.Column('position_a', sa.Text(), nullable=False),
        sa.Column('position_b', sa.Text(), nullable=False),
        sa.Column('evidence_a', JSONB, nullable=False),
        sa.Column('evidence_b', JSONB, nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='open'),
        sa.Column('resolution', sa.Text(), nullable=True),
        sa.Column('resolved_by', sa.String(length=36), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['team_run_id'], ['agent_team_runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_a_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_b_id'], ['agents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_agent_conflicts_team_run_id', 'agent_conflicts', ['team_run_id'])
    op.create_index('ix_agent_conflicts_agent_a_id', 'agent_conflicts', ['agent_a_id'])
    op.create_index('ix_agent_conflicts_agent_b_id', 'agent_conflicts', ['agent_b_id'])
    op.create_index('ix_agent_conflicts_status', 'agent_conflicts', ['status'])
    op.create_index('ix_agent_conflicts_created_at', 'agent_conflicts', ['created_at'])


def downgrade() -> None:
    op.drop_table('agent_conflicts')
    op.drop_table('agent_messages')
    op.drop_table('agent_team_runs')
    op.drop_table('agent_team_members')
    op.drop_table('agent_team_versions')
    op.drop_table('agent_teams')
    op.drop_table('agent_delegations')
    op.drop_table('agent_runs')
    op.drop_table('agent_versions')
    op.drop_table('agents')
