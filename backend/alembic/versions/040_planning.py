"""create work_plans, work_plan_versions, planning_items, planning_dependencies, work_resources, resource_availability, capacity_snapshots, capacity_reservations, planning_constraints, schedule_candidates, planning_blockers, planning_scenarios, planning_recommendations, plan_staleness_records

Revision ID: 040
Revises: 039
Create Date: 2026-10-07 01:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

JSONB = sa.JSON().with_variant(postgresql.JSONB, "postgresql")

# revision identifiers, used by Alembic.
revision: str = '040'
down_revision: Union[str, None] = '039'
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None


def upgrade() -> None:
    # 1. work_plans
    op.create_table(
        'work_plans',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=True),
        sa.Column('objective_id', sa.String(length=36), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='draft'),
        sa.Column('planning_mode', sa.String(length=32), nullable=False, server_default='assisted'),
        sa.Column('planning_horizon_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('planning_horizon_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_work_plans_workspace_id', 'work_plans', ['workspace_id'])
    op.create_index('ix_work_plans_project_id', 'work_plans', ['project_id'])
    op.create_index('ix_work_plans_objective_id', 'work_plans', ['objective_id'])
    op.create_index('ix_work_plans_status', 'work_plans', ['status'])
    op.create_index('ix_work_plans_created_at', 'work_plans', ['created_at'])
    op.create_index('ix_work_plans_ws_status', 'work_plans', ['workspace_id', 'status'])

    # 2. work_plan_versions
    op.create_table(
        'work_plan_versions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('work_plan_id', sa.String(length=36), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('plan_snapshot', JSONB, nullable=False, server_default='{}'),
        sa.Column('constraint_snapshot', JSONB, nullable=False, server_default='{}'),
        sa.Column('capacity_snapshot', JSONB, nullable=False, server_default='{}'),
        sa.Column('resource_snapshot', JSONB, nullable=False, server_default='{}'),
        sa.Column('created_by', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['work_plan_id'], ['work_plans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('work_plan_id', 'version', name='uq_work_plan_version'),
    )
    op.create_index('ix_work_plan_versions_work_plan_id', 'work_plan_versions', ['work_plan_id'])
    op.create_index('ix_work_plan_versions_created_at', 'work_plan_versions', ['created_at'])

    # 3. planning_items
    op.create_table(
        'planning_items',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('work_plan_version_id', sa.String(length=36), nullable=False),
        sa.Column('resource_type', sa.String(length=64), nullable=False),
        sa.Column('resource_id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('priority', sa.String(length=32), nullable=False, server_default='medium'),
        sa.Column('estimated_duration', sa.Integer(), nullable=True),
        sa.Column('estimated_cost', sa.Float(), nullable=True),
        sa.Column('required_capabilities', JSONB, nullable=False, server_default='[]'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='planned'),
        sa.Column('planned_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('planned_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['work_plan_version_id'], ['work_plan_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_planning_items_version_id', 'planning_items', ['work_plan_version_id'])
    op.create_index('ix_planning_items_resource_type', 'planning_items', ['resource_type'])
    op.create_index('ix_planning_items_resource_id', 'planning_items', ['resource_id'])
    op.create_index('ix_planning_items_status', 'planning_items', ['status'])

    # 4. planning_dependencies
    op.create_table(
        'planning_dependencies',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('work_plan_version_id', sa.String(length=36), nullable=False),
        sa.Column('predecessor_item_id', sa.String(length=36), nullable=False),
        sa.Column('successor_item_id', sa.String(length=36), nullable=False),
        sa.Column('dependency_type', sa.String(length=32), nullable=False, server_default='finish_to_start'),
        sa.Column('lag', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['work_plan_version_id'], ['work_plan_versions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['predecessor_item_id'], ['planning_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['successor_item_id'], ['planning_items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_planning_dep_version_id', 'planning_dependencies', ['work_plan_version_id'])
    op.create_index('ix_planning_dep_predecessor', 'planning_dependencies', ['predecessor_item_id'])
    op.create_index('ix_planning_dep_successor', 'planning_dependencies', ['successor_item_id'])

    # 5. work_resources
    op.create_table(
        'work_resources',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=True),
        sa.Column('resource_type', sa.String(length=32), nullable=False),
        sa.Column('resource_ref', sa.String(64), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='active'),
        sa.Column('capabilities', JSONB, nullable=False, server_default='[]'),
        sa.Column('availability_policy', JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_work_resources_workspace_id', 'work_resources', ['workspace_id'])
    op.create_index('ix_work_resources_project_id', 'work_resources', ['project_id'])
    op.create_index('ix_work_resources_type', 'work_resources', ['resource_type'])
    op.create_index('ix_work_resources_ref', 'work_resources', ['resource_ref'])
    op.create_index('ix_work_resources_status', 'work_resources', ['status'])

    # 6. resource_availability
    op.create_table(
        'resource_availability',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('resource_id', sa.String(length=36), nullable=False),
        sa.Column('start_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('capacity_units', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('reserved_units', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('source', sa.String(length=32), nullable=False, server_default='manual'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['resource_id'], ['work_resources.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_res_avail_resource_id', 'resource_availability', ['resource_id'])
    op.create_index('ix_res_avail_start_at', 'resource_availability', ['start_at'])
    op.create_index('ix_res_avail_end_at', 'resource_availability', ['end_at'])

    # 7. capacity_snapshots
    op.create_table(
        'capacity_snapshots',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=True),
        sa.Column('resource_id', sa.String(length=36), nullable=False),
        sa.Column('snapshot_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('available_units', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('reserved_units', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('allocated_units', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('remaining_units', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('source', sa.String(length=32), nullable=False, server_default='system'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['resource_id'], ['work_resources.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_cap_snapshots_workspace_id', 'capacity_snapshots', ['workspace_id'])
    op.create_index('ix_cap_snapshots_resource_id', 'capacity_snapshots', ['resource_id'])
    op.create_index('ix_cap_snapshots_period_start', 'capacity_snapshots', ['period_start'])
    op.create_index('ix_cap_snapshots_period_end', 'capacity_snapshots', ['period_end'])

    # 8. capacity_reservations
    op.create_table(
        'capacity_reservations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('resource_id', sa.String(length=36), nullable=False),
        sa.Column('planning_item_id', sa.String(length=36), nullable=True),
        sa.Column('start_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('units', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='proposed'),
        sa.Column('created_by', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['resource_id'], ['work_resources.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['planning_item_id'], ['planning_items.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_cap_res_resource_id', 'capacity_reservations', ['resource_id'])
    op.create_index('ix_cap_res_item_id', 'capacity_reservations', ['planning_item_id'])
    op.create_index('ix_cap_res_status', 'capacity_reservations', ['status'])
    op.create_index('ix_cap_res_start_at', 'capacity_reservations', ['start_at'])
    op.create_index('ix_cap_res_end_at', 'capacity_reservations', ['end_at'])

    # 9. planning_constraints
    op.create_table(
        'planning_constraints',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('work_plan_version_id', sa.String(length=36), nullable=False),
        sa.Column('constraint_type', sa.String(length=32), nullable=False),
        sa.Column('configuration', JSONB, nullable=False, server_default='{}'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('hard_constraint', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['work_plan_version_id'], ['work_plan_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_planning_constraints_version_id', 'planning_constraints', ['work_plan_version_id'])
    op.create_index('ix_planning_constraints_type', 'planning_constraints', ['constraint_type'])

    # 10. schedule_candidates
    op.create_table(
        'schedule_candidates',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('work_plan_version_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('schedule', JSONB, nullable=False, server_default='{}'),
        sa.Column('assumptions', JSONB, nullable=False, server_default='[]'),
        sa.Column('constraint_results', JSONB, nullable=False, server_default='{}'),
        sa.Column('resource_allocations', JSONB, nullable=False, server_default='{}'),
        sa.Column('estimated_duration', sa.Float(), nullable=True),
        sa.Column('estimated_cost', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['work_plan_version_id'], ['work_plan_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_schedule_candidates_version_id', 'schedule_candidates', ['work_plan_version_id'])

    # 11. planning_blockers
    op.create_table(
        'planning_blockers',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('work_plan_version_id', sa.String(length=36), nullable=False),
        sa.Column('planning_item_id', sa.String(length=36), nullable=True),
        sa.Column('type', sa.String(length=32), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(length=32), nullable=False, server_default='medium'),
        sa.Column('evidence_ids', JSONB, nullable=False, server_default='[]'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='open'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['work_plan_version_id'], ['work_plan_versions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['planning_item_id'], ['planning_items.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_planning_blockers_version_id', 'planning_blockers', ['work_plan_version_id'])
    op.create_index('ix_planning_blockers_item_id', 'planning_blockers', ['planning_item_id'])
    op.create_index('ix_planning_blockers_status', 'planning_blockers', ['status'])

    # 12. planning_scenarios
    op.create_table(
        'planning_scenarios',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('work_plan_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('modifications', JSONB, nullable=False, server_default='{}'),
        sa.Column('simulation_results', JSONB, nullable=False, server_default='{}'),
        sa.Column('comparison', JSONB, nullable=False, server_default='{}'),
        sa.Column('created_by', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['work_plan_id'], ['work_plans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_planning_scenarios_workspace_id', 'planning_scenarios', ['workspace_id'])
    op.create_index('ix_planning_scenarios_plan_id', 'planning_scenarios', ['work_plan_id'])

    # 13. planning_recommendations
    op.create_table(
        'planning_recommendations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('work_plan_id', sa.String(length=36), nullable=False),
        sa.Column('recommendation_type', sa.String(length=64), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('evidence_ids', JSONB, nullable=False, server_default='[]'),
        sa.Column('affected_resources', JSONB, nullable=False, server_default='[]'),
        sa.Column('affected_items', JSONB, nullable=False, server_default='[]'),
        sa.Column('risk', sa.Text(), nullable=True),
        sa.Column('assumptions', JSONB, nullable=False, server_default='[]'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='proposed'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['work_plan_id'], ['work_plans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_plan_rec_workspace_id', 'planning_recommendations', ['workspace_id'])
    op.create_index('ix_plan_rec_plan_id', 'planning_recommendations', ['work_plan_id'])
    op.create_index('ix_plan_rec_status', 'planning_recommendations', ['status'])

    # 14. plan_staleness_records
    op.create_table(
        'plan_staleness_records',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('work_plan_id', sa.String(length=36), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_stale', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['work_plan_id'], ['work_plans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_plan_stale_plan_id', 'plan_staleness_records', ['work_plan_id'])
    op.create_index('ix_plan_stale_is_stale', 'plan_staleness_records', ['is_stale'])


def downgrade() -> None:
    op.drop_table('plan_staleness_records')
    op.drop_table('planning_recommendations')
    op.drop_table('planning_scenarios')
    op.drop_table('planning_blockers')
    op.drop_table('schedule_candidates')
    op.drop_table('planning_constraints')
    op.drop_table('capacity_reservations')
    op.drop_table('capacity_snapshots')
    op.drop_table('resource_availability')
    op.drop_table('work_resources')
    op.drop_table('planning_dependencies')
    op.drop_table('planning_items')
    op.drop_table('work_plan_versions')
    op.drop_table('work_plans')
