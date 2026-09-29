import enum
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EvaluationMode(str, enum.Enum):
    """Execution policy modes for the evaluation engine."""
    OFF = "off"
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"


class EvaluationStatus(str, enum.Enum):
    """Overall outcome status of an evaluation run."""
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    SKIPPED = "skipped"


class EvaluationRecommendation(str, enum.Enum):
    """Engine recommendation for orchestrator lifecycle decision."""
    ACCEPT = "accept"
    REVISE = "revise"
    FAIL = "fail"


class CheckType(str, enum.Enum):
    """Verification check categories."""
    GROUNDING = "grounding"
    COMPLETENESS = "completeness"
    CITATION = "citation"
    FORMAT = "format"
    SAFETY = "safety"


class FindingStatus(str, enum.Enum):
    """Status for an individual verification check."""
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    INFO = "info"


class UnsupportedClaim(BaseModel):
    """Specific unsupported or ungrounded statement with rationale and evidence links."""
    claim: str = Field(..., description="The unsupported assertion in the output")
    reason: str = Field(..., description="Explanation of why the context does not support this claim")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Probabilistic confidence score")
    evidence_ids: List[str] = Field(default_factory=list, description="IDs of context/document items checked")


class EvaluationFindingItem(BaseModel):
    """Atomic evaluation finding with evidence references for auditability."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    check_type: CheckType
    status: FindingStatus
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    description: str
    evidence_ids: List[str] = Field(default_factory=list, description="Context, document, or web source IDs")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CheckResult(BaseModel):
    """Outcome of a single evaluator module execution."""
    type: CheckType
    status: FindingStatus
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    description: Optional[str] = None
    issues: List[Any] = Field(default_factory=list)
    findings: List[EvaluationFindingItem] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    duration_ms: int = Field(default=0, ge=0)


class EvaluationResult(BaseModel):
    """
    Complete structured verification result returned by the EvaluationEngine.
    Note: Does NOT compute an arbitrary single numeric quality score.
    """
    status: EvaluationStatus = Field(..., description="passed | warning | failed | skipped")
    recommendation: EvaluationRecommendation = Field(..., description="accept | revise | fail")
    mode: EvaluationMode = Field(default=EvaluationMode.STANDARD)
    attempt: int = Field(default=1, ge=1)
    checks: List[CheckResult] = Field(default_factory=list)
    findings: List[EvaluationFindingItem] = Field(default_factory=list)
    summary: str = Field(default="")
    duration_ms: int = Field(default=0, ge=0)
    revision_suggested: bool = Field(default=False)
    revision_reasons: List[str] = Field(default_factory=list)
    unsupported_claims: List[UnsupportedClaim] = Field(default_factory=list)
    missing_requirements: List[str] = Field(default_factory=list)
    format_issues: List[str] = Field(default_factory=list)
    citation_issues: List[str] = Field(default_factory=list)
    safety_issues: List[str] = Field(default_factory=list)


class EvaluationContext(BaseModel):
    """
    Sanitized, trusted execution context passed to evaluators.
    External retrieved items are marked with stable IDs and untrusted boundaries.
    """
    task_id: str
    task_title: str = ""
    task_instructions: str
    output_text: str
    context_items: List[Any] = Field(default_factory=list)
    retrieval_sources: List[Any] = Field(default_factory=list)
    web_sources: List[Any] = Field(default_factory=list)
    sources: List[Any] = Field(default_factory=list)
    expected_format: Optional[str] = None
    format_schema: Optional[Dict[str, Any]] = None
    required_sections: List[str] = Field(default_factory=list)
    attempt: int = 1

