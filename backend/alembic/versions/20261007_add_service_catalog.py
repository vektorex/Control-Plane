"""add service catalog

Revision ID: add_service_catalog_step_48
Revises: add_work_contracts_step_47
Create Date: 2026-10-07 23:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_service_catalog_step_48'
down_revision = 'add_work_contracts_step_47'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create service_catalog_items
    op.create_table(
        'service_catalog_items',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('workspace_id', sa.String(36), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id'), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('resource_id', sa.String(36), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('subcategory', sa.String(100), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, default='draft'),
        sa.Column('visibility', sa.String(50), nullable=False, default='workspace'),
        sa.Column('owner_type', sa.String(50), nullable=False),
        sa.Column('owner_id', sa.String(36), nullable=False),
        sa.Column('version_reference', sa.String(50), nullable=True),
        sa.Column('capability_summary', sa.JSON, nullable=False),
        sa.Column('input_schema', sa.JSON, nullable=True),
        sa.Column('output_schema', sa.JSON, nullable=True),
        sa.Column('requirements', sa.JSON, nullable=False),
        sa.Column('supported_modes', sa.JSON, nullable=False),
        sa.Column('supported_modalities', sa.JSON, nullable=False),
        sa.Column('supported_data_classes', sa.JSON, nullable=False),
        sa.Column('required_permissions', sa.JSON, nullable=False),
        sa.Column('required_tools', sa.JSON, nullable=False),
        sa.Column('required_connectors', sa.JSON, nullable=False),
        sa.Column('required_models', sa.JSON, nullable=False),
        sa.Column('dependency_summary', sa.JSON, nullable=False),
        sa.Column('availability_status', sa.String(50), nullable=False, default='unknown'),
        sa.Column('eligibility_status', sa.String(50), nullable=False, default='unknown'),
        sa.Column('quality_evidence_summary', sa.JSON, nullable=False),
        sa.Column('sla_reference', sa.JSON, nullable=True),
        sa.Column('documentation_reference', sa.JSON, nullable=True),
        sa.Column('provenance', sa.JSON, nullable=False),
        sa.Column('freshness_status', sa.String(50), nullable=False, default='unknown'),
        sa.Column('last_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    op.create_index('ix_service_catalog_items_org', 'service_catalog_items', ['organization_id'])
    op.create_index('ix_service_catalog_items_workspace', 'service_catalog_items', ['workspace_id'])
    op.create_index('ix_service_catalog_items_resource', 'service_catalog_items', ['resource_type', 'resource_id'])
    op.create_index('ix_service_catalog_items_category', 'service_catalog_items', ['category'])
    op.create_index('ix_service_catalog_items_status', 'service_catalog_items', ['status'])

def downgrade() -> None:
    op.drop_index('ix_service_catalog_items_status', table_name='service_catalog_items')
    op.drop_index('ix_service_catalog_items_category', table_name='service_catalog_items')
    op.drop_index('ix_service_catalog_items_resource', table_name='service_catalog_items')
    op.drop_index('ix_service_catalog_items_workspace', table_name='service_catalog_items')
    op.drop_index('ix_service_catalog_items_org', table_name='service_catalog_items')
    op.drop_table('service_catalog_items')
