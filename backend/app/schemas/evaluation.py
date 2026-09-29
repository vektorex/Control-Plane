from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from backend.app.services.evaluation.schemas import (
    CheckResult,
    EvaluationMode,
    EvaluationRecommendation,
    EvaluationResult,
    EvaluationStatus,
    UnsupportedClaim,
)


class EvaluationFindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    evaluation_run_id: UUID
    check_type: str
    status: str
    confidence: float
    description: str
    evidence_ids: Optional[List[str]] = None
    metadata_snapshot: Optional[Dict[str, Any]] = None
    created_at: datetime


class EvaluationRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    run_id: UUID
    status: str
    evaluator_type: str
    recommendation: str
    mode: str
    attempt: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = 0
    raw_summary: Optional[str] = None
    findings: List[EvaluationFindingResponse] = Field(default_factory=list)
    created_at: datetime


class EvaluateTaskRequest(BaseModel):
    mode: Optional[str] = Field(default=None, description="Evaluation mode: off | basic | standard | strict")
    strict: Optional[bool] = Field(default=False, description="Strict evaluation mode toggle")
    expected_format: Optional[str] = Field(default=None, description="Expected format: json | table | list | code")
    max_revisions: Optional[int] = Field(default=2, ge=0, le=3, description="Max revision attempts")


class EvaluateTaskResponse(BaseModel):
    evaluation_run: EvaluationRunResponse
    result: EvaluationResult


class RunEvaluationHistoryResponse(BaseModel):
    run_id: UUID
    evaluation_runs: List[EvaluationRunResponse]
    total_evaluations: int
    latest_status: Optional[str] = None
    latest_recommendation: Optional[str] = None
