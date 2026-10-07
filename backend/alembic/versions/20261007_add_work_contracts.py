"""add work contracts

Revision ID: add_work_contracts_step_47
Revises: add_org_knowledge_step_46
Create Date: 2026-10-07 23:10:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_work_contracts_step_47'
down_revision = 'add_org_knowledge_step_46'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create work_contracts
    op.create_table(
        'work_contracts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workspace_id', sa.String(36), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id'), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('contract_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('priority', sa.String(50), nullable=True),
        sa.Column('requester_type', sa.String(50), nullable=False),
        sa.Column('requester_id', sa.String(36), nullable=False),
        sa.Column('owner_user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('objective_id', sa.String(36), sa.ForeignKey('objectives.id'), nullable=True),
        sa.Column('outcome_id', sa.String(36), sa.ForeignKey('outcomes.id'), nullable=True),
        sa.Column('plan_id', sa.String(36), sa.ForeignKey('work_plans.id'), nullable=True),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('effective_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create work_contract_versions
    op.create_table(
        'work_contract_versions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('contract_id', sa.String(36), sa.ForeignKey('work_contracts.id'), nullable=False),
        sa.Column('version', sa.Integer, nullable=False),
        sa.Column('scope_snapshot', sa.JSON, nullable=False),
        sa.Column('deliverables_snapshot', sa.JSON, nullable=False),
        sa.Column('acceptance_snapshot', sa.JSON, nullable=False),
        sa.Column('sla_snapshot', sa.JSON, nullable=False),
        sa.Column('resource_snapshot', sa.JSON, nullable=False),
        sa.Column('policy_snapshot', sa.JSON, nullable=False),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Create contract_deliverables
    op.create_table(
        'contract_deliverables',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('contract_version_id', sa.String(36), sa.ForeignKey('work_contract_versions.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('deliverable_type', sa.String(50), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=True),
        sa.Column('resource_id', sa.String(36), nullable=True),
        sa.Column('required', sa.Integer, nullable=False, default=1),
        sa.Column('status', sa.String(50), nullable=False, default='pending'),
        sa.Column('due_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Create service_level_agreements
    op.create_table(
        'service_level_agreements',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('contract_version_id', sa.String(36), sa.ForeignKey('work_contract_versions.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('metric', sa.String(50), nullable=False),
        sa.Column('target', sa.Float, nullable=False),
        sa.Column('unit', sa.String(50), nullable=False),
        sa.Column('measurement_window', sa.String(50), nullable=False),
        sa.Column('measurement_source', sa.String(50), nullable=False),
        sa.Column('start_condition', sa.JSON, nullable=False),
        sa.Column('stop_condition', sa.JSON, nullable=False),
        sa.Column('breach_threshold', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Create sla_measurements
    op.create_table(
        'sla_measurements',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('sla_id', sa.String(36), sa.ForeignKey('service_level_agreements.id'), nullable=False),
        sa.Column('contract_id', sa.String(36), sa.ForeignKey('work_contracts.id'), nullable=False),
        sa.Column('measurement_window_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('measurement_window_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('observed_value', sa.Float, nullable=True),
        sa.Column('target_value', sa.Float, nullable=False),
        sa.Column('unit', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('source_id', sa.String(36), nullable=False),
        sa.Column('evidence_ids', sa.JSON, nullable=False),
        sa.Column('measured_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

def downgrade() -> None:
    op.drop_table('sla_measurements')
    op.drop_table('service_level_agreements')
    op.drop_table('contract_deliverables')
    op.drop_table('work_contract_versions')
    op.drop_table('work_contracts')
