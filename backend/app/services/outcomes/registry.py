"""
Controlled registries, enumerations, and validation constants for Step 43:
AI Outcome Intelligence & Work Impact Layer.
"""
from enum import Enum
from typing import Set


class ObjectiveType(str, Enum):
    BUSINESS = "business"
    PRODUCT = "product"
    ENGINEERING = "engineering"
    RESEARCH = "research"
    OPERATIONS = "operations"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    PERSONAL = "personal"
    PROJECT = "project"


class ObjectiveStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    AT_RISK = "at_risk"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class TargetMetricType(str, Enum):
    COUNT = "count"
    PERCENTAGE = "percentage"
    DURATION = "duration"
    CURRENCY = "currency"
    BOOLEAN = "boolean"
    RATE = "rate"
    RATIO = "ratio"
    CUSTOM = "custom"


class MeasurementSource(str, Enum):
    MANUAL = "manual"
    SYSTEM = "system"
    CONNECTOR = "connector"
    WORKFLOW = "workflow"
    EVALUATION = "evaluation"
    EVENT = "event"
    ARTIFACT = "artifact"
    DOCUMENT = "document"
    EXTERNAL_REFERENCE = "external_reference"


class OutcomeType(str, Enum):
    DELIVERABLE = "deliverable"
    DECISION = "decision"
    RESOLUTION = "resolution"
    OPTIMIZATION = "optimization"
    RISK_REDUCTION = "risk_reduction"
    ISSUE_RESOLUTION = "issue_resolution"
    RESEARCH_FINDING = "research_finding"
    AUTOMATION = "automation"
    APPROVAL = "approval"
    MILESTONE = "milestone"
    CUSTOMER_OUTCOME = "customer_outcome"
    OPERATIONAL_OUTCOME = "operational_outcome"
    SECURITY_OUTCOME = "security_outcome"


class OutcomeStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    OBSERVED = "observed"
    VERIFIED = "verified"
    DISPUTED = "disputed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OutcomeConfidence(str, Enum):
    UNVERIFIED = "unverified"
    SUPPORTED = "supported"
    STRONGLY_SUPPORTED = "strongly_supported"
    VERIFIED = "verified"
    DISPUTED = "disputed"


class EvidenceType(str, Enum):
    EXECUTION_RESULT = "execution_result"
    EVALUATION_RESULT = "evaluation_result"
    HUMAN_CONFIRMATION = "human_confirmation"
    ARTIFACT = "artifact"
    DOCUMENT = "document"
    CONNECTOR_RECORD = "connector_record"
    WORKFLOW_RESULT = "workflow_result"
    METRIC_OBSERVATION = "metric_observation"
    SECURITY_EVENT = "security_event"
    SIMULATION_RESULT = "simulation_result"
    COLLABORATION_DECISION = "collaboration_decision"
    EXTERNAL_REFERENCE = "external_reference"


class EvidenceStatus(str, Enum):
    UNREVIEWED = "unreviewed"
    SUPPORTED = "supported"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class MilestoneStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    MISSED = "missed"
    CANCELLED = "cancelled"


class WorkDecisionType(str, Enum):
    HUMAN = "human"
    AI_ASSISTED = "AI_assisted"
    POLICY = "policy"
    WORKFLOW = "workflow"
    AGENT = "agent"
    TEAM = "team"


class WorkDecisionStatus(str, Enum):
    PROPOSED = "proposed"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class WorkLinkRelationship(str, Enum):
    CONTRIBUTES_TO = "contributes_to"
    PRODUCED = "produced"
    SUPPORTS = "supports"
    VALIDATED_BY = "validated_by"
    BLOCKED_BY = "blocked_by"
    DERIVED_FROM = "derived_from"
    MEASURES = "measures"
    IMPLEMENTS = "implements"


class AttributionType(str, Enum):
    DIRECT = "direct"
    SUPPORTING = "supporting"
    CONTRIBUTING = "contributing"
    BLOCKING = "blocking"
    UNKNOWN = "unknown"


class AttributionConfidence(str, Enum):
    OBSERVED = "observed"
    ESTIMATED = "estimated"
    INFERRED = "inferred"


class AttributionSource(str, Enum):
    DETERMINISTIC = "deterministic"
    HUMAN = "human"
    AI_GENERATED_ATTRIBUTION = "AI_GENERATED_ATTRIBUTION"
    AI_GENERATED = "AI_GENERATED_ATTRIBUTION"
    OBSERVED = "observed"


class ImpactAnalysisType(str, Enum):
    TIME_SAVED = "time_saved"
    COST_CHANGE = "cost_change"
    RISK_CHANGE = "risk_change"
    QUALITY_CHANGE = "quality_change"
    THROUGHPUT_CHANGE = "throughput_change"
    RESOLUTION_CHANGE = "resolution_change"
    PROCESS_CHANGE = "process_change"
    OPERATIONAL_CHANGE = "operational_change"


class OutcomeHealthStatus(str, Enum):
    HEALTHY = "healthy"
    AT_RISK = "at_risk"
    BLOCKED = "blocked"
    STALE = "stale"
    VERIFIED = "verified"
    DISPUTED = "disputed"
    FAILED = "failed"


# Supported resource types that can link to an outcome
ALLOWED_WORK_RESOURCE_TYPES: Set[str] = {
    "Task",
    "Run",
    "Workflow",
    "WorkflowRun",
    "AgentRun",
    "AgentTeamRun",
    "Document",
    "Artifact",
    "EvaluationRun",
    "SimulationRun",
    "Decision",
    "CollaborationSession",
}
