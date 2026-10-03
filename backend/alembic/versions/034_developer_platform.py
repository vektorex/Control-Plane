"""create developer platform, api credentials, scopes, quotas, webhooks, idempotency, and usage tables

Revision ID: 034
Revises: 033
Create Date: 2026-10-04 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '034'
down_revision: Union[str, None] = '033'
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None


def upgrade() -> None:
    # 1. developer_applications
    op.create_table(
        'developer_applications',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('environment', sa.String(length=50), nullable=False, server_default='development'),
        sa.Column('created_by', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_developer_applications_organization_id', 'developer_applications', ['organization_id'])
    op.create_index('ix_developer_applications_status', 'developer_applications', ['status'])
    op.create_index('ix_developer_applications_environment', 'developer_applications', ['environment'])
    op.create_index('ix_developer_applications_org_env', 'developer_applications', ['organization_id', 'environment'])

    # 2. api_credentials
    op.create_table(
        'api_credentials',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('application_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('key_prefix', sa.String(length=32), nullable=False),
        sa.Column('key_hash', sa.String(length=128), nullable=False),
        sa.Column('credential_type', sa.String(length=50), nullable=False, server_default='api_key'),
        sa.Column('environment', sa.String(length=50), nullable=False, server_default='development'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(['application_id'], ['developer_applications.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_api_credentials_application_id', 'api_credentials', ['application_id'])
    op.create_index('ix_api_credentials_key_prefix', 'api_credentials', ['key_prefix'])
    op.create_index('ix_api_credentials_key_hash', 'api_credentials', ['key_hash'], unique=True)
    op.create_index('ix_api_credentials_environment', 'api_credentials', ['environment'])
    op.create_index('ix_api_credentials_status', 'api_credentials', ['status'])
    op.create_index('ix_api_credentials_app_status', 'api_credentials', ['application_id', 'status'])

    # 3. api_scope_assignments
    op.create_table(
        'api_scope_assignments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('credential_id', sa.String(length=36), nullable=False),
        sa.Column('scope', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['credential_id'], ['api_credentials.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_api_scope_assignments_credential_id', 'api_scope_assignments', ['credential_id'])
    op.create_index('ix_api_scope_assignments_scope', 'api_scope_assignments', ['scope'])
    op.create_index('ix_api_scope_assignments_cred_scope', 'api_scope_assignments', ['credential_id', 'scope'], unique=True)

    # 4. api_resource_scopes
    op.create_table(
        'api_resource_scopes',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('credential_id', sa.String(length=36), nullable=False),
        sa.Column('resource_scope_type', sa.String(length=50), nullable=False, server_default='organization'),
        sa.Column('workspace_id', sa.String(length=36), nullable=True),
        sa.Column('project_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['credential_id'], ['api_credentials.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_api_resource_scopes_credential_id', 'api_resource_scopes', ['credential_id'])
    op.create_index('ix_api_resource_scopes_workspace_id', 'api_resource_scopes', ['workspace_id'])
    op.create_index('ix_api_resource_scopes_project_id', 'api_resource_scopes', ['project_id'])

    # 5. api_quotas
    op.create_table(
        'api_quotas',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('application_id', sa.String(length=36), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('limit', sa.BigInteger(), nullable=False),
        sa.Column('period', sa.String(length=50), nullable=False, server_default='minute'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['application_id'], ['developer_applications.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_api_quotas_application_id', 'api_quotas', ['application_id'])
    op.create_index('ix_api_quotas_app_resource', 'api_quotas', ['application_id', 'resource_type'], unique=True)

    # 6. api_idempotency_records
    op.create_table(
        'api_idempotency_records',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('application_id', sa.String(length=36), nullable=False),
        sa.Column('credential_id', sa.String(length=36), nullable=False),
        sa.Column('endpoint', sa.String(length=255), nullable=False),
        sa.Column('idempotency_key', sa.String(length=255), nullable=False),
        sa.Column('request_fingerprint', sa.String(length=128), nullable=False),
        sa.Column('response_reference', sa.Text(), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=False, server_default='200'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_api_idempotency_records_org_id', 'api_idempotency_records', ['organization_id'])
    op.create_index('ix_api_idempotency_records_app_id', 'api_idempotency_records', ['application_id'])
    op.create_index('ix_api_idempotency_records_key', 'api_idempotency_records', ['idempotency_key'])
    op.create_index('ix_api_idempotency_records_expires_at', 'api_idempotency_records', ['expires_at'])
    op.create_index('ix_idempotency_app_key', 'api_idempotency_records', ['application_id', 'idempotency_key'], unique=True)

    # 7. api_usage_records
    op.create_table(
        'api_usage_records',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('application_id', sa.String(length=36), nullable=False),
        sa.Column('credential_id', sa.String(length=36), nullable=False),
        sa.Column('endpoint', sa.String(length=255), nullable=False),
        sa.Column('method', sa.String(length=10), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=False),
        sa.Column('request_bytes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('response_bytes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('latency_ms', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('tokens', sa.Integer(), nullable=True),
        sa.Column('cost', sa.Float(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('request_id', sa.String(length=64), nullable=False),
        sa.Column('run_id', sa.String(length=36), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_api_usage_records_org_id', 'api_usage_records', ['organization_id'])
    op.create_index('ix_api_usage_records_app_id', 'api_usage_records', ['application_id'])
    op.create_index('ix_api_usage_records_timestamp', 'api_usage_records', ['timestamp'])
    op.create_index('ix_api_usage_records_request_id', 'api_usage_records', ['request_id'])
    op.create_index('ix_api_usage_org_timestamp', 'api_usage_records', ['organization_id', 'timestamp'])
    op.create_index('ix_api_usage_app_timestamp', 'api_usage_records', ['application_id', 'timestamp'])

    # 8. webhook_subscriptions
    op.create_table(
        'webhook_subscriptions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('application_id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('url', sa.String(length=1024), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('events', sa.JSON(), nullable=False),
        sa.Column('secret_hash', sa.String(length=128), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_delivery_at', sa.DateTime(), nullable=True),
        sa.Column('failure_count', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['application_id'], ['developer_applications.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_webhook_subscriptions_application_id', 'webhook_subscriptions', ['application_id'])
    op.create_index('ix_webhook_subscriptions_organization_id', 'webhook_subscriptions', ['organization_id'])
    op.create_index('ix_webhook_subscriptions_status', 'webhook_subscriptions', ['status'])
    op.create_index('ix_webhook_subs_app_status', 'webhook_subscriptions', ['application_id', 'status'])

    # 9. application_approvals
    op.create_table(
        'application_approvals',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('application_id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('requested_environment', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('requested_by', sa.String(length=36), nullable=False),
        sa.Column('reviewed_by', sa.String(length=36), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['application_id'], ['developer_applications.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_application_approvals_app_id', 'application_approvals', ['application_id'])
    op.create_index('ix_application_approvals_org_id', 'application_approvals', ['organization_id'])
    op.create_index('ix_application_approvals_status', 'application_approvals', ['status'])

    # 10. api_environment_configs
    op.create_table(
        'api_environment_configs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('environment', sa.String(length=50), nullable=False),
        sa.Column('require_approval', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('default_rate_limit_rpm', sa.Integer(), nullable=False, server_default='120'),
        sa.Column('default_rate_limit_rph', sa.Integer(), nullable=False, server_default='5000'),
        sa.Column('max_payload_bytes', sa.Integer(), nullable=False, server_default='10485760'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_api_environment_configs_org_id', 'api_environment_configs', ['organization_id'])
    op.create_index('ix_env_configs_org_env', 'api_environment_configs', ['organization_id', 'environment'], unique=True)


def downgrade() -> None:
    op.drop_table('api_environment_configs')
    op.drop_table('application_approvals')
    op.drop_table('webhook_subscriptions')
    op.drop_table('api_usage_records')
    op.drop_table('api_idempotency_records')
    op.drop_table('api_quotas')
    op.drop_table('api_resource_scopes')
    op.drop_table('api_scope_assignments')
    op.drop_table('api_credentials')
    op.drop_table('developer_applications')
