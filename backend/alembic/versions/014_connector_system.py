"""Connector System schema: credentials and permissions

Revision ID: 014_connector_system
Revises: 013_workflow_system
Create Date: 2026-09-30 01:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from backend.app.db.models.guid import GUID

# revision identifiers, used by Alembic.
revision: str = "014_connector_system"
down_revision: Union[str, None] = "013_workflow_system"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create credentials table
    op.create_table(
        "credentials",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("user_id", GUID(), nullable=True),
        sa.Column("connector_name", sa.String(length=100), nullable=False),
        sa.Column("credential_type", sa.String(length=50), nullable=False, server_default="pat"),
        sa.Column("encrypted_secret", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_id", "connector_name", name="uq_credentials_workspace_connector"),
    )
    op.create_index("ix_credentials_id", "credentials", ["id"], unique=False)
    op.create_index("ix_credentials_workspace_id", "credentials", ["workspace_id"], unique=False)
    op.create_index("ix_credentials_user_id", "credentials", ["user_id"], unique=False)
    op.create_index("ix_credentials_connector_name", "credentials", ["connector_name"], unique=False)
    op.create_index("ix_credentials_ws_conn", "credentials", ["workspace_id", "connector_name"], unique=False)

    # 2. Create connector_permissions table
    op.create_table(
        "connector_permissions",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("connector_name", sa.String(length=100), nullable=False),
        sa.Column("operation", sa.String(length=100), nullable=False),
        sa.Column("permission_level", sa.String(length=50), nullable=False, server_default="read"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_id", "connector_name", "operation", name="uq_connector_permissions_ws_conn_op"),
    )
    op.create_index("ix_connector_permissions_id", "connector_permissions", ["id"], unique=False)
    op.create_index("ix_connector_permissions_workspace_id", "connector_permissions", ["workspace_id"], unique=False)
    op.create_index("ix_connector_permissions_connector_name", "connector_permissions", ["connector_name"], unique=False)
    op.create_index("ix_connector_permissions_operation", "connector_permissions", ["operation"], unique=False)
    op.create_index("ix_connector_permissions_ws_conn", "connector_permissions", ["workspace_id", "connector_name"], unique=False)


def downgrade() -> None:
    op.drop_table("connector_permissions")
    op.drop_table("credentials")
