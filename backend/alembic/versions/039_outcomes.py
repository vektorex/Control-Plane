"""create objectives, outcome_targets, outcomes, outcome_work_links, outcome_evidence, outcome_measurements, outcome_milestones, work_decisions, outcome_attributions, impact_analyses, outcome_health_records

Revision ID: 039
Revises: 038
Create Date: 2026-10-06 20:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

JSONB = sa.JSON().with_variant(postgresql.JSONB, "postgresql")

# revision identifiers, used by Alembic.
revision: str = '039'
down_revision: Union[str, None] = '038'
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None


def upgrade() -> None:
    # 1. objectives
    op.create_table(
        'objectives',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('objective_type', sa.String(length=32), nullable=False, server_default='business'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='draft'),
        sa.Column('priority', sa.String(length=32), nullable=False, server_default='medium'),
        sa.Column('owner_user_id', sa.String(length=36), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=False),
        sa.Column('requirements', JSONB, nullable=False, server_default='{}'),
        sa.Column('start_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('target_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_objectives_workspace_id', 'objectives', ['workspace_id'])
    op.create_index('ix_objectives_project_id', 'objectives', ['project_id'])
    op.create_index('ix_objectives_status', 'objectives', ['status'])
    op.create_index('ix_objectives_objective_type', 'objectives', ['objective_type'])
    op.create_index('ix_objectives_owner_user_id', 'objectives', ['owner_user_id'])
    op.create_index('ix_objectives_created_at', 'objectives', ['created_at'])
    op.create_index('ix_objectives_ws_status', 'objectives', ['workspace_id', 'status'])
    op.create_index('ix_objectives_ws_priority', 'objectives', ['workspace_id', 'priority'])

    # 2. outcome_targets
    op.create_table(
        'outcome_targets',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('objective_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metric_type', sa.String(length=32), nullable=False, server_default='count'),
        sa.Column('target_value', sa.Float(), nullable=True),
        sa.Column('target_unit', sa.String(length=64), nullable=True),
        sa.Column('baseline_value', sa.Float(), nullable=True),
        sa.Column('current_value', sa.Float(), nullable=True),
        sa.Column('target_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('measurement_source', sa.String(length=64), nullable=False, server_default='system'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='planned'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['objective_id'], ['objectives.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_outcome_targets_objective_id', 'outcome_targets', ['objective_id'])
    op.create_index('ix_outcome_targets_status', 'outcome_targets', ['status'])

    # 3. outcomes
    op.create_table(
        'outcomes',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=True),
        sa.Column('objective_id', sa.String(length=36), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('outcome_type', sa.String(length=64), nullable=False, server_default='deliverable'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='planned'),
        sa.Column('confidence', sa.String(length=32), nullable=False, server_default='unverified'),
        sa.Column('owner_user_id', sa.String(length=36), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=False),
        sa.Column('requirements', JSONB, nullable=False, server_default='{}'),
        sa.Column('observed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verified_by', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['objective_id'], ['objectives.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_outcomes_workspace_id', 'outcomes', ['workspace_id'])
    op.create_index('ix_outcomes_project_id', 'outcomes', ['project_id'])
    op.create_index('ix_outcomes_objective_id', 'outcomes', ['objective_id'])
    op.create_index('ix_outcomes_status', 'outcomes', ['status'])
    op.create_index('ix_outcomes_outcome_type', 'outcomes', ['outcome_type'])
    op.create_index('ix_outcomes_created_at', 'outcomes', ['created_at'])
    op.create_index('ix_outcomes_ws_status', 'outcomes', ['workspace_id', 'status'])
    op.create_index('ix_outcomes_ws_type', 'outcomes', ['workspace_id', 'outcome_type'])

    # 4. outcome_work_links
    op.create_table(
        'outcome_work_links',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('outcome_id', sa.String(length=36), nullable=False),
        sa.Column('resource_type', sa.String(length=64), nullable=False),
        sa.Column('resource_id', sa.String(length=255), nullable=False),
        sa.Column('relationship_type', sa.String(length=64), nullable=False, server_default='contributes_to'),
        sa.Column('evidence_ids', JSONB, nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['outcome_id'], ['outcomes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_outcome_work_links_outcome_id', 'outcome_work_links', ['outcome_id'])
    op.create_index('ix_outcome_work_links_resource_id', 'outcome_work_links', ['resource_id'])
    op.create_index('ix_outcome_work_links_res', 'outcome_work_links', ['resource_type', 'resource_id'])

    # 5. outcome_evidence
    op.create_table(
        'outcome_evidence',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('outcome_id', sa.String(length=36), nullable=False),
        sa.Column('source_type', sa.String(length=64), nullable=False),
        sa.Column('source_id', sa.String(length=255), nullable=False),
        sa.Column('evidence_type', sa.String(length=64), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('snapshot', JSONB, nullable=False, server_default='{}'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='unreviewed'),
        sa.Column('is_human_confirmed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_ai_generated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('observed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['outcome_id'], ['outcomes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_outcome_evidence_outcome_id', 'outcome_evidence', ['outcome_id'])
    op.create_index('ix_outcome_evidence_status', 'outcome_evidence', ['status'])
    op.create_index('ix_outcome_evidence_created_at', 'outcome_evidence', ['created_at'])

    # 6. outcome_measurements
    op.create_table(
        'outcome_measurements',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('outcome_id', sa.String(length=36), nullable=False),
        sa.Column('target_id', sa.String(length=36), nullable=True),
        sa.Column('metric_name', sa.String(length=128), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=64), nullable=False),
        sa.Column('measurement_source', sa.String(length=64), nullable=False),
        sa.Column('observed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('evidence_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['outcome_id'], ['outcomes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_id'], ['outcome_targets.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_outcome_measurements_outcome_id', 'outcome_measurements', ['outcome_id'])
    op.create_index('ix_outcome_measurements_target_id', 'outcome_measurements', ['target_id'])
    op.create_index('ix_outcome_measurements_created_at', 'outcome_measurements', ['created_at'])

    # 7. outcome_milestones
    op.create_table(
        'outcome_milestones',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('objective_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='planned'),
        sa.Column('due_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('owner_user_id', sa.String(length=36), nullable=True),
        sa.Column('connected_resource_type', sa.String(length=64), nullable=True),
        sa.Column('connected_resource_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['objective_id'], ['objectives.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_outcome_milestones_objective_id', 'outcome_milestones', ['objective_id'])
    op.create_index('ix_outcome_milestones_status', 'outcome_milestones', ['status'])

    # 8. work_decisions
    op.create_table(
        'work_decisions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=True),
        sa.Column('objective_id', sa.String(length=36), nullable=True),
        sa.Column('outcome_id', sa.String(length=36), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('decision_type', sa.String(length=32), nullable=False, server_default='human'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='proposed'),
        sa.Column('decision_owner', sa.String(length=255), nullable=False),
        sa.Column('evidence_ids', JSONB, nullable=False, server_default='[]'),
        sa.Column('provenance', JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_work_decisions_workspace_id', 'work_decisions', ['workspace_id'])
    op.create_index('ix_work_decisions_project_id', 'work_decisions', ['project_id'])
    op.create_index('ix_work_decisions_objective_id', 'work_decisions', ['objective_id'])
    op.create_index('ix_work_decisions_outcome_id', 'work_decisions', ['outcome_id'])
    op.create_index('ix_work_decisions_status', 'work_decisions', ['status'])
    op.create_index('ix_work_decisions_created_at', 'work_decisions', ['created_at'])
    op.create_index('ix_work_decisions_ws_status', 'work_decisions', ['workspace_id', 'status'])

    # 9. outcome_attributions
    op.create_table(
        'outcome_attributions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('outcome_id', sa.String(length=36), nullable=False),
        sa.Column('resource_type', sa.String(length=64), nullable=False),
        sa.Column('resource_id', sa.String(length=255), nullable=False),
        sa.Column('attribution_type', sa.String(length=32), nullable=False, server_default='contributing'),
        sa.Column('evidence_ids', JSONB, nullable=False, server_default='[]'),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('attribution_source', sa.String(length=32), nullable=False, server_default='deterministic'),
        sa.Column('attribution_confidence', sa.String(length=32), nullable=False, server_default='inferred'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['outcome_id'], ['outcomes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_outcome_attributions_outcome_id', 'outcome_attributions', ['outcome_id'])
    op.create_index('ix_outcome_attributions_resource_id', 'outcome_attributions', ['resource_id'])

    # 10. impact_analyses
    op.create_table(
        'impact_analyses',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('outcome_id', sa.String(length=36), nullable=False),
        sa.Column('analysis_type', sa.String(length=32), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('evidence_ids', JSONB, nullable=False, server_default='[]'),
        sa.Column('observations', JSONB, nullable=False, server_default='[]'),
        sa.Column('limitations', sa.Text(), nullable=True),
        sa.Column('attribution_confidence', sa.String(length=32), nullable=False, server_default='observed'),
        sa.Column('baseline_value', sa.Float(), nullable=True),
        sa.Column('observed_value', sa.Float(), nullable=True),
        sa.Column('difference_value', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['outcome_id'], ['outcomes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_impact_analyses_outcome_id', 'impact_analyses', ['outcome_id'])

    # 11. outcome_health_records
    op.create_table(
        'outcome_health_records',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('objective_id', sa.String(length=36), nullable=True),
        sa.Column('outcome_id', sa.String(length=36), nullable=True),
        sa.Column('health_status', sa.String(length=32), nullable=False, server_default='healthy'),
        sa.Column('reasons', JSONB, nullable=False, server_default='[]'),
        sa.Column('checked_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_outcome_health_records_objective_id', 'outcome_health_records', ['objective_id'])
    op.create_index('ix_outcome_health_records_outcome_id', 'outcome_health_records', ['outcome_id'])

    # 12. Add nullable outcome references to tasks table
    try:
        op.add_column('tasks', sa.Column('objective_id', sa.String(length=36), nullable=True))
        op.add_column('tasks', sa.Column('outcome_id', sa.String(length=36), nullable=True))
        op.add_column('tasks', sa.Column('milestone_id', sa.String(length=36), nullable=True))
        op.create_index('ix_tasks_objective_id', 'tasks', ['objective_id'])
        op.create_index('ix_tasks_outcome_id', 'tasks', ['outcome_id'])
        op.create_index('ix_tasks_milestone_id', 'tasks', ['milestone_id'])
    except Exception:
        pass


def downgrade() -> None:
    try:
        op.drop_index('ix_tasks_milestone_id', 'tasks')
        op.drop_index('ix_tasks_outcome_id', 'tasks')
        op.drop_index('ix_tasks_objective_id', 'tasks')
        op.drop_column('tasks', 'milestone_id')
        op.drop_column('tasks', 'outcome_id')
        op.drop_column('tasks', 'objective_id')
    except Exception:
        pass

    op.drop_table('outcome_health_records')
    op.drop_table('impact_analyses')
    op.drop_table('outcome_attributions')
    op.drop_table('work_decisions')
    op.drop_table('outcome_milestones')
    op.drop_table('outcome_measurements')
    op.drop_table('outcome_evidence')
    op.drop_table('outcome_work_links')
    op.drop_table('outcomes')
    op.drop_table('outcome_targets')
    op.drop_table('objectives')
