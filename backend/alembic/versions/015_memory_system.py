"""Memory System schema: memories, embeddings, conflicts, suggestions, settings

Revision ID: 015_memory_system
Revises: 014_connector_system
Create Date: 2026-09-30 02:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from backend.app.db.models.guid import GUID
from backend.app.db.models.vector_type import VectorType

# revision identifiers, used by Alembic.
revision: str = "015_memory_system"
down_revision: Union[str, None] = "014_connector_system"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create memories table
    op.create_table(
        "memories",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("user_id", GUID(), nullable=True),
        sa.Column("project_id", GUID(), nullable=True),
        sa.Column("scope", sa.String(length=50), nullable=False, server_default="user"),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("normalized_content", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False, server_default="explicit_user"),
        sa.Column("source_id", sa.String(length=255), nullable=True),
        sa.Column("importance", sa.String(length=20), nullable=False, server_default="medium"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_memories_id", "memories", ["id"], unique=False)
    op.create_index("ix_memories_workspace_id", "memories", ["workspace_id"], unique=False)
    op.create_index("ix_memories_user_id", "memories", ["user_id"], unique=False)
    op.create_index("ix_memories_project_id", "memories", ["project_id"], unique=False)
    op.create_index("ix_memories_scope", "memories", ["scope"], unique=False)
    op.create_index("ix_memories_type", "memories", ["type"], unique=False)
    op.create_index("ix_memories_status", "memories", ["status"], unique=False)
    op.create_index("ix_memories_created_at", "memories", ["created_at"], unique=False)
    op.create_index("ix_memories_updated_at", "memories", ["updated_at"], unique=False)
    op.create_index("ix_memories_last_used_at", "memories", ["last_used_at"], unique=False)
    op.create_index("ix_memories_expires_at", "memories", ["expires_at"], unique=False)
    op.create_index("ix_memories_ws_user", "memories", ["workspace_id", "user_id"], unique=False)
    op.create_index("ix_memories_ws_proj", "memories", ["workspace_id", "project_id"], unique=False)
    op.create_index("ix_memories_ws_scope_status", "memories", ["workspace_id", "scope", "status"], unique=False)
    op.create_index("ix_memories_ws_type_status", "memories", ["workspace_id", "type", "status"], unique=False)

    # 2. Create memory_embeddings table
    op.create_table(
        "memory_embeddings",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("memory_id", GUID(), nullable=False),
        sa.Column("embedding", VectorType(dim=1536), nullable=True),
        sa.Column("embedding_model", sa.String(length=100), nullable=False, server_default="text-embedding-3-small"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["memory_id"], ["memories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("memory_id", name="uq_memory_embeddings_memory_id"),
    )
    op.create_index("ix_memory_embeddings_id", "memory_embeddings", ["id"], unique=False)
    op.create_index("ix_memory_embeddings_memory_id", "memory_embeddings", ["memory_id"], unique=True)

    # 3. Create memory_conflicts table
    op.create_table(
        "memory_conflicts",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("memory_a_id", GUID(), nullable=False),
        sa.Column("memory_b_id", GUID(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="unresolved"),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["memory_a_id"], ["memories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["memory_b_id"], ["memories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_memory_conflicts_id", "memory_conflicts", ["id"], unique=False)
    op.create_index("ix_memory_conflicts_workspace_id", "memory_conflicts", ["workspace_id"], unique=False)
    op.create_index("ix_memory_conflicts_memory_a_id", "memory_conflicts", ["memory_a_id"], unique=False)
    op.create_index("ix_memory_conflicts_memory_b_id", "memory_conflicts", ["memory_b_id"], unique=False)
    op.create_index("ix_memory_conflicts_status", "memory_conflicts", ["status"], unique=False)
    op.create_index("ix_memory_conflicts_ws_status", "memory_conflicts", ["workspace_id", "status"], unique=False)

    # 4. Create memory_suggestions table
    op.create_table(
        "memory_suggestions",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("user_id", GUID(), nullable=True),
        sa.Column("project_id", GUID(), nullable=True),
        sa.Column("type", sa.String(length=50), nullable=False, server_default="preference"),
        sa.Column("scope", sa.String(length=50), nullable=False, server_default="user"),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.8"),
        sa.Column("source_type", sa.String(length=50), nullable=False, server_default="task"),
        sa.Column("source_id", sa.String(length=255), nullable=True),
        sa.Column("importance", sa.String(length=20), nullable=False, server_default="medium"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_memory_suggestions_id", "memory_suggestions", ["id"], unique=False)
    op.create_index("ix_memory_suggestions_workspace_id", "memory_suggestions", ["workspace_id"], unique=False)
    op.create_index("ix_memory_suggestions_user_id", "memory_suggestions", ["user_id"], unique=False)
    op.create_index("ix_memory_suggestions_status", "memory_suggestions", ["status"], unique=False)
    op.create_index("ix_memory_suggestions_ws_status", "memory_suggestions", ["workspace_id", "status"], unique=False)
    op.create_index("ix_memory_suggestions_ws_user", "memory_suggestions", ["workspace_id", "user_id"], unique=False)

    # 5. Create user_memory_settings table
    op.create_table(
        "user_memory_settings",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("user_id", GUID(), nullable=False),
        sa.Column("memory_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("suggestions_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("default_retrieval_mode", sa.String(length=50), nullable=False, server_default="auto"),
        sa.Column("default_scope", sa.String(length=50), nullable=False, server_default="user"),
        sa.Column("retention_preference", sa.String(length=50), nullable=False, server_default="never"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_id", "user_id", name="uq_user_memory_settings_ws_user"),
    )
    op.create_index("ix_user_memory_settings_id", "user_memory_settings", ["id"], unique=False)
    op.create_index("ix_user_memory_settings_ws_user", "user_memory_settings", ["workspace_id", "user_id"], unique=False)

    # 6. Add memory telemetry columns to run_telemetry table
    with op.batch_alter_table("run_telemetry") as batch_op:
        batch_op.add_column(sa.Column("memory_retrieval_calls", sa.Integer(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("memory_results", sa.Integer(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("memory_ids_used", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("memory_duration_ms", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    with op.batch_alter_table("run_telemetry") as batch_op:
        batch_op.drop_column("memory_duration_ms")
        batch_op.drop_column("memory_ids_used")
        batch_op.drop_column("memory_results")
        batch_op.drop_column("memory_retrieval_calls")

    op.drop_table("user_memory_settings")
    op.drop_table("memory_suggestions")
    op.drop_table("memory_conflicts")
    op.drop_table("memory_embeddings")
    op.drop_table("memories")
