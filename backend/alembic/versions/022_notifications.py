"""Step 25: Notifications & External Delivery Layer

Revision ID: 022_notifications
Revises: 021_durable_jobs
Create Date: 2026-10-02 23:55:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from backend.app.db.models.guid import GUID

# revision identifiers, used by Alembic.
revision: str = "022_notifications"
down_revision: Union[str, None] = "021_durable_jobs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name if bind else "postgresql"

    # 1. Upgrade notifications table columns if existing, or create if not present
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if "notifications" in tables:
        columns = [c["name"] for c in inspector.get_columns("notifications")]
        if "project_id" not in columns:
            op.add_column("notifications", sa.Column("project_id", GUID(), nullable=True))
            if dialect != "sqlite":
                op.create_foreign_key(
                    "fk_notifications_project_id", "notifications", "projects", ["project_id"], ["id"], ondelete="SET NULL"
                )
        if "event_type" not in columns:
            op.add_column("notifications", sa.Column("event_type", sa.String(length=100), nullable=True))
            # Sync existing type to event_type
            if "type" in columns:
                op.execute("UPDATE notifications SET event_type = type WHERE event_type IS NULL")
            if dialect != "sqlite":
                op.alter_column("notifications", "event_type", nullable=False)
            op.create_index("ix_notifications_ws_event_type", "notifications", ["workspace_id", "event_type"], unique=False)
        if "body" not in columns:
            op.add_column("notifications", sa.Column("body", sa.Text(), nullable=True))
            if "message" in columns:
                op.execute("UPDATE notifications SET body = message WHERE body IS NULL")
            if dialect != "sqlite":
                op.alter_column("notifications", "body", nullable=False)
        if "severity" not in columns:
            op.add_column("notifications", sa.Column("severity", sa.String(length=20), nullable=False, server_default="info"))
            op.create_index("ix_notifications_severity", "notifications", ["severity"], unique=False)
        if "status" not in columns:
            op.add_column("notifications", sa.Column("status", sa.String(length=20), nullable=False, server_default="unread"))
            if "read" in columns:
                op.execute("UPDATE notifications SET status = 'read' WHERE read = true")
            op.create_index("ix_notifications_status", "notifications", ["status"], unique=False)
        if "source_type" not in columns:
            op.add_column("notifications", sa.Column("source_type", sa.String(length=50), nullable=True))
            if "reference_type" in columns:
                op.execute("UPDATE notifications SET source_type = reference_type WHERE source_type IS NULL")
        if "source_id" not in columns:
            op.add_column("notifications", sa.Column("source_id", sa.String(length=255), nullable=True))
            if "reference_id" in columns:
                op.execute("UPDATE notifications SET source_id = reference_id WHERE source_id IS NULL")
        if "metadata_json" not in columns:
            op.add_column("notifications", sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"))
        if "updated_at" not in columns:
            op.add_column("notifications", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
        if "read_at" not in columns:
            op.add_column("notifications", sa.Column("read_at", sa.DateTime(timezone=True), nullable=True))
        if "user_id" in columns and dialect == "postgresql":
            op.alter_column("notifications", "user_id", nullable=True)
    else:
        op.create_table(
            "notifications",
            sa.Column("id", GUID(), nullable=False),
            sa.Column("workspace_id", GUID(), nullable=False),
            sa.Column("project_id", GUID(), nullable=True),
            sa.Column("user_id", GUID(), nullable=True),
            sa.Column("event_type", sa.String(length=100), nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column("severity", sa.String(length=20), nullable=False, server_default="info"),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="unread"),
            sa.Column("source_type", sa.String(length=50), nullable=True),
            sa.Column("source_id", sa.String(length=255), nullable=True),
            sa.Column("metadata_json", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_notifications_id", "notifications", ["id"], unique=False)
        op.create_index("ix_notifications_workspace_id", "notifications", ["workspace_id"], unique=False)
        op.create_index("ix_notifications_event_type", "notifications", ["workspace_id", "event_type"], unique=False)
        op.create_index("ix_notifications_status", "notifications", ["status"], unique=False)
        op.create_index("ix_notifications_severity", "notifications", ["severity"], unique=False)
        op.create_index("ix_notifications_created", "notifications", ["workspace_id", "created_at"], unique=False)

    # 2. notification_deliveries table
    op.create_table(
        "notification_deliveries",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("notification_id", GUID(), nullable=False),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("channel", sa.String(length=50), nullable=False),
        sa.Column("destination", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="queued"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("provider_message_id", sa.String(length=255), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["notification_id"], ["notifications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notification_deliveries_id", "notification_deliveries", ["id"], unique=False)
    op.create_index("ix_notification_deliveries_notif_id", "notification_deliveries", ["notification_id"], unique=False)
    op.create_index("ix_notification_deliveries_workspace_id", "notification_deliveries", ["workspace_id"], unique=False)
    op.create_index("ix_delivery_status_sched", "notification_deliveries", ["status", "scheduled_at"], unique=False)
    op.create_index("ix_delivery_idempotency", "notification_deliveries", ["notification_id", "channel", "destination"], unique=False)
    op.create_index("ix_delivery_workspace_channel", "notification_deliveries", ["workspace_id", "channel", "status"], unique=False)

    # 3. webhook_endpoints table
    op.create_table(
        "webhook_endpoints",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("url", sa.String(length=1000), nullable=False),
        sa.Column("secret_reference", sa.String(length=255), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("subscribed_events", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_webhook_endpoints_id", "webhook_endpoints", ["id"], unique=False)
    op.create_index("ix_webhook_workspace_active", "webhook_endpoints", ["workspace_id", "active"], unique=False)

    # 4. notification_preferences table
    op.create_table(
        "notification_preferences",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("user_id", GUID(), nullable=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("channel", sa.String(length=50), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_id", "user_id", "event_type", "channel", name="uq_notification_preference"),
    )
    op.create_index("ix_notification_preferences_id", "notification_preferences", ["id"], unique=False)
    op.create_index("ix_notif_pref_lookup", "notification_preferences", ["workspace_id", "user_id", "event_type"], unique=False)


def downgrade() -> None:
    op.drop_table("notification_preferences")
    op.drop_table("webhook_endpoints")
    op.drop_table("notification_deliveries")
    # Leave notifications intact to avoid breaking legacy HITL dependencies
