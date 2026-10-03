"""
Pydantic schemas for Step 33: Data Governance, Privacy & Compliance Evidence Layer.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Data Assets & Inventory
# ---------------------------------------------------------------------------

class DataAssetBase(BaseModel):
    name: str
    description: Optional[str] = None
    asset_type: str = Field(description="e.g. document, artifact, memory, run, task, cache_entry, etc.")
    resource_type: str = Field(description="Subsystem resource domain")
    resource_id: str
    data_classification: str = Field(default="internal")
    owner_type: str = Field(default="user")
    owner_id: str
    source_type: str = Field(default="direct")
    source_id: Optional[str] = None
    storage_location: str = Field(default="logical:db")
    contains_personal_data: bool = False
    contains_sensitive_data: bool = False
    contains_secrets: bool = False
    retention_policy_id: Optional[str] = None
    workspace_id: Optional[str] = None
    project_id: Optional[str] = None


class DataAssetCreate(DataAssetBase):
    pass


class DataAssetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    data_classification: Optional[str] = None
    retention_policy_id: Optional[str] = None
    status: Optional[str] = None
    contains_personal_data: Optional[bool] = None
    contains_sensitive_data: Optional[bool] = None
    contains_secrets: Optional[bool] = None


class DataFindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    asset_id: str
    finding_type: str
    location: Optional[str] = None
    redaction_strategy: str
    confidence: float
    fingerprint: str
    preview: Optional[str] = None
    created_at: datetime


class ClassificationRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    asset_id: str
    classification: str
    reason: Optional[str] = None
    detected_by: str
    confidence: float
    created_at: datetime
    updated_at: datetime
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None


class DataAssetResponse(DataAssetBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    last_accessed_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    classifications: List[ClassificationRecordResponse] = []
    findings: List[DataFindingResponse] = []


class ClassificationReviewRequest(BaseModel):
    asset_id: str
    target_classification: str
    reason: str
    reviewed_by: Optional[str] = None


# ---------------------------------------------------------------------------
# Data Lineage
# ---------------------------------------------------------------------------

class LineageEdgeCreate(BaseModel):
    source_asset_id: str
    target_asset_id: str
    relationship_type: str
    transformation_type: str
    metadata: Optional[Dict[str, Any]] = None


class LineageEdgeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    organization_id: str
    source_asset_id: str
    target_asset_id: str
    relationship_type: str
    transformation_type: str
    created_at: datetime
    created_by: Optional[str] = None
    edge_metadata: Optional[Dict[str, Any]] = Field(default=None, alias="metadata")


class LineageGraphNode(BaseModel):
    id: str
    name: str
    asset_type: str
    resource_type: str
    classification: str
    status: str


class LineageGraphResponse(BaseModel):
    root_asset_id: str
    nodes: List[LineageGraphNode]
    edges: List[LineageEdgeResponse]


# ---------------------------------------------------------------------------
# Retention Policies
# ---------------------------------------------------------------------------

class RetentionPolicyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    resource_type: str
    retention_days: Optional[int] = None
    action: str = Field(default="retain", description="retain, archive, anonymize, delete")
    grace_period_days: int = 7
    enabled: bool = True
    workspace_id: Optional[str] = None


class RetentionPolicyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    retention_days: Optional[int] = None
    action: Optional[str] = None
    grace_period_days: Optional[int] = None
    enabled: Optional[bool] = None


class RetentionPolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    workspace_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    resource_type: str
    retention_days: Optional[int] = None
    action: str
    grace_period_days: int
    enabled: bool
    created_by: str
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Deletion System
# ---------------------------------------------------------------------------

class DeletionRequestCreate(BaseModel):
    scope_type: str = Field(description="asset, resource, workspace, user")
    scope_id: str
    reason: Optional[str] = None
    workspace_id: Optional[str] = None


class DeletionRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    workspace_id: Optional[str] = None
    requested_by: str
    scope_type: str
    scope_id: str
    reason: Optional[str] = None
    status: str
    requested_at: datetime
    approved_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    verification_status: str
    verification_summary: Optional[str] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Export System
# ---------------------------------------------------------------------------

class ExportRequestCreate(BaseModel):
    scope_type: str
    scope_id: str
    format: str = Field(default="json", description="json, jsonl, csv")
    workspace_id: Optional[str] = None


class ExportManifest(BaseModel):
    export_id: str
    organization_id: str
    workspace_id: Optional[str] = None
    scope_type: str
    scope_id: str
    format: str
    asset_count: int
    assets: List[Dict[str, Any]]
    created_at: datetime
    sanitized: bool = True
    version: str = "1.0"


class ExportRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    workspace_id: Optional[str] = None
    requested_by: str
    scope_type: str
    scope_id: str
    format: str
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    artifact_id: Optional[str] = None
    manifest: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Privacy Requests
# ---------------------------------------------------------------------------

class PrivacyRequestCreate(BaseModel):
    request_type: str = Field(description="access, export, deletion, correction, restriction")
    scope: str = Field(default="user")
    workspace_id: Optional[str] = None


class PrivacyRequestUpdate(BaseModel):
    status: Optional[str] = None
    verification_status: Optional[str] = None


class PrivacyRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    workspace_id: Optional[str] = None
    requester_user_id: str
    request_type: str
    scope: str
    status: str
    verification_status: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Legal Holds
# ---------------------------------------------------------------------------

class LegalHoldCreate(BaseModel):
    name: str
    reason: Optional[str] = None
    workspace_id: Optional[str] = None
    asset_ids: Optional[List[str]] = Field(default_factory=list)


class LegalHoldReleaseRequest(BaseModel):
    reason: Optional[str] = None


class LegalHoldResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    workspace_id: Optional[str] = None
    name: str
    reason: Optional[str] = None
    status: str
    created_by: str
    created_at: datetime
    released_at: Optional[datetime] = None
    asset_count: int = 0


# ---------------------------------------------------------------------------
# Compliance Evidence
# ---------------------------------------------------------------------------

class ComplianceEvidenceCreate(BaseModel):
    evidence_type: str
    subject_type: str
    subject_id: str
    action: str
    result: str
    actor_type: str = "user"
    actor_id: Optional[str] = None
    policy_version_id: Optional[str] = None
    governance_decision_id: Optional[str] = None
    workspace_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ComplianceEvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    organization_id: str
    workspace_id: Optional[str] = None
    evidence_type: str
    subject_type: str
    subject_id: str
    action: str
    result: str
    policy_version_id: Optional[str] = None
    governance_decision_id: Optional[str] = None
    actor_type: str
    actor_id: Optional[str] = None
    timestamp: datetime
    evidence_hash: str
    previous_evidence_hash: Optional[str] = None
    evidence_metadata: Optional[Dict[str, Any]] = Field(default=None, alias="metadata")


class EvidenceVerificationResult(BaseModel):
    valid: bool
    total_records: int
    broken_links: List[str] = []
    message: str


# ---------------------------------------------------------------------------
# Data Access Records
# ---------------------------------------------------------------------------

class DataAccessRecordCreate(BaseModel):
    asset_id: str
    actor_type: str = "user"
    actor_id: str
    action: str
    result: str
    workspace_id: Optional[str] = None
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None


class DataAccessRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    workspace_id: Optional[str] = None
    asset_id: str
    actor_type: str
    actor_id: str
    action: str
    result: str
    timestamp: datetime
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Overview & Reports
# ---------------------------------------------------------------------------

class DataGovernanceOverviewResponse(BaseModel):
    total_assets: int = 0
    classification_counts: Dict[str, int] = {}
    active_legal_holds: int = 0
    pending_deletions: int = 0
    pending_privacy_requests: int = 0
    recent_evidence_count: int = 0
    assets_with_findings: int = 0
    evidence_chain_valid: bool = True


class RetentionReportResponse(BaseModel):
    total_policies: int
    policies_by_action: Dict[str, int]
    assets_expiring_soon: int
    assets_expired: int


class ClassificationReportResponse(BaseModel):
    total_classified: int
    distribution: Dict[str, int]
    recent_reviews: int
    unreviewed_sensitive_assets: int


class AccessReportResponse(BaseModel):
    total_access_events: int
    actions_distribution: Dict[str, int]
    denied_access_count: int


class DeletionReportResponse(BaseModel):
    total_requests: int
    completed: int
    blocked: int
    failed: int


class EvidenceReportResponse(BaseModel):
    total_records: int
    chain_valid: bool
    evidence_types_distribution: Dict[str, int]
