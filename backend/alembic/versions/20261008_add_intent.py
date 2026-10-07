"""add intent solution

Revision ID: add_intent_solution_step_50
Revises: add_solutions_step_49
Create Date: 2026-10-08 00:10:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_intent_solution_step_50'
down_revision = 'add_solutions_step_49'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create intent_requests table
    op.create_table(
        'intent_requests',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('workspace_id', sa.String(36), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id'), nullable=True),
        sa.Column('submitted_by', sa.String(36), nullable=False),
        sa.Column('raw_intent', sa.Text, nullable=False),
        sa.Column('normalized_intent', sa.Text, nullable=True),
        sa.Column('status', sa.String(50), nullable=False, default='received'),
        sa.Column('complexity', sa.String(50), nullable=False, default='unknown'),
        sa.Column('confidence', sa.Float, nullable=True),
        sa.Column('analysis', sa.JSON, nullable=False),
        sa.Column('constraints', sa.JSON, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Create intent_requirements table
    op.create_table(
        'intent_requirements',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('intent_request_id', sa.String(36), sa.ForeignKey('intent_requests.id'), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('value', sa.JSON, nullable=True),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('mandatory', sa.Boolean, nullable=False, default=True),
        sa.Column('confidence', sa.Float, nullable=True),
        sa.Column('status', sa.String(50), nullable=False, default='active'),
    )

    # Create intent_clarifications table
    op.create_table(
        'intent_clarifications',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('intent_request_id', sa.String(36), sa.ForeignKey('intent_requests.id'), nullable=False),
        sa.Column('question', sa.Text, nullable=False),
        sa.Column('reason', sa.Text, nullable=False),
        sa.Column('options', sa.JSON, nullable=False),
        sa.Column('required', sa.Boolean, nullable=False, default=True),
        sa.Column('answer', sa.Text, nullable=True),
        sa.Column('answered_by', sa.String(36), nullable=True),
        sa.Column('answered_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Create intent_capability_matches table
    op.create_table(
        'intent_capability_matches',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('intent_request_id', sa.String(36), sa.ForeignKey('intent_requests.id'), nullable=False),
        sa.Column('catalog_item_id', sa.String(36), nullable=False),
        sa.Column('requirement_ids', sa.JSON, nullable=False),
        sa.Column('compatibility', sa.String(50), nullable=False),
        sa.Column('eligibility', sa.String(50), nullable=False),
        sa.Column('availability', sa.String(50), nullable=False),
        sa.Column('matched_capabilities', sa.JSON, nullable=False),
        sa.Column('missing_requirements', sa.JSON, nullable=False),
        sa.Column('incompatibilities', sa.JSON, nullable=False),
        sa.Column('evidence', sa.JSON, nullable=False),
    )

    # Create candidate_solutions table
    op.create_table(
        'candidate_solutions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('intent_request_id', sa.String(36), sa.ForeignKey('intent_requests.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('objective', sa.Text, nullable=False),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, default='draft'),
        sa.Column('solution_blueprint', sa.JSON, nullable=False),
        sa.Column('requirements', sa.JSON, nullable=False),
        sa.Column('assumptions', sa.JSON, nullable=False),
        sa.Column('validation_summary', sa.JSON, nullable=False),
        sa.Column('simulation_summary', sa.JSON, nullable=False),
        sa.Column('provenance', sa.JSON, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Create candidate_solution_evidence table
    op.create_table(
        'candidate_solution_evidence',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('candidate_id', sa.String(36), sa.ForeignKey('candidate_solutions.id'), nullable=False),
        sa.Column('evidence_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('data', sa.JSON, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    op.create_index('ix_intent_requests_org', 'intent_requests', ['organization_id'])
    op.create_index('ix_intent_requests_workspace', 'intent_requests', ['workspace_id'])
    op.create_index('ix_candidate_solutions_intent', 'candidate_solutions', ['intent_request_id'])

def downgrade() -> None:
    op.drop_index('ix_candidate_solutions_intent', table_name='candidate_solutions')
    op.drop_index('ix_intent_requests_workspace', table_name='intent_requests')
    op.drop_index('ix_intent_requests_org', table_name='intent_requests')
    
    op.drop_table('candidate_solution_evidence')
    op.drop_table('candidate_solutions')
    op.drop_table('intent_capability_matches')
    op.drop_table('intent_clarifications')
    op.drop_table('intent_requirements')
    op.drop_table('intent_requests')
