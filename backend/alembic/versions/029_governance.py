"""Alembic migration 029: AI Governance tables — governance_policies,
governance_policy_versions, budget_policies, budget_reservations, governance_decisions.
Step 32.
"""
from alembic import op
import sqlalchemy as sa

revision = "029"
down_revision = "028_semantic_cache"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # governance_policies
    op.create_table(
        "governance_policies",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), nullable=False),
        sa.Column("workspace_id", sa.String(36), nullable=True),
        sa.Column("project_id", sa.String(36), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("priority", sa.Integer, nullable=False, server_default="100"),
        sa.Column("scope", sa.String(32), nullable=False, server_default="workspace"),
        sa.Column("active_version_id", sa.String(36), nullable=True),
        sa.Column("created_by", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_gov_policy_id", "governance_policies", ["id"])
    op.create_index("ix_gov_policy_org", "governance_policies", ["organization_id"])
    op.create_index("ix_gov_policy_workspace", "governance_policies", ["workspace_id"])
    op.create_index("ix_gov_policy_project", "governance_policies", ["project_id"])
    op.create_index("ix_gov_policy_status", "governance_policies", ["status"])
    op.create_index("ix_gov_policy_priority", "governance_policies", ["priority"])
    op.create_index(
        "ix_gov_policy_org_scope_status",
        "governance_policies",
        ["organization_id", "scope", "status"],
    )
    op.create_index(
        "ix_gov_policy_workspace_status",
        "governance_policies",
        ["workspace_id", "status", "priority"],
    )
    op.create_index(
        "ix_gov_policy_project_status",
        "governance_policies",
        ["project_id", "status"],
    )

    # governance_policy_versions
    op.create_table(
        "governance_policy_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("policy_id", sa.String(36), nullable=False),
        sa.Column("version_number", sa.Integer, nullable=False),
        sa.Column("rules", sa.JSON, nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("change_summary", sa.Text, nullable=True),
        sa.Column("created_by", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("policy_id", "version_number", name="uq_policy_version_number"),
    )
    op.create_index("ix_gov_policy_ver_id", "governance_policy_versions", ["id"])
    op.create_index("ix_gov_policy_ver_policy", "governance_policy_versions", ["policy_id"])
    op.create_index("ix_gov_policy_ver_status", "governance_policy_versions", ["policy_id", "status"])
    op.create_index("ix_gov_policy_ver_number", "governance_policy_versions", ["version_number"])

    # budget_policies
    op.create_table(
        "budget_policies",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), nullable=False),
        sa.Column("workspace_id", sa.String(36), nullable=True),
        sa.Column("project_id", sa.String(36), nullable=True),
        sa.Column("daily_limit_usd", sa.Float, nullable=True),
        sa.Column("monthly_limit_usd", sa.Float, nullable=True),
        sa.Column("per_run_limit_usd", sa.Float, nullable=True),
        sa.Column("per_user_daily_limit_usd", sa.Float, nullable=True),
        sa.Column("soft_threshold_pct", sa.Float, nullable=False, server_default="0.80"),
        sa.Column("hard_threshold_pct", sa.Float, nullable=False, server_default="1.00"),
        sa.Column("on_soft_breach", sa.String(32), nullable=False, server_default="warn"),
        sa.Column("on_hard_breach", sa.String(32), nullable=False, server_default="deny"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("created_by", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )
    op.create_index("ix_budget_policy_id", "budget_policies", ["id"])
    op.create_index("ix_budget_policy_org", "budget_policies", ["organization_id"])
    op.create_index("ix_budget_policy_workspace", "budget_policies", ["workspace_id", "is_active"])
    op.create_index("ix_budget_policy_project", "budget_policies", ["project_id", "is_active"])

    # budget_reservations
    op.create_table(
        "budget_reservations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), nullable=False),
        sa.Column("workspace_id", sa.String(36), nullable=False),
        sa.Column("project_id", sa.String(36), nullable=True),
        sa.Column("user_id", sa.String(36), nullable=True),
        sa.Column("run_id", sa.String(36), nullable=True),
        sa.Column("job_id", sa.String(36), nullable=True),
        sa.Column("reserved_amount_usd", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("actual_amount_usd", sa.Float, nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("settled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_budget_reservation_id", "budget_reservations", ["id"])
    op.create_index("ix_budget_reservation_workspace", "budget_reservations", ["workspace_id"])
    op.create_index(
        "ix_budget_reservation_active",
        "budget_reservations",
        ["workspace_id", "status", "expires_at"],
    )
    op.create_index("ix_budget_reservation_run", "budget_reservations", ["run_id", "status"])

    # governance_decisions (audit log)
    op.create_table(
        "governance_decisions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), nullable=False),
        sa.Column("workspace_id", sa.String(36), nullable=True),
        sa.Column("project_id", sa.String(36), nullable=True),
        sa.Column("user_id", sa.String(36), nullable=True),
        sa.Column("enforcement_point", sa.String(64), nullable=False),
        sa.Column("decision", sa.String(32), nullable=False),
        sa.Column("reasons", sa.JSON, nullable=False),
        sa.Column("matched_policy_ids", sa.JSON, nullable=False),
        sa.Column("policy_version", sa.String(64), nullable=True),
        sa.Column("constraints", sa.JSON, nullable=False),
        sa.Column("required_approvals", sa.JSON, nullable=False),
        sa.Column("required_verifications", sa.JSON, nullable=False),
        sa.Column("evaluation_latency_ms", sa.Integer, nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )
    op.create_index("ix_gov_decision_id", "governance_decisions", ["id"])
    op.create_index("ix_gov_decision_org", "governance_decisions", ["organization_id"])
    op.create_index("ix_gov_decision_workspace", "governance_decisions", ["workspace_id"])
    op.create_index("ix_gov_decision_created", "governance_decisions", ["created_at"])
    op.create_index(
        "ix_gov_decision_workspace_decision",
        "governance_decisions",
        ["workspace_id", "decision", "created_at"],
    )
    op.create_index(
        "ix_gov_decision_enforcement",
        "governance_decisions",
        ["enforcement_point", "decision", "created_at"],
    )
    op.create_index("ix_gov_decision_expires", "governance_decisions", ["expires_at"])


def downgrade() -> None:
    op.drop_table("governance_decisions")
    op.drop_table("budget_reservations")
    op.drop_table("budget_policies")
    op.drop_table("governance_policy_versions")
    op.drop_table("governance_policies")
