"""Step 28: Prompt Management, Versioning, Release, and Experimentation

Revision ID: 025_prompt_management
Revises: 024_access_control_and_organizations
Create Date: 2026-10-03 14:00:00.000000

"""
from typing import Sequence, Union
import uuid
from alembic import op
import sqlalchemy as sa
from backend.app.db.models.guid import GUID

# revision identifiers, used by Alembic.
revision: str = "025_prompt_management"
down_revision: Union[str, None] = "024_access_control_and_organizations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    # 1. Create prompts table
    if "prompts" not in tables:
        op.create_table(
            "prompts",
            sa.Column("id", GUID(), nullable=False),
            sa.Column("organization_id", GUID(), nullable=False),
            sa.Column("workspace_id", GUID(), nullable=False),
            sa.Column("project_id", GUID(), nullable=True),
            sa.Column("owner_user_id", GUID(), nullable=False),
            sa.Column("key", sa.String(length=255), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("prompt_type", sa.String(length=50), nullable=False, server_default="instruction"),
            sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="RESTRICT"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_prompts_id", "prompts", ["id"], unique=False)
        op.create_index("ix_prompts_org_id", "prompts", ["organization_id"], unique=False)
        op.create_index("ix_prompts_ws_id", "prompts", ["workspace_id"], unique=False)
        op.create_index("ix_prompts_project_id", "prompts", ["project_id"], unique=False)
        op.create_index("ix_prompts_owner_user_id", "prompts", ["owner_user_id"], unique=False)
        op.create_index("ix_prompts_key", "prompts", ["key"], unique=False)
        op.create_index("ix_prompts_type", "prompts", ["prompt_type"], unique=False)
        op.create_index("ix_prompts_status", "prompts", ["status"], unique=False)
        op.create_index("ix_prompts_created_at", "prompts", ["created_at"], unique=False)
        op.create_index("ix_prompts_org_ws_key", "prompts", ["organization_id", "workspace_id", "key"], unique=False)

    # 2. Create prompt_versions table
    if "prompt_versions" not in tables:
        op.create_table(
            "prompt_versions",
            sa.Column("id", GUID(), nullable=False),
            sa.Column("prompt_id", GUID(), nullable=False),
            sa.Column("version_number", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=50), nullable=False, server_default="draft"),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("variable_schema", sa.JSON(), nullable=False),
            sa.Column("model_requirements", sa.JSON(), nullable=True),
            sa.Column("execution_config", sa.JSON(), nullable=True),
            sa.Column("change_summary", sa.Text(), nullable=True),
            sa.Column("created_by", GUID(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("content_hash", sa.String(length=64), nullable=True),
            sa.ForeignKeyConstraint(["prompt_id"], ["prompts.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("prompt_id", "version_number", name="uq_prompt_id_version_number"),
        )
        op.create_index("ix_prompt_versions_id", "prompt_versions", ["id"], unique=False)
        op.create_index("ix_prompt_versions_prompt_id", "prompt_versions", ["prompt_id"], unique=False)
        op.create_index("ix_prompt_versions_status", "prompt_versions", ["status"], unique=False)
        op.create_index("ix_prompt_versions_content_hash", "prompt_versions", ["content_hash"], unique=False)
        op.create_index("ix_prompt_versions_created_by", "prompt_versions", ["created_by"], unique=False)
        op.create_index("ix_prompt_versions_created_at", "prompt_versions", ["created_at"], unique=False)

    # 3. Create prompt_releases table
    if "prompt_releases" not in tables:
        op.create_table(
            "prompt_releases",
            sa.Column("id", GUID(), nullable=False),
            sa.Column("prompt_id", GUID(), nullable=False),
            sa.Column("environment", sa.String(length=50), nullable=False),
            sa.Column("version_id", GUID(), nullable=False),
            sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
            sa.Column("released_by", GUID(), nullable=False),
            sa.Column("released_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("previous_version_id", GUID(), nullable=True),
            sa.ForeignKeyConstraint(["prompt_id"], ["prompts.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["version_id"], ["prompt_versions.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["previous_version_id"], ["prompt_versions.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["released_by"], ["users.id"], ondelete="RESTRICT"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_prompt_releases_id", "prompt_releases", ["id"], unique=False)
        op.create_index("ix_prompt_releases_prompt_id", "prompt_releases", ["prompt_id"], unique=False)
        op.create_index("ix_prompt_releases_env", "prompt_releases", ["environment"], unique=False)
        op.create_index("ix_prompt_releases_version_id", "prompt_releases", ["version_id"], unique=False)
        op.create_index("ix_prompt_releases_status", "prompt_releases", ["status"], unique=False)
        op.create_index("ix_prompt_releases_released_at", "prompt_releases", ["released_at"], unique=False)
        op.create_index("ix_prompt_releases_env_status", "prompt_releases", ["prompt_id", "environment", "status"], unique=False)

    # 4. Create prompt_experiments table
    if "prompt_experiments" not in tables:
        op.create_table(
            "prompt_experiments",
            sa.Column("id", GUID(), nullable=False),
            sa.Column("organization_id", GUID(), nullable=False),
            sa.Column("workspace_id", GUID(), nullable=False),
            sa.Column("project_id", GUID(), nullable=True),
            sa.Column("prompt_id", GUID(), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=50), nullable=False, server_default="draft"),
            sa.Column("allocation_key", sa.String(length=100), nullable=False, server_default="user_id"),
            sa.Column("created_by", GUID(), nullable=False),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["prompt_id"], ["prompts.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_prompt_experiments_id", "prompt_experiments", ["id"], unique=False)
        op.create_index("ix_prompt_experiments_org_id", "prompt_experiments", ["organization_id"], unique=False)
        op.create_index("ix_prompt_experiments_ws_id", "prompt_experiments", ["workspace_id"], unique=False)
        op.create_index("ix_prompt_experiments_prompt_id", "prompt_experiments", ["prompt_id"], unique=False)
        op.create_index("ix_prompt_experiments_status", "prompt_experiments", ["status"], unique=False)
        op.create_index("ix_prompt_experiments_created_at", "prompt_experiments", ["created_at"], unique=False)

    # 5. Create prompt_experiment_variants table
    if "prompt_experiment_variants" not in tables:
        op.create_table(
            "prompt_experiment_variants",
            sa.Column("id", GUID(), nullable=False),
            sa.Column("experiment_id", GUID(), nullable=False),
            sa.Column("prompt_version_id", GUID(), nullable=False),
            sa.Column("label", sa.String(length=50), nullable=False),
            sa.Column("allocation_weight", sa.Float(), nullable=False, server_default="1.0"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["experiment_id"], ["prompt_experiments.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["prompt_version_id"], ["prompt_versions.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("experiment_id", "prompt_version_id", name="uq_exp_prompt_version"),
            sa.UniqueConstraint("experiment_id", "label", name="uq_exp_variant_label"),
        )
        op.create_index("ix_prompt_exp_variants_id", "prompt_experiment_variants", ["id"], unique=False)
        op.create_index("ix_prompt_exp_variants_exp_id", "prompt_experiment_variants", ["experiment_id"], unique=False)

    # 6. Create prompt_experiment_assignments table
    if "prompt_experiment_assignments" not in tables:
        op.create_table(
            "prompt_experiment_assignments",
            sa.Column("id", GUID(), nullable=False),
            sa.Column("experiment_id", GUID(), nullable=False),
            sa.Column("variant_id", GUID(), nullable=False),
            sa.Column("allocation_key_value", sa.String(length=255), nullable=False),
            sa.Column("assigned_version_id", GUID(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["experiment_id"], ["prompt_experiments.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["variant_id"], ["prompt_experiment_variants.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["assigned_version_id"], ["prompt_versions.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("experiment_id", "allocation_key_value", name="uq_exp_alloc_key"),
        )
        op.create_index("ix_prompt_exp_assignments_id", "prompt_experiment_assignments", ["id"], unique=False)
        op.create_index("ix_prompt_exp_assignments_exp_id", "prompt_experiment_assignments", ["experiment_id"], unique=False)
        op.create_index("ix_prompt_exp_assignments_key", "prompt_experiment_assignments", ["allocation_key_value"], unique=False)


def downgrade() -> None:
    op.drop_table("prompt_experiment_assignments")
    op.drop_table("prompt_experiment_variants")
    op.drop_table("prompt_experiments")
    op.drop_table("prompt_releases")
    op.drop_table("prompt_versions")
    op.drop_table("prompts")
