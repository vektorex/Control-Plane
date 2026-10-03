"""Step 31: Production-Grade Semantic Cache and Intelligent Reuse Layer

Revision ID: 028_semantic_cache
Revises: 027_multimodal_artifacts
Create Date: 2026-10-03 21:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from backend.app.db.models.guid import GUID
from backend.app.db.models.vector_type import VectorType

# revision identifiers, used by Alembic.
revision: str = "028_semantic_cache"
down_revision: Union[str, None] = "027_multimodal_artifacts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if "cache_entries" not in tables:
        op.create_table(
            "cache_entries",
            sa.Column("id", GUID(), nullable=False),
            sa.Column("organization_id", GUID(), nullable=False),
            sa.Column("workspace_id", GUID(), nullable=False),
            sa.Column("project_id", GUID(), nullable=True),
            sa.Column("user_id", GUID(), nullable=True),
            sa.Column("namespace", sa.String(length=64), nullable=False, server_default="workspace"),
            sa.Column("cache_key", sa.String(length=64), nullable=True),
            sa.Column("semantic_embedding", VectorType(1536), nullable=True),
            sa.Column("normalized_request", sa.Text(), nullable=False),
            sa.Column("request_fingerprint", sa.String(length=64), nullable=False),
            sa.Column("response_content", sa.Text(), nullable=False),
            sa.Column("response_metadata", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("source_snapshot", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("prompt_id", GUID(), nullable=True),
            sa.Column("prompt_version_id", GUID(), nullable=True),
            sa.Column("model_id", sa.String(length=128), nullable=True),
            sa.Column("model_provider", sa.String(length=64), nullable=True),
            sa.Column("execution_config_hash", sa.String(length=64), nullable=True),
            sa.Column("context_hash", sa.String(length=64), nullable=True),
            sa.Column("artifact_hash", sa.String(length=64), nullable=True),
            sa.Column("graph_snapshot_hash", sa.String(length=64), nullable=True),
            sa.Column("memory_snapshot_hash", sa.String(length=64), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
            sa.Column("invalidation_reason", sa.String(length=255), nullable=True),
            sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("accessed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("last_hit_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("hit_count", sa.Integer(), nullable=False, server_default="0"),
            sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_cache_entries_id", "cache_entries", ["id"], unique=False)
        op.create_index("ix_cache_entries_organization_id", "cache_entries", ["organization_id"], unique=False)
        op.create_index("ix_cache_entries_workspace_id", "cache_entries", ["workspace_id"], unique=False)
        op.create_index("ix_cache_entries_project_id", "cache_entries", ["project_id"], unique=False)
        op.create_index("ix_cache_entries_user_id", "cache_entries", ["user_id"], unique=False)
        op.create_index("ix_cache_entries_namespace", "cache_entries", ["namespace"], unique=False)
        op.create_index("ix_cache_entries_cache_key", "cache_entries", ["cache_key"], unique=False)
        op.create_index("ix_cache_entries_request_fingerprint", "cache_entries", ["request_fingerprint"], unique=False)
        op.create_index("ix_cache_entries_prompt_id", "cache_entries", ["prompt_id"], unique=False)
        op.create_index("ix_cache_entries_prompt_version_id", "cache_entries", ["prompt_version_id"], unique=False)
        op.create_index("ix_cache_entries_model_id", "cache_entries", ["model_id"], unique=False)
        op.create_index("ix_cache_entries_status", "cache_entries", ["status"], unique=False)
        op.create_index("ix_cache_entries_expires_at", "cache_entries", ["expires_at"], unique=False)
        op.create_index("ix_cache_entries_created_at", "cache_entries", ["created_at"], unique=False)
        op.create_index("ix_cache_entries_accessed_at", "cache_entries", ["accessed_at"], unique=False)
        op.create_index("ix_cache_entries_tenant", "cache_entries", ["organization_id", "workspace_id", "status"], unique=False)
        op.create_index("ix_cache_entries_lookup", "cache_entries", ["workspace_id", "namespace", "cache_key", "status"], unique=False)
        op.create_index("ix_cache_entries_expires", "cache_entries", ["status", "expires_at"], unique=False)
        op.create_index("ix_cache_entries_prompt_ver", "cache_entries", ["prompt_version_id", "status"], unique=False)
        op.create_index("ix_cache_entries_artifact", "cache_entries", ["artifact_hash", "status"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if "cache_entries" in tables:
        op.drop_table("cache_entries")
