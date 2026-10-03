"""Alembic migration 031: AI Security Operations tables — security_signals,
security_incidents, incident_signals, incident_timeline_events,
security_indicators, security_playbooks, containment_actions.
Step 34.
"""
from alembic import op
import sqlalchemy as sa

revision = "031"
down_revision = "030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. security_signals
    op.create_table(
        "security_signals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), nullable=False),
        sa.Column("workspace_id", sa.String(36), nullable=True),
        sa.Column("project_id", sa.String(36), nullable=True),
        sa.Column("signal_type", sa.String(100), nullable=False),
        sa.Column("source_type", sa.String(100), nullable=False),
        sa.Column("source_id", sa.String(255), nullable=True),
        sa.Column("actor_type", sa.String(50), nullable=True),
        sa.Column("actor_id", sa.String(255), nullable=True),
        sa.Column("resource_type", sa.String(100), nullable=True),
        sa.Column("resource_id", sa.String(255), nullable=True),
        sa.Column("severity", sa.String(32), nullable=False, server_default="low"),
        sa.Column("confidence", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("request_id", sa.String(255), nullable=True),
        sa.Column("correlation_id", sa.String(255), nullable=True),
        sa.Column("causation_id", sa.String(255), nullable=True),
        sa.Column("metadata", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("status", sa.String(50), nullable=False, server_default="new"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_security_signals_org", "security_signals", ["organization_id"])
    op.create_index("ix_security_signals_ws", "security_signals", ["workspace_id"])
    op.create_index("ix_security_signals_type", "security_signals", ["signal_type"])
    op.create_index("ix_security_signals_sev", "security_signals", ["severity"])
    op.create_index("ix_security_signals_status", "security_signals", ["status"])
    op.create_index("ix_security_signals_ts", "security_signals", ["timestamp"])
    op.create_index("ix_security_signals_actor", "security_signals", ["actor_id"])
    op.create_index("ix_security_signals_res", "security_signals", ["resource_id"])

    # 2. security_incidents
    op.create_table(
        "security_incidents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), nullable=False),
        sa.Column("workspace_id", sa.String(36), nullable=True),
        sa.Column("project_id", sa.String(36), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("category", sa.String(100), nullable=False, server_default="unknown"),
        sa.Column("severity", sa.String(32), nullable=False, server_default="medium"),
        sa.Column("status", sa.String(50), nullable=False, server_default="open"),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("assigned_to", sa.String(255), nullable=True),
        sa.Column("resolved_by", sa.String(255), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_summary", sa.Text, nullable=True),
        sa.Column("metadata", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_security_incidents_org", "security_incidents", ["organization_id"])
    op.create_index("ix_security_incidents_ws", "security_incidents", ["workspace_id"])
    op.create_index("ix_security_incidents_cat", "security_incidents", ["category"])
    op.create_index("ix_security_incidents_sev", "security_incidents", ["severity"])
    op.create_index("ix_security_incidents_status", "security_incidents", ["status"])
    op.create_index("ix_security_incidents_last_seen", "security_incidents", ["last_seen_at"])

    # 3. incident_signals
    op.create_table(
        "incident_signals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("incident_id", sa.String(36), sa.ForeignKey("security_incidents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("signal_id", sa.String(36), sa.ForeignKey("security_signals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relationship", sa.String(50), nullable=False, server_default="related"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_incident_signals_inc", "incident_signals", ["incident_id"])
    op.create_index("ix_incident_signals_sig", "incident_signals", ["signal_id"])

    # 4. incident_timeline_events
    op.create_table(
        "incident_timeline_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("incident_id", sa.String(36), sa.ForeignKey("security_incidents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("source_type", sa.String(100), nullable=False),
        sa.Column("source_id", sa.String(255), nullable=True),
        sa.Column("actor_type", sa.String(50), nullable=True),
        sa.Column("actor_id", sa.String(255), nullable=True),
        sa.Column("summary", sa.Text, nullable=False),
        sa.Column("metadata", sa.JSON, nullable=False, server_default="{}"),
    )
    op.create_index("ix_incident_timeline_inc", "incident_timeline_events", ["incident_id"])
    op.create_index("ix_incident_timeline_ts", "incident_timeline_events", ["timestamp"])

    # 5. security_indicators
    op.create_table(
        "security_indicators",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), nullable=False),
        sa.Column("indicator_type", sa.String(100), nullable=False),
        sa.Column("value_hash", sa.String(64), nullable=False),
        sa.Column("value_display", sa.String(255), nullable=False),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("confidence", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("metadata", sa.JSON, nullable=False, server_default="{}"),
    )
    op.create_index("ix_security_indicators_org", "security_indicators", ["organization_id"])
    op.create_index("ix_security_indicators_type", "security_indicators", ["indicator_type"])
    op.create_index("ix_security_indicators_hash", "security_indicators", ["value_hash"])

    # 6. security_playbooks
    op.create_table(
        "security_playbooks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("trigger_conditions", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("actions", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_security_playbooks_org", "security_playbooks", ["organization_id"])

    # 7. containment_actions
    op.create_table(
        "containment_actions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("incident_id", sa.String(36), sa.ForeignKey("security_incidents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action_type", sa.String(100), nullable=False),
        sa.Column("target_type", sa.String(100), nullable=False),
        sa.Column("target_id", sa.String(255), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="requested"),
        sa.Column("requested_by", sa.String(255), nullable=False),
        sa.Column("approved_by", sa.String(255), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("reason", sa.Text, nullable=False),
    )
    op.create_index("ix_containment_actions_inc", "containment_actions", ["incident_id"])
    op.create_index("ix_containment_actions_status", "containment_actions", ["status"])
    op.create_index("ix_containment_actions_type", "containment_actions", ["action_type"])


def downgrade() -> None:
    op.drop_table("containment_actions")
    op.drop_table("security_playbooks")
    op.drop_table("security_indicators")
    op.drop_table("incident_timeline_events")
    op.drop_table("incident_signals")
    op.drop_table("security_incidents")
    op.drop_table("security_signals")
