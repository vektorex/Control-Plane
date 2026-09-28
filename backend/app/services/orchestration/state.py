import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from backend.app.services.orchestration.plan import ExecutionPlan, StepStatus


class ExecutionStepRecord(BaseModel):
    """
    Detailed telemetry and runtime status record for a single executed plan step.
    """
    model_config = ConfigDict(use_enum_values=True)

    id: str = Field(default_factory=lambda: f"step-rec-{uuid.uuid4().hex[:8]}")
    step_id: str = Field(..., description="Corresponds to ExecutionStepPlan.id")
    step_index: int = Field(..., description="0-based sequence index")
    step_type: str = Field(..., description="Type of step executed (context, retrieve, tool, generate)")
    status: StepStatus = Field(default=StepStatus.PENDING)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = Field(default=0, ge=0)
    tool_name: Optional[str] = None
    retrieval_strategy: Optional[str] = None
    output_summary: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    def mark_started(self) -> None:
        self.status = StepStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)

    def mark_completed(self, summary: Optional[Dict[str, Any]] = None) -> None:
        self.status = StepStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)
        if summary:
            self.output_summary = summary

    def mark_failed(self, error_code: str, error_message: str) -> None:
        self.status = StepStatus.FAILED
        self.completed_at = datetime.now(timezone.utc)
        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)
        self.error_code = error_code
        self.error_message = error_message


class ExecutionState(BaseModel):
    """
    Ephemerally managed runtime state of an orchestration execution plan.
    Strictly isolated per-execution and cleared upon run persistence.
    """
    model_config = ConfigDict(use_enum_values=True)

    task_id: str
    plan: ExecutionPlan
    current_step_index: int = 0
    iteration: int = 1
    planning_mode: str = "hybrid"
    planner_model: Optional[str] = None
    proposed_plan: Optional[Dict[str, Any]] = None
    validated_plan: Optional[Dict[str, Any]] = None
    validation_errors: List[str] = Field(default_factory=list)
    repair_count: int = 0
    completion_evaluation: Optional[Dict[str, Any]] = None
    action_history: List[str] = Field(default_factory=list)

    step_records: List[ExecutionStepRecord] = Field(default_factory=list)
    context_items: List[Any] = Field(default_factory=list)
    retrieval_results: List[Any] = Field(default_factory=list)
    tool_results: List[Any] = Field(default_factory=list)
    generated_output: Optional[str] = None
    token_usage: Dict[str, int] = Field(default_factory=lambda: {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0})
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    elapsed_time_ms: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def get_or_create_step_record(self, step_id: str, step_index: int, step_type: str, tool_name: Optional[str] = None, retrieval_strategy: Optional[str] = None) -> ExecutionStepRecord:
        for rec in self.step_records:
            if rec.step_id == step_id:
                return rec
        record = ExecutionStepRecord(
            step_id=step_id,
            step_index=step_index,
            step_type=step_type,
            tool_name=tool_name,
            retrieval_strategy=retrieval_strategy,
        )
        self.step_records.append(record)
        return record

    def record_error(self, step_id: str, error_code: str, error_message: str) -> None:
        self.errors.append({
            "step_id": step_id,
            "error_code": error_code,
            "error_message": error_message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def complete(self) -> None:
        self.completed_at = datetime.now(timezone.utc)
        delta = self.completed_at - self.started_at
        self.elapsed_time_ms = int(delta.total_seconds() * 1000)

    @property
    def is_completed(self) -> bool:
        return self.completed_at is not None

