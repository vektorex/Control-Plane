"""User profile table and multi-tenant workspace ownership

Revision ID: 002_user_and_workspace_ownership
Revises: 001_initial_schema
Create Date: 2026-09-27 13:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from backend.app.db.models.guid import GUID

# revision identifiers, used by Alembic.
revision: str = "002_user_and_workspace_ownership"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create users table
    op.create_table(
        "users",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("auth_user_id", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("auth_user_id", name="uq_users_auth_user_id"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_auth_user_id"), "users", ["auth_user_id"], unique=True)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)

    # 2. Add owner_user_id column to workspaces
    op.add_column("workspaces", sa.Column("owner_user_id", GUID(), nullable=True))

    # In SQLite/Postgres migration: Add foreign key and unique constraint
    # Drop previous unique constraint/index on slug if exists
    try:
        op.drop_index("ix_workspaces_slug", table_name="workspaces")
    except Exception:
        pass

    op.create_index(op.f("ix_workspaces_slug"), "workspaces", ["slug"], unique=False)
    op.create_index(op.f("ix_workspaces_owner_user_id"), "workspaces", ["owner_user_id"], unique=False)

    with op.batch_alter_table("workspaces") as batch_op:
        batch_op.create_foreign_key(
            "fk_workspaces_owner_user_id_users",
            "users",
            ["owner_user_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_unique_constraint(
            "uq_workspace_owner_slug",
            ["owner_user_id", "slug"],
        )


def downgrade() -> None:
    with op.batch_alter_table("workspaces") as batch_op:
        batch_op.drop_constraint("uq_workspace_owner_slug", type_="unique")
        batch_op.drop_constraint("fk_workspaces_owner_user_id_users", type_="foreignkey")
        batch_op.drop_column("owner_user_id")

    try:
        op.drop_index("ix_workspaces_owner_user_id", table_name="workspaces")
    except Exception:
        pass

    op.drop_table("users")
