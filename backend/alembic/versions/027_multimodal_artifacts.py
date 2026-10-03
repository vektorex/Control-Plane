"""Step 30: Multimodal AI and Unified Artifact Intelligence

Revision ID: 027_multimodal_artifacts
Revises: 026_knowledge_graph
Create Date: 2026-10-03 20:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from backend.app.db.models.guid import GUID

# revision identifiers, used by Alembic.
revision: str = "027_multimodal_artifacts"
down_revision: Union[str, None] = "026_knowledge_graph"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    # 1. Create artifacts table
    if "artifacts" not in tables:
        op.create_table(
            "artifacts",
            sa.Column("id", GUID(), nullable=False),
            sa.Column("organization_id", GUID(), nullable=False),
            sa.Column("workspace_id", GUID(), nullable=False),
            sa.Column("project_id", GUID(), nullable=True),
            sa.Column("owner_user_id", GUID(), nullable=False),
            sa.Column("artifact_type", sa.String(length=64), nullable=False),
            sa.Column("mime_type", sa.String(length=128), nullable=False),
            sa.Column("filename", sa.String(length=255), nullable=False),
            sa.Column("size_bytes", sa.Integer(), nullable=False),
            sa.Column("storage_reference", sa.String(length=512), nullable=False),
            sa.Column("content_hash", sa.String(length=64), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="uploaded"),
            sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_artifacts_id", "artifacts", ["id"], unique=False)
        op.create_index("ix_artifacts_organization_id", "artifacts", ["organization_id"], unique=False)
        op.create_index("ix_artifacts_workspace_id", "artifacts", ["workspace_id"], unique=False)
        op.create_index("ix_artifacts_project_id", "artifacts", ["project_id"], unique=False)
        op.create_index("ix_artifacts_owner_user_id", "artifacts", ["owner_user_id"], unique=False)
        op.create_index("ix_artifacts_artifact_type", "artifacts", ["artifact_type"], unique=False)
        op.create_index("ix_artifacts_mime_type", "artifacts", ["mime_type"], unique=False)
        op.create_index("ix_artifacts_content_hash", "artifacts", ["content_hash"], unique=False)
        op.create_index("ix_artifacts_status", "artifacts", ["status"], unique=False)
        op.create_index("ix_artifacts_created_at", "artifacts", ["created_at"], unique=False)
        op.create_index("ix_artifacts_org_ws", "artifacts", ["organization_id", "workspace_id"], unique=False)
        op.create_index("ix_artifacts_ws_status", "artifacts", ["workspace_id", "status"], unique=False)

    # 2. Create artifact_parts table
    if "artifact_parts" not in tables:
        op.create_table(
            "artifact_parts",
            sa.Column("id", GUID(), nullable=False),
            sa.Column("artifact_id", GUID(), nullable=False),
            sa.Column("part_type", sa.String(length=64), nullable=False),
            sa.Column("sequence_number", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("content_reference", sa.String(length=512), nullable=True),
            sa.Column("text_content", sa.Text(), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("content_hash", sa.String(length=64), nullable=True),
            sa.Column("token_estimate", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["artifact_id"], ["artifacts.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_artifact_parts_id", "artifact_parts", ["id"], unique=False)
        op.create_index("ix_artifact_parts_artifact_id", "artifact_parts", ["artifact_id"], unique=False)
        op.create_index("ix_artifact_parts_type", "artifact_parts", ["part_type"], unique=False)
        op.create_index("ix_artifact_parts_artifact_seq", "artifact_parts", ["artifact_id", "sequence_number"], unique=False)

    # 3. Create artifact_evidence table
    if "artifact_evidence" not in tables:
        op.create_table(
            "artifact_evidence",
            sa.Column("id", GUID(), nullable=False),
            sa.Column("artifact_id", GUID(), nullable=False),
            sa.Column("part_id", GUID(), nullable=True),
            sa.Column("page", sa.Integer(), nullable=True),
            sa.Column("timestamp", sa.Float(), nullable=True),
            sa.Column("region", sa.JSON(), nullable=True),
            sa.Column("source_text", sa.Text(), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["artifact_id"], ["artifacts.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["part_id"], ["artifact_parts.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_artifact_evidence_id", "artifact_evidence", ["id"], unique=False)
        op.create_index("ix_artifact_evidence_artifact_id", "artifact_evidence", ["artifact_id"], unique=False)
        op.create_index("ix_artifact_evidence_part_id", "artifact_evidence", ["part_id"], unique=False)
        op.create_index("ix_artifact_evidence_artifact_part", "artifact_evidence", ["artifact_id", "part_id"], unique=False)


def downgrade() -> None:
    op.drop_table("artifact_evidence")
    op.drop_table("artifact_parts")
    op.drop_table("artifacts")
