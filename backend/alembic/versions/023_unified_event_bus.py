"""Step 26: Unified Event Bus and Real-Time Execution Updates

Revision ID: 023_unified_event_bus
Revises: 022_notifications
Create Date: 2026-10-03 00:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from backend.app.db.models.guid import GUID

# revision identifiers, used by Alembic.
revision: str = "023_unified_event_bus"
down_revision: Union[str, None] = "022_notifications"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name if bind else "postgresql"
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    # 1. Create events table
    if "events" not in tables:
        op.create_table(
            "events",
            sa.Column("id", GUID(), nullable=False),
            sa.Column("workspace_id", GUID(), nullable=False),
            sa.Column("project_id", GUID(), nullable=True),
            sa.Column("actor_type", sa.String(length=50), nullable=False, server_default="system"),
            sa.Column("actor_id", sa.String(length=255), nullable=True),
            sa.Column("event_type", sa.String(length=100), nullable=False),
            sa.Column("aggregate_type", sa.String(length=50), nullable=False),
            sa.Column("aggregate_id", sa.String(length=255), nullable=False),
            sa.Column("parent_event_id", GUID(), nullable=True),
            sa.Column("correlation_id", sa.String(length=255), nullable=True),
            sa.Column("causation_id", sa.String(length=255), nullable=True),
            sa.Column("sequence_number", sa.Integer(), nullable=True),
            sa.Column("idempotency_key", sa.String(length=255), nullable=True),
            sa.Column("payload", sa.JSON(), nullable=False),
            sa.Column("metadata_json", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("workspace_id", "idempotency_key", name="uq_events_workspace_idempotency"),
        )
        op.create_index("ix_events_id", "events", ["id"], unique=False)
        op.create_index("ix_events_workspace_id", "events", ["workspace_id"], unique=False)
        op.create_index("ix_events_project_id", "events", ["project_id"], unique=False)
        op.create_index("ix_events_event_type", "events", ["event_type"], unique=False)
        op.create_index("ix_events_aggregate_type", "events", ["aggregate_type"], unique=False)
        op.create_index("ix_events_aggregate_id", "events", ["aggregate_id"], unique=False)
        op.create_index("ix_events_correlation_id", "events", ["correlation_id"], unique=False)
        op.create_index("ix_events_created_at", "events", ["created_at"], unique=False)
        op.create_index("ix_events_ws_created", "events", ["workspace_id", "created_at"], unique=False)
        op.create_index("ix_events_ws_event_type", "events", ["workspace_id", "event_type"], unique=False)
        op.create_index("ix_events_ws_aggregate", "events", ["workspace_id", "aggregate_type", "aggregate_id"], unique=False)
        op.create_index("ix_events_aggregate_sequence", "events", ["workspace_id", "aggregate_type", "aggregate_id", "sequence_number"], unique=False)
        op.create_index("ix_events_ws_correlation", "events", ["workspace_id", "correlation_id"], unique=False)

    # 2. Create event_deliveries table
    if "event_deliveries" not in tables:
        op.create_table(
            "event_deliveries",
            sa.Column("id", GUID(), nullable=False),
            sa.Column("event_id", GUID(), nullable=False),
            sa.Column("consumer_name", sa.String(length=100), nullable=False),
            sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
            sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("available_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("error_code", sa.String(length=100), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("event_id", "consumer_name", name="uq_event_deliveries_event_consumer"),
        )
        op.create_index("ix_event_deliveries_id", "event_deliveries", ["id"], unique=False)
        op.create_index("ix_event_deliveries_event_id", "event_deliveries", ["event_id"], unique=False)
        op.create_index("ix_event_deliveries_consumer_name", "event_deliveries", ["consumer_name"], unique=False)
        op.create_index("ix_event_deliveries_status", "event_deliveries", ["status"], unique=False)
        op.create_index("ix_event_deliveries_available_at", "event_deliveries", ["available_at"], unique=False)
        op.create_index("ix_event_deliveries_status_available", "event_deliveries", ["status", "available_at"], unique=False)


def downgrade() -> None:
    op.drop_table("event_deliveries")
    op.drop_table("events")
