"""Step 29: Knowledge Graph and Structured Context Layer

Revision ID: 026_knowledge_graph
Revises: 025_prompt_management
Create Date: 2026-10-03 16:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from backend.app.db.models.guid import GUID

# revision identifiers, used by Alembic.
revision: str = "026_knowledge_graph"
down_revision: Union[str, None] = "025_prompt_management"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    # 1. Create entities table
    if "entities" not in tables:
        op.create_table(
            "entities",
            sa.Column("id", GUID(), nullable=False),
            sa.Column("organization_id", GUID(), nullable=False),
            sa.Column("workspace_id", GUID(), nullable=False),
            sa.Column("project_id", GUID(), nullable=True),
            sa.Column("entity_type", sa.String(length=64), nullable=False),
            sa.Column("canonical_name", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("properties", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("source_count", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("confidence", sa.Float(), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_entities_id", "entities", ["id"], unique=False)
        op.create_index("ix_entities_organization_id", "entities", ["organization_id"], unique=False)
        op.create_index("ix_entities_workspace_id", "entities", ["workspace_id"], unique=False)
        op.create_index("ix_entities_project_id", "entities", ["project_id"], unique=False)
        op.create_index("ix_entities_entity_type", "entities", ["entity_type"], unique=False)
        op.create_index("ix_entities_canonical_name", "entities", ["canonical_name"], unique=False)
        op.create_index("ix_entities_status", "entities", ["status"], unique=False)
        op.create_index("ix_entities_created_at", "entities", ["created_at"], unique=False)
        op.create_index("ix_entities_workspace_type", "entities", ["workspace_id", "entity_type"], unique=False)
        op.create_index("ix_entities_workspace_name", "entities", ["workspace_id", "canonical_name"], unique=False)

    # 2. Create entity_aliases table
    if "entity_aliases" not in tables:
        op.create_table(
            "entity_aliases",
            sa.Column("id", GUID(), nullable=False),
            sa.Column("entity_id", GUID(), nullable=False),
            sa.Column("alias", sa.String(length=255), nullable=False),
            sa.Column("normalized_alias", sa.String(length=255), nullable=False),
            sa.Column("source_type", sa.String(length=32), nullable=False, server_default="manual"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["entity_id"], ["entities.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("entity_id", "normalized_alias", name="uq_entity_alias"),
        )
        op.create_index("ix_entity_aliases_id", "entity_aliases", ["id"], unique=False)
        op.create_index("ix_entity_aliases_entity_id", "entity_aliases", ["entity_id"], unique=False)
        op.create_index("ix_entity_aliases_normalized", "entity_aliases", ["normalized_alias"], unique=False)

    # 3. Create entity_sources table
    if "entity_sources" not in tables:
        op.create_table(
            "entity_sources",
            sa.Column("id", GUID(), nullable=False),
            sa.Column("entity_id", GUID(), nullable=False),
            sa.Column("source_type", sa.String(length=64), nullable=False),
            sa.Column("source_id", sa.String(length=255), nullable=False),
            sa.Column("source_location", sa.String(length=512), nullable=True),
            sa.Column("content_hash", sa.String(length=64), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["entity_id"], ["entities.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_entity_sources_id", "entity_sources", ["id"], unique=False)
        op.create_index("ix_entity_sources_entity_id", "entity_sources", ["entity_id"], unique=False)
        op.create_index("ix_entity_sources_source_type", "entity_sources", ["source_type"], unique=False)
        op.create_index("ix_entity_sources_source_id", "entity_sources", ["source_id"], unique=False)
        op.create_index("ix_entity_sources_content_hash", "entity_sources", ["content_hash"], unique=False)

    # 4. Create relationships table
    if "relationships" not in tables:
        op.create_table(
            "relationships",
            sa.Column("id", GUID(), nullable=False),
            sa.Column("organization_id", GUID(), nullable=False),
            sa.Column("workspace_id", GUID(), nullable=False),
            sa.Column("project_id", GUID(), nullable=True),
            sa.Column("source_entity_id", GUID(), nullable=False),
            sa.Column("relationship_type", sa.String(length=64), nullable=False),
            sa.Column("target_entity_id", GUID(), nullable=False),
            sa.Column("properties", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("source_reference", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("confidence", sa.Float(), nullable=True),
            sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
            sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["source_entity_id"], ["entities.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["target_entity_id"], ["entities.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_relationships_id", "relationships", ["id"], unique=False)
        op.create_index("ix_relationships_org_id", "relationships", ["organization_id"], unique=False)
        op.create_index("ix_relationships_ws_id", "relationships", ["workspace_id"], unique=False)
        op.create_index("ix_relationships_project_id", "relationships", ["project_id"], unique=False)
        op.create_index("ix_relationships_source_id", "relationships", ["source_entity_id"], unique=False)
        op.create_index("ix_relationships_target_id", "relationships", ["target_entity_id"], unique=False)
        op.create_index("ix_relationships_type", "relationships", ["relationship_type"], unique=False)
        op.create_index("ix_relationships_status", "relationships", ["status"], unique=False)
        op.create_index("ix_relationships_created_at", "relationships", ["created_at"], unique=False)
        op.create_index("ix_relationships_source_type", "relationships", ["source_entity_id", "relationship_type"], unique=False)
        op.create_index("ix_relationships_target_type", "relationships", ["target_entity_id", "relationship_type"], unique=False)

    # 5. Create graph_change_proposals table
    if "graph_change_proposals" not in tables:
        op.create_table(
            "graph_change_proposals",
            sa.Column("id", GUID(), nullable=False),
            sa.Column("organization_id", GUID(), nullable=False),
            sa.Column("workspace_id", GUID(), nullable=False),
            sa.Column("project_id", GUID(), nullable=True),
            sa.Column("source_id", sa.String(length=255), nullable=False),
            sa.Column("source_type", sa.String(length=64), nullable=False, server_default="extraction"),
            sa.Column("proposed_entities", sa.JSON(), nullable=False, server_default="[]"),
            sa.Column("proposed_relationships", sa.JSON(), nullable=False, server_default="[]"),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
            sa.Column("created_by", GUID(), nullable=True),
            sa.Column("reviewed_by", GUID(), nullable=True),
            sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("rejection_reason", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_graph_proposals_id", "graph_change_proposals", ["id"], unique=False)
        op.create_index("ix_graph_proposals_org_id", "graph_change_proposals", ["organization_id"], unique=False)
        op.create_index("ix_graph_proposals_ws_id", "graph_change_proposals", ["workspace_id"], unique=False)
        op.create_index("ix_graph_proposals_status", "graph_change_proposals", ["status"], unique=False)
        op.create_index("ix_graph_proposals_created_at", "graph_change_proposals", ["created_at"], unique=False)

    # 6. Create graph_change_logs table
    if "graph_change_logs" not in tables:
        op.create_table(
            "graph_change_logs",
            sa.Column("id", GUID(), nullable=False),
            sa.Column("organization_id", GUID(), nullable=False),
            sa.Column("workspace_id", GUID(), nullable=False),
            sa.Column("project_id", GUID(), nullable=True),
            sa.Column("entity_id", GUID(), nullable=True),
            sa.Column("relationship_id", GUID(), nullable=True),
            sa.Column("action", sa.String(length=64), nullable=False),
            sa.Column("actor_id", GUID(), nullable=True),
            sa.Column("source_type", sa.String(length=64), nullable=False, server_default="manual"),
            sa.Column("before_state", sa.JSON(), nullable=True),
            sa.Column("after_state", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_graph_changelogs_id", "graph_change_logs", ["id"], unique=False)
        op.create_index("ix_graph_changelogs_org_id", "graph_change_logs", ["organization_id"], unique=False)
        op.create_index("ix_graph_changelogs_ws_id", "graph_change_logs", ["workspace_id"], unique=False)
        op.create_index("ix_graph_changelogs_entity_id", "graph_change_logs", ["entity_id"], unique=False)
        op.create_index("ix_graph_changelogs_rel_id", "graph_change_logs", ["relationship_id"], unique=False)
        op.create_index("ix_graph_changelogs_created_at", "graph_change_logs", ["created_at"], unique=False)

    # 7. Create graph_conflicts table
    if "graph_conflicts" not in tables:
        op.create_table(
            "graph_conflicts",
            sa.Column("id", GUID(), nullable=False),
            sa.Column("organization_id", GUID(), nullable=False),
            sa.Column("workspace_id", GUID(), nullable=False),
            sa.Column("entity_id", GUID(), nullable=True),
            sa.Column("relationship_id", GUID(), nullable=True),
            sa.Column("conflict_type", sa.String(length=64), nullable=False),
            sa.Column("details", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("resolved_by", GUID(), nullable=True),
            sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_graph_conflicts_id", "graph_conflicts", ["id"], unique=False)
        op.create_index("ix_graph_conflicts_org_id", "graph_conflicts", ["organization_id"], unique=False)
        op.create_index("ix_graph_conflicts_ws_id", "graph_conflicts", ["workspace_id"], unique=False)
        op.create_index("ix_graph_conflicts_status", "graph_conflicts", ["status"], unique=False)
        op.create_index("ix_graph_conflicts_type", "graph_conflicts", ["conflict_type"], unique=False)
        op.create_index("ix_graph_conflicts_created_at", "graph_conflicts", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_table("graph_conflicts")
    op.drop_table("graph_change_logs")
    op.drop_table("graph_change_proposals")
    op.drop_table("relationships")
    op.drop_table("entity_sources")
    op.drop_table("entity_aliases")
    op.drop_table("entities")
