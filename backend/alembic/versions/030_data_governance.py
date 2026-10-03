"""Alembic migration 030: Data Governance tables — data_assets,
classification_records, data_findings, data_lineage_edges, retention_policies,
deletion_requests, export_requests, privacy_requests, legal_holds, legal_hold_assets,
compliance_evidence, data_access_records.
Step 33.
"""
from alembic import op
import sqlalchemy as sa

revision = "030"
down_revision = "029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. data_assets
    op.create_table(
        "data_assets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), nullable=False),
        sa.Column("workspace_id", sa.String(36), nullable=True),
        sa.Column("project_id", sa.String(36), nullable=True),
        sa.Column("asset_type", sa.String(50), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("resource_id", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("data_classification", sa.String(32), nullable=False, server_default="internal"),
        sa.Column("owner_type", sa.String(50), nullable=False, server_default="user"),
        sa.Column("owner_id", sa.String(36), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False, server_default="direct"),
        sa.Column("source_id", sa.String(255), nullable=True),
        sa.Column("storage_location", sa.String(255), nullable=False, server_default="logical:db"),
        sa.Column("contains_personal_data", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("contains_sensitive_data", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("contains_secrets", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("retention_policy_id", sa.String(36), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_accessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_data_assets_org", "data_assets", ["organization_id"])
    op.create_index("ix_data_assets_workspace", "data_assets", ["workspace_id"])
    op.create_index("ix_data_assets_project", "data_assets", ["project_id"])
    op.create_index("ix_data_assets_asset_type", "data_assets", ["asset_type"])
    op.create_index("ix_data_assets_res_type_id", "data_assets", ["resource_type", "resource_id"])
    op.create_index("ix_data_assets_classification", "data_assets", ["data_classification"])
    op.create_index("ix_data_assets_status", "data_assets", ["status"])

    # 2. classification_records
    op.create_table(
        "classification_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("asset_id", sa.String(36), sa.ForeignKey("data_assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("classification", sa.String(32), nullable=False),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("detected_by", sa.String(50), nullable=False),
        sa.Column("confidence", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("reviewed_by", sa.String(36), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_class_records_asset", "classification_records", ["asset_id"])
    op.create_index("ix_class_records_class", "classification_records", ["classification"])

    # 3. data_findings
    op.create_table(
        "data_findings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("asset_id", sa.String(36), sa.ForeignKey("data_assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("finding_type", sa.String(50), nullable=False),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("redaction_strategy", sa.String(50), nullable=False, server_default="mask"),
        sa.Column("confidence", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("preview", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_data_findings_asset", "data_findings", ["asset_id"])
    op.create_index("ix_data_findings_type", "data_findings", ["finding_type"])

    # 4. data_lineage_edges
    op.create_table(
        "data_lineage_edges",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), nullable=False),
        sa.Column("source_asset_id", sa.String(36), nullable=False),
        sa.Column("target_asset_id", sa.String(36), nullable=False),
        sa.Column("relationship_type", sa.String(50), nullable=False),
        sa.Column("transformation_type", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("metadata", sa.JSON, nullable=True),
    )
    op.create_index("ix_lineage_org", "data_lineage_edges", ["organization_id"])
    op.create_index("ix_lineage_source", "data_lineage_edges", ["source_asset_id"])
    op.create_index("ix_lineage_target", "data_lineage_edges", ["target_asset_id"])

    # 5. retention_policies
    op.create_table(
        "retention_policies",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), nullable=False),
        sa.Column("workspace_id", sa.String(36), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("retention_days", sa.Integer, nullable=True),
        sa.Column("action", sa.String(32), nullable=False, server_default="retain"),
        sa.Column("grace_period_days", sa.Integer, nullable=False, server_default="7"),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_by", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_ret_policies_org", "retention_policies", ["organization_id"])
    op.create_index("ix_ret_policies_workspace", "retention_policies", ["workspace_id"])
    op.create_index("ix_ret_policies_res_type", "retention_policies", ["resource_type"])

    # 6. deletion_requests
    op.create_table(
        "deletion_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), nullable=False),
        sa.Column("workspace_id", sa.String(36), nullable=True),
        sa.Column("requested_by", sa.String(36), nullable=False),
        sa.Column("scope_type", sa.String(50), nullable=False),
        sa.Column("scope_id", sa.String(255), nullable=False),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="requested"),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verification_status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("verification_summary", sa.Text, nullable=True),
        sa.Column("error", sa.Text, nullable=True),
    )
    op.create_index("ix_deletion_requests_org", "deletion_requests", ["organization_id"])
    op.create_index("ix_deletion_requests_status", "deletion_requests", ["status"])

    # 7. export_requests
    op.create_table(
        "export_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), nullable=False),
        sa.Column("workspace_id", sa.String(36), nullable=True),
        sa.Column("requested_by", sa.String(36), nullable=False),
        sa.Column("scope_type", sa.String(50), nullable=False),
        sa.Column("scope_id", sa.String(255), nullable=False),
        sa.Column("format", sa.String(16), nullable=False, server_default="json"),
        sa.Column("status", sa.String(32), nullable=False, server_default="requested"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("artifact_id", sa.String(36), nullable=True),
        sa.Column("manifest", sa.JSON, nullable=True),
    )
    op.create_index("ix_export_requests_org", "export_requests", ["organization_id"])
    op.create_index("ix_export_requests_status", "export_requests", ["status"])

    # 8. privacy_requests
    op.create_table(
        "privacy_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), nullable=False),
        sa.Column("workspace_id", sa.String(36), nullable=True),
        sa.Column("requester_user_id", sa.String(36), nullable=False),
        sa.Column("request_type", sa.String(32), nullable=False),
        sa.Column("scope", sa.String(255), nullable=False, server_default="user"),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("verification_status", sa.String(32), nullable=False, server_default="unverified"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_privacy_requests_org", "privacy_requests", ["organization_id"])
    op.create_index("ix_privacy_requests_user", "privacy_requests", ["requester_user_id"])
    op.create_index("ix_privacy_requests_status", "privacy_requests", ["status"])

    # 9. legal_holds
    op.create_table(
        "legal_holds",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), nullable=False),
        sa.Column("workspace_id", sa.String(36), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_by", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_legal_holds_org", "legal_holds", ["organization_id"])
    op.create_index("ix_legal_holds_status", "legal_holds", ["status"])

    # 10. legal_hold_assets
    op.create_table(
        "legal_hold_assets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("legal_hold_id", sa.String(36), sa.ForeignKey("legal_holds.id", ondelete="CASCADE"), nullable=False),
        sa.Column("asset_id", sa.String(36), sa.ForeignKey("data_assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_lha_hold", "legal_hold_assets", ["legal_hold_id"])
    op.create_index("ix_lha_asset", "legal_hold_assets", ["asset_id"])

    # 11. compliance_evidence
    op.create_table(
        "compliance_evidence",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), nullable=False),
        sa.Column("workspace_id", sa.String(36), nullable=True),
        sa.Column("evidence_type", sa.String(50), nullable=False),
        sa.Column("subject_type", sa.String(50), nullable=False),
        sa.Column("subject_id", sa.String(255), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("result", sa.String(50), nullable=False),
        sa.Column("policy_version_id", sa.String(36), nullable=True),
        sa.Column("governance_decision_id", sa.String(36), nullable=True),
        sa.Column("actor_type", sa.String(50), nullable=False, server_default="system"),
        sa.Column("actor_id", sa.String(36), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("evidence_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("previous_evidence_hash", sa.String(64), nullable=True),
        sa.Column("metadata", sa.JSON, nullable=True),
    )
    op.create_index("ix_comp_evidence_org", "compliance_evidence", ["organization_id"])
    op.create_index("ix_comp_evidence_type", "compliance_evidence", ["evidence_type"])
    op.create_index("ix_comp_evidence_subject", "compliance_evidence", ["subject_id"])
    op.create_index("ix_comp_evidence_timestamp", "compliance_evidence", ["timestamp"])

    # 12. data_access_records
    op.create_table(
        "data_access_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), nullable=False),
        sa.Column("workspace_id", sa.String(36), nullable=True),
        sa.Column("asset_id", sa.String(36), nullable=False),
        sa.Column("actor_type", sa.String(50), nullable=False, server_default="user"),
        sa.Column("actor_id", sa.String(36), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("result", sa.String(50), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("request_id", sa.String(64), nullable=True),
        sa.Column("correlation_id", sa.String(64), nullable=True),
    )
    op.create_index("ix_data_access_org", "data_access_records", ["organization_id"])
    op.create_index("ix_data_access_asset", "data_access_records", ["asset_id"])
    op.create_index("ix_data_access_actor", "data_access_records", ["actor_id"])


def downgrade() -> None:
    op.drop_table("data_access_records")
    op.drop_table("compliance_evidence")
    op.drop_table("legal_hold_assets")
    op.drop_table("legal_holds")
    op.drop_table("privacy_requests")
    op.drop_table("export_requests")
    op.drop_table("deletion_requests")
    op.drop_table("retention_policies")
    op.drop_table("data_lineage_edges")
    op.drop_table("data_findings")
    op.drop_table("classification_records")
    op.drop_table("data_assets")
