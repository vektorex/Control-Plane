"""Step 27: Multi-Tenant Organizations, Teams, Roles & Access Control

Revision ID: 024_access_control_and_organizations
Revises: 023_unified_event_bus
Create Date: 2026-10-03 12:00:00.000000

"""
from datetime import datetime, timezone
from typing import Sequence, Union
import uuid
from alembic import op
import sqlalchemy as sa
from backend.app.db.models.guid import GUID

# revision identifiers, used by Alembic.
revision: str = "024_access_control_and_organizations"
down_revision: Union[str, None] = "023_unified_event_bus"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    # 1. Create organizations table
    if "organizations" not in tables:
        op.create_table(
            "organizations",
            sa.Column("id", GUID(), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("slug", sa.String(length=255), nullable=False),
            sa.Column("owner_user_id", GUID(), nullable=False),
            sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="RESTRICT"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("slug", name="uq_organizations_slug"),
        )
        op.create_index("ix_organizations_id", "organizations", ["id"], unique=False)
        op.create_index("ix_organizations_slug", "organizations", ["slug"], unique=True)
        op.create_index("ix_organizations_owner_user_id", "organizations", ["owner_user_id"], unique=False)
        op.create_index("ix_organizations_status", "organizations", ["status"], unique=False)

    # 2. Create organization_members table
    if "organization_members" not in tables:
        op.create_table(
            "organization_members",
            sa.Column("id", GUID(), nullable=False),
            sa.Column("organization_id", GUID(), nullable=False),
            sa.Column("user_id", GUID(), nullable=False),
            sa.Column("role", sa.String(length=50), nullable=False, server_default="member"),
            sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
            sa.Column("joined_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("organization_id", "user_id", name="uq_org_member_org_user"),
        )
        op.create_index("ix_organization_members_id", "organization_members", ["id"], unique=False)
        op.create_index("ix_organization_members_org_id", "organization_members", ["organization_id"], unique=False)
        op.create_index("ix_organization_members_user_id", "organization_members", ["user_id"], unique=False)
        op.create_index("ix_organization_members_role", "organization_members", ["role"], unique=False)
        op.create_index("ix_organization_members_status", "organization_members", ["status"], unique=False)

    # 3. Create organization_invitations table
    if "organization_invitations" not in tables:
        op.create_table(
            "organization_invitations",
            sa.Column("id", GUID(), nullable=False),
            sa.Column("organization_id", GUID(), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("role", sa.String(length=50), nullable=False, server_default="member"),
            sa.Column("token_hash", sa.String(length=255), nullable=False),
            sa.Column("invited_by", GUID(), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["invited_by"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("token_hash", name="uq_org_invitation_token_hash"),
        )
        op.create_index("ix_org_invitations_id", "organization_invitations", ["id"], unique=False)
        op.create_index("ix_org_invitations_org_id", "organization_invitations", ["organization_id"], unique=False)
        op.create_index("ix_org_invitations_email", "organization_invitations", ["email"], unique=False)
        op.create_index("ix_org_invitations_token_hash", "organization_invitations", ["token_hash"], unique=True)

    # 4. Create workspace_members table
    if "workspace_members" not in tables:
        op.create_table(
            "workspace_members",
            sa.Column("id", GUID(), nullable=False),
            sa.Column("workspace_id", GUID(), nullable=False),
            sa.Column("user_id", GUID(), nullable=False),
            sa.Column("role", sa.String(length=50), nullable=False, server_default="member"),
            sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("workspace_id", "user_id", name="uq_ws_member_ws_user"),
        )
        op.create_index("ix_workspace_members_id", "workspace_members", ["id"], unique=False)
        op.create_index("ix_workspace_members_workspace_id", "workspace_members", ["workspace_id"], unique=False)
        op.create_index("ix_workspace_members_user_id", "workspace_members", ["user_id"], unique=False)

    # 5. Create project_members table
    if "project_members" not in tables:
        op.create_table(
            "project_members",
            sa.Column("id", GUID(), nullable=False),
            sa.Column("project_id", GUID(), nullable=False),
            sa.Column("user_id", GUID(), nullable=False),
            sa.Column("role", sa.String(length=50), nullable=False, server_default="editor"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("project_id", "user_id", name="uq_proj_member_proj_user"),
        )
        op.create_index("ix_project_members_id", "project_members", ["id"], unique=False)
        op.create_index("ix_project_members_project_id", "project_members", ["project_id"], unique=False)
        op.create_index("ix_project_members_user_id", "project_members", ["user_id"], unique=False)

    # 6. Alter workspaces table
    if "workspaces" in tables:
        ws_cols = [c["name"] for c in inspector.get_columns("workspaces")]
        with op.batch_alter_table("workspaces") as batch_op:
            if "organization_id" not in ws_cols:
                batch_op.add_column(sa.Column("organization_id", GUID(), nullable=True))
                batch_op.create_foreign_key("fk_workspaces_organization_id", "organizations", ["organization_id"], ["id"], ondelete="CASCADE")
                batch_op.create_index("ix_workspaces_organization_id", ["organization_id"])
            if "status" not in ws_cols:
                batch_op.add_column(sa.Column("status", sa.String(length=50), nullable=False, server_default="active"))

    # 7. Alter projects table
    if "projects" in tables:
        proj_cols = [c["name"] for c in inspector.get_columns("projects")]
        with op.batch_alter_table("projects") as batch_op:
            if "access_mode" not in proj_cols:
                batch_op.add_column(sa.Column("access_mode", sa.String(length=50), nullable=False, server_default="workspace"))

    # 8. Alter tasks table
    if "tasks" in tables:
        task_cols = [c["name"] for c in inspector.get_columns("tasks")]
        with op.batch_alter_table("tasks") as batch_op:
            if "owner_user_id" not in task_cols:
                batch_op.add_column(sa.Column("owner_user_id", GUID(), nullable=True))
                batch_op.create_foreign_key("fk_tasks_owner_user_id", "users", ["owner_user_id"], ["id"], ondelete="SET NULL")
                batch_op.create_index("ix_tasks_owner_user_id", ["owner_user_id"])

    # 9. Data Migration: Migrate existing users -> personal organizations -> workspaces
    if "users" in tables and "workspaces" in tables:
        users = bind.execute(sa.text("SELECT id, email FROM users")).fetchall()
        for u in users:
            user_id = u[0]
            email = u[1] or "user@domain.local"
            clean_name = email.split("@")[0]
            org_id = str(uuid.uuid4())
            org_slug = f"{clean_name.lower()}-org-{str(user_id)[:6]}"
            now_iso = datetime.now(timezone.utc)

            # Check if user already owns an organization
            existing_org = bind.execute(
                sa.text("SELECT id FROM organizations WHERE owner_user_id = :uid LIMIT 1"),
                {"uid": user_id},
            ).fetchone()

            if not existing_org:
                bind.execute(
                    sa.text(
                        "INSERT INTO organizations (id, name, slug, owner_user_id, status, created_at, updated_at) "
                        "VALUES (:id, :name, :slug, :owner_user_id, 'active', :now, :now)"
                    ),
                    {
                        "id": org_id,
                        "name": f"{clean_name.capitalize()}'s Organization",
                        "slug": org_slug,
                        "owner_user_id": user_id,
                        "now": now_iso,
                    },
                )
                # Organization membership
                bind.execute(
                    sa.text(
                        "INSERT INTO organization_members (id, organization_id, user_id, role, status, joined_at, created_at, updated_at) "
                        "VALUES (:id, :org_id, :uid, 'owner', 'active', :now, :now, :now)"
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "org_id": org_id,
                        "uid": user_id,
                        "now": now_iso,
                    },
                )
                target_org_id = org_id
            else:
                target_org_id = existing_org[0]

            # Backfill workspaces
            workspaces = bind.execute(
                sa.text("SELECT id FROM workspaces WHERE owner_user_id = :uid"),
                {"uid": user_id},
            ).fetchall()

            for ws in workspaces:
                ws_id = ws[0]
                bind.execute(
                    sa.text("UPDATE workspaces SET organization_id = :org_id WHERE id = :ws_id AND organization_id IS NULL"),
                    {"org_id": target_org_id, "ws_id": ws_id},
                )
                # Ensure workspace membership exists
                existing_wm = bind.execute(
                    sa.text("SELECT id FROM workspace_members WHERE workspace_id = :ws_id AND user_id = :uid"),
                    {"ws_id": ws_id, "uid": user_id},
                ).fetchone()
                if not existing_wm:
                    bind.execute(
                        sa.text(
                            "INSERT INTO workspace_members (id, workspace_id, user_id, role, status, created_at, updated_at) "
                            "VALUES (:id, :ws_id, :uid, 'admin', 'active', :now, :now)"
                        ),
                        {
                            "id": str(uuid.uuid4()),
                            "ws_id": ws_id,
                            "uid": user_id,
                            "now": now_iso,
                        },
                    )


def downgrade() -> None:
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.drop_column("owner_user_id")

    with op.batch_alter_table("projects") as batch_op:
        batch_op.drop_column("access_mode")

    with op.batch_alter_table("workspaces") as batch_op:
        batch_op.drop_column("status")
        batch_op.drop_column("organization_id")

    op.drop_table("project_members")
    op.drop_table("workspace_members")
    op.drop_table("organization_invitations")
    op.drop_table("organization_members")
    op.drop_table("organizations")
