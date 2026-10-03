"""create marketplace packages, versions, dependencies, installations, reviews, provenance, and tags

Revision ID: 035
Revises: 034
Create Date: 2026-10-04 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '035'
down_revision: Union[str, None] = '034'
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None


def upgrade() -> None:
    # 1. marketplace_packages
    op.create_table(
        'marketplace_packages',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('owner_organization_id', sa.String(length=36), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('package_type', sa.String(length=50), nullable=False),
        sa.Column('visibility', sa.String(length=50), nullable=False, server_default='private'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='draft'),
        sa.Column('current_version_id', sa.String(length=36), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('owner_organization_id', 'slug', name='uq_marketplace_org_slug'),
    )
    op.create_index('ix_marketplace_packages_owner_id', 'marketplace_packages', ['owner_organization_id'])
    op.create_index('ix_marketplace_packages_slug', 'marketplace_packages', ['slug'])
    op.create_index('ix_marketplace_packages_category', 'marketplace_packages', ['category'])
    op.create_index('ix_marketplace_packages_package_type', 'marketplace_packages', ['package_type'])
    op.create_index('ix_marketplace_packages_visibility', 'marketplace_packages', ['visibility'])
    op.create_index('ix_marketplace_packages_status', 'marketplace_packages', ['status'])

    # 2. marketplace_package_versions
    op.create_table(
        'marketplace_package_versions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('package_id', sa.String(length=36), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('manifest', sa.JSON(), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('manifest_hash', sa.String(length=64), nullable=False),
        sa.Column('compatibility', sa.JSON(), nullable=True),
        sa.Column('security_status', sa.String(length=50), nullable=False, server_default='not_scanned'),
        sa.Column('validation_status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('publication_status', sa.String(length=50), nullable=False, server_default='draft'),
        sa.Column('created_by', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('deprecated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['package_id'], ['marketplace_packages.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('package_id', 'version', name='uq_package_version'),
    )
    op.create_index('ix_marketplace_package_versions_package_id', 'marketplace_package_versions', ['package_id'])
    op.create_index('ix_marketplace_package_versions_sec_status', 'marketplace_package_versions', ['security_status'])
    op.create_index('ix_marketplace_package_versions_pub_status', 'marketplace_package_versions', ['publication_status'])

    # 3. marketplace_dependencies
    op.create_table(
        'marketplace_dependencies',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('package_version_id', sa.String(length=36), nullable=False),
        sa.Column('dependency_type', sa.String(length=50), nullable=False),
        sa.Column('dependency_identifier', sa.String(length=255), nullable=False),
        sa.Column('version_constraint', sa.String(length=100), nullable=False, server_default='*'),
        sa.Column('optional', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['package_version_id'], ['marketplace_package_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_marketplace_dependencies_version_id', 'marketplace_dependencies', ['package_version_id'])

    # 4. marketplace_installations
    op.create_table(
        'marketplace_installations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('package_id', sa.String(length=36), nullable=False),
        sa.Column('package_version_id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=True),
        sa.Column('project_id', sa.String(length=36), nullable=True),
        sa.Column('installed_by', sa.String(length=36), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='installed'),
        sa.Column('configuration', sa.JSON(), nullable=False),
        sa.Column('installed_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('uninstalled_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['package_id'], ['marketplace_packages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['package_version_id'], ['marketplace_package_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_marketplace_installations_package_id', 'marketplace_installations', ['package_id'])
    op.create_index('ix_marketplace_installations_org_id', 'marketplace_installations', ['organization_id'])
    op.create_index('ix_marketplace_installations_workspace_id', 'marketplace_installations', ['workspace_id'])
    op.create_index('ix_marketplace_installations_status', 'marketplace_installations', ['status'])

    # 5. marketplace_reviews
    op.create_table(
        'marketplace_reviews',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('package_id', sa.String(length=36), nullable=False),
        sa.Column('package_version_id', sa.String(length=36), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('review', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='published'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['package_id'], ['marketplace_packages.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('package_id', 'organization_id', 'user_id', name='uq_package_user_review'),
    )
    op.create_index('ix_marketplace_reviews_package_id', 'marketplace_reviews', ['package_id'])

    # 6. marketplace_usage_records
    op.create_table(
        'marketplace_usage_records',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('package_id', sa.String(length=36), nullable=False),
        sa.Column('package_version_id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=True),
        sa.Column('installation_id', sa.String(length=36), nullable=True),
        sa.Column('run_id', sa.String(length=36), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('operation', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='success'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_marketplace_usage_records_pkg_id', 'marketplace_usage_records', ['package_id'])
    op.create_index('ix_marketplace_usage_records_org_id', 'marketplace_usage_records', ['organization_id'])
    op.create_index('ix_marketplace_usage_records_timestamp', 'marketplace_usage_records', ['timestamp'])

    # 7. marketplace_provenance
    op.create_table(
        'marketplace_provenance',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('package_version_id', sa.String(length=36), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False, server_default='native'),
        sa.Column('source_reference', sa.String(length=500), nullable=True),
        sa.Column('creator_organization_id', sa.String(length=36), nullable=False),
        sa.Column('creator_user_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('parent_version_id', sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(['package_version_id'], ['marketplace_package_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('package_version_id', name='uq_package_version_provenance'),
    )

    # 8. marketplace_tags
    op.create_table(
        'marketplace_tags',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_marketplace_tag_name'),
    )

    # 9. marketplace_package_tags
    op.create_table(
        'marketplace_package_tags',
        sa.Column('package_id', sa.String(length=36), nullable=False),
        sa.Column('tag_id', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(['package_id'], ['marketplace_packages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['marketplace_tags.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('package_id', 'tag_id'),
    )

    # 10. marketplace_approvals
    op.create_table(
        'marketplace_approvals',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('package_id', sa.String(length=36), nullable=False),
        sa.Column('package_version_id', sa.String(length=36), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('action_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('requested_by', sa.String(length=36), nullable=True),
        sa.Column('reviewed_by', sa.String(length=36), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['package_id'], ['marketplace_packages.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_marketplace_approvals_pkg_id', 'marketplace_approvals', ['package_id'])
    op.create_index('ix_marketplace_approvals_org_id', 'marketplace_approvals', ['organization_id'])


def downgrade() -> None:
    op.drop_table('marketplace_approvals')
    op.drop_table('marketplace_package_tags')
    op.drop_table('marketplace_tags')
    op.drop_table('marketplace_provenance')
    op.drop_table('marketplace_usage_records')
    op.drop_table('marketplace_reviews')
    op.drop_table('marketplace_installations')
    op.drop_table('marketplace_dependencies')
    op.drop_table('marketplace_package_versions')
    op.drop_table('marketplace_packages')
