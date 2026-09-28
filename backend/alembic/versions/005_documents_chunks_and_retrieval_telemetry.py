"""Documents, document chunks, and retrieval telemetry metadata

Revision ID: 005_documents_chunks_and_retrieval_telemetry
Revises: 004_task_context_and_run_context_metadata
Create Date: 2026-09-28 15:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from backend.app.db.models.guid import GUID
from backend.app.db.models.vector_type import VectorType

# revision identifiers, used by Alembic.
revision: str = "005_documents_chunks_and_retrieval_telemetry"
down_revision: Union[str, None] = "004_task_context_and_run_context_metadata"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enable pgvector extension on PostgreSQL if supported
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # 2. Create documents table
    op.create_table(
        "documents",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("project_id", GUID(), nullable=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("storage_key", sa.String(length=500), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="pending", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("chunk_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_documents_id"), "documents", ["id"], unique=False)
    op.create_index(op.f("ix_documents_workspace_id"), "documents", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_documents_project_id"), "documents", ["project_id"], unique=False)
    op.create_index(op.f("ix_documents_status"), "documents", ["status"], unique=False)
    op.create_index(op.f("ix_documents_created_at"), "documents", ["created_at"], unique=False)

    # 3. Create document_chunks table
    op.create_table(
        "document_chunks",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("document_id", GUID(), nullable=False),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("project_id", GUID(), nullable=True),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("embedding", VectorType(dim=1536), nullable=True),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_document_chunks_id"), "document_chunks", ["id"], unique=False)
    op.create_index(op.f("ix_document_chunks_document_id"), "document_chunks", ["document_id"], unique=False)
    op.create_index(op.f("ix_document_chunks_workspace_id"), "document_chunks", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_document_chunks_project_id"), "document_chunks", ["project_id"], unique=False)
    op.create_index(op.f("ix_document_chunks_chunk_index"), "document_chunks", ["chunk_index"], unique=False)
    op.create_index(op.f("ix_document_chunks_created_at"), "document_chunks", ["created_at"], unique=False)

    # 4. Add retrieval telemetry columns to runs table
    with op.batch_alter_table("runs") as batch_op:
        batch_op.add_column(sa.Column("retrieval_enabled", sa.Boolean(), server_default=sa.text("0"), nullable=True))
        batch_op.add_column(sa.Column("retrieved_chunk_count", sa.Integer(), server_default="0", nullable=True))
        batch_op.add_column(sa.Column("retrieval_latency_ms", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("retrieval_sources", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("runs") as batch_op:
        batch_op.drop_column("retrieval_sources")
        batch_op.drop_column("retrieval_latency_ms")
        batch_op.drop_column("retrieved_chunk_count")
        batch_op.drop_column("retrieval_enabled")

    op.drop_index(op.f("ix_document_chunks_created_at"), table_name="document_chunks")
    op.drop_index(op.f("ix_document_chunks_chunk_index"), table_name="document_chunks")
    op.drop_index(op.f("ix_document_chunks_project_id"), table_name="document_chunks")
    op.drop_index(op.f("ix_document_chunks_workspace_id"), table_name="document_chunks")
    op.drop_index(op.f("ix_document_chunks_document_id"), table_name="document_chunks")
    op.drop_index(op.f("ix_document_chunks_id"), table_name="document_chunks")
    op.drop_table("document_chunks")

    op.drop_index(op.f("ix_documents_created_at"), table_name="documents")
    op.drop_index(op.f("ix_documents_status"), table_name="documents")
    op.drop_index(op.f("ix_documents_project_id"), table_name="documents")
    op.drop_index(op.f("ix_documents_workspace_id"), table_name="documents")
    op.drop_index(op.f("ix_documents_id"), table_name="documents")
    op.drop_table("documents")
