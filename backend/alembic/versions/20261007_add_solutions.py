"""add solutions

Revision ID: add_solutions_step_49
Revises: add_service_catalog_step_48
Create Date: 2026-10-07 23:50:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_solutions_step_49'
down_revision = 'add_service_catalog_step_48'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create solutions table
    op.create_table(
        'solutions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('workspace_id', sa.String(36), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id'), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('objective', sa.Text, nullable=True),
        sa.Column('status', sa.String(50), nullable=False, default='draft'),
        sa.Column('visibility', sa.String(50), nullable=False, default='workspace'),
        sa.Column('owner_type', sa.String(50), nullable=False),
        sa.Column('owner_id', sa.String(36), nullable=False),
        sa.Column('current_version_id', sa.String(36), nullable=True), # Will add foreign key later to avoid circular dependency
        sa.Column('created_by', sa.String(36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Create solution_versions table
    op.create_table(
        'solution_versions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('solution_id', sa.String(36), sa.ForeignKey('solutions.id'), nullable=False),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, default='draft'),
        sa.Column('objective', sa.Text, nullable=True),
        sa.Column('inputs_schema', sa.JSON, nullable=True),
        sa.Column('outputs_schema', sa.JSON, nullable=True),
        sa.Column('constraints', sa.JSON, nullable=False),
        sa.Column('requirements', sa.JSON, nullable=False),
        sa.Column('created_by', sa.String(36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deprecated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_immutable', sa.Boolean, nullable=False, default=False),
    )

    # Add FK back to solutions.current_version_id
    op.create_foreign_key('fk_solutions_current_version_id', 'solutions', 'solution_versions', ['current_version_id'], ['id'])

    # Create solution_components table
    op.create_table(
        'solution_components',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('solution_version_id', sa.String(36), sa.ForeignKey('solution_versions.id'), nullable=False),
        sa.Column('catalog_item_id', sa.String(36), nullable=False),
        sa.Column('component_key', sa.String(100), nullable=False),
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('component_type', sa.String(50), nullable=False),
        sa.Column('configuration', sa.JSON, nullable=False),
        sa.Column('position', sa.JSON, nullable=False),
        sa.Column('input_mapping', sa.JSON, nullable=False),
        sa.Column('output_mapping', sa.JSON, nullable=False),
        sa.Column('required', sa.Boolean, nullable=False, default=True),
        sa.Column('optional', sa.Boolean, nullable=False, default=False),
        sa.Column('condition', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Create solution_connections table
    op.create_table(
        'solution_connections',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('solution_version_id', sa.String(36), sa.ForeignKey('solution_versions.id'), nullable=False),
        sa.Column('source_component_id', sa.String(36), sa.ForeignKey('solution_components.id'), nullable=False),
        sa.Column('source_port', sa.String(100), nullable=False),
        sa.Column('target_component_id', sa.String(36), sa.ForeignKey('solution_components.id'), nullable=False),
        sa.Column('target_port', sa.String(100), nullable=False),
        sa.Column('mapping', sa.JSON, nullable=False),
        sa.Column('condition', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Create solution_inputs table
    op.create_table(
        'solution_inputs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('solution_version_id', sa.String(36), sa.ForeignKey('solution_versions.id'), nullable=False),
        sa.Column('key', sa.String(100), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('data_type', sa.String(50), nullable=False),
        sa.Column('schema', sa.JSON, nullable=True),
        sa.Column('required', sa.Boolean, nullable=False, default=True),
        sa.Column('default_value', sa.JSON, nullable=True),
        sa.Column('sensitivity', sa.String(50), nullable=False, default='public'),
        sa.Column('validation_rules', sa.JSON, nullable=False),
    )

    # Create solution_outputs table
    op.create_table(
        'solution_outputs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('solution_version_id', sa.String(36), sa.ForeignKey('solution_versions.id'), nullable=False),
        sa.Column('key', sa.String(100), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('data_type', sa.String(50), nullable=False),
        sa.Column('schema', sa.JSON, nullable=True),
        sa.Column('required', sa.Boolean, nullable=False, default=True),
        sa.Column('evidence_required', sa.Boolean, nullable=False, default=False),
        sa.Column('acceptance_criteria', sa.JSON, nullable=False),
    )

    # Create solution_requirements table
    op.create_table(
        'solution_requirements',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('solution_version_id', sa.String(36), sa.ForeignKey('solution_versions.id'), nullable=False),
        sa.Column('requirement_type', sa.String(50), nullable=False),
        sa.Column('value', sa.JSON, nullable=False),
        sa.Column('source', sa.String(100), nullable=False),
        sa.Column('required', sa.Boolean, nullable=False, default=True),
        sa.Column('reason', sa.Text, nullable=True),
    )

    op.create_index('ix_solutions_org', 'solutions', ['organization_id'])
    op.create_index('ix_solutions_workspace', 'solutions', ['workspace_id'])
    op.create_index('ix_solution_versions_solution', 'solution_versions', ['solution_id'])
    op.create_index('ix_solution_components_catalog', 'solution_components', ['catalog_item_id'])

def downgrade() -> None:
    op.drop_index('ix_solution_components_catalog', table_name='solution_components')
    op.drop_index('ix_solution_versions_solution', table_name='solution_versions')
    op.drop_index('ix_solutions_workspace', table_name='solutions')
    op.drop_index('ix_solutions_org', table_name='solutions')
    
    op.drop_table('solution_requirements')
    op.drop_table('solution_outputs')
    op.drop_table('solution_inputs')
    op.drop_table('solution_connections')
    op.drop_table('solution_components')
    
    op.drop_constraint('fk_solutions_current_version_id', 'solutions', type_='foreignkey')
    
    op.drop_table('solution_versions')
    op.drop_table('solutions')
