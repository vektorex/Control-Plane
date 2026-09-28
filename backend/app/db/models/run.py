import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from backend.app.db.models.enums import RunStatus
from backend.app.db.models.guid import GUID

if TYPE_CHECKING:
    from backend.app.db.models.task import Task


class Run(Base):
    """
    Run entity capturing execution telemetry, snapshots, token metrics, context metadata, and output of a Task execution attempt.
    """
    __tablename__ = "runs"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=RunStatus.QUEUED.value,
        index=True,
    )
    model_provider: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    input_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    input_snapshot: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    output_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Step 6: Context Engine Execution Metadata
    context_item_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    estimated_context_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    context_truncated: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=False)
    context_sources: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    # Step 7: Hybrid RAG & Retrieval Telemetry Metadata
    retrieval_enabled: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=False)
    retrieved_chunk_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    retrieval_latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    retrieval_sources: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)

    # Step 8: Intelligent Retrieval Router Telemetry Metadata
    retrieval_mode: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    retrieval_required: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    retrieval_strategy: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    retrieval_scope: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    retrieval_top_k: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    retrieval_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retrieval_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Step 9: Tool System & Web Search Execution Metadata
    tools_used: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    tool_call_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    tool_latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    tool_errors: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    tool_executions: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)

    # Step 10: Orchestration Engine Execution Metadata
    execution_plan: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    execution_steps: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    orchestration_duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    retrieval_strategies: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    final_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    step_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    failed_step: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Step 11: LLM-Assisted Planning & Agentic Loop Metadata
    planner_mode: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    planner_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    repair_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    iteration_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=1)
    completion_evaluation: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Step 12: Model Router & Intelligence Metadata
    estimated_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    model_selection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    model_routing_policy: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    fallback_attempts: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)


    created_at: Mapped[datetime] = mapped_column(

        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    task: Mapped["Task"] = relationship(
        "Task",
        back_populates="runs",
    )

    def __repr__(self) -> str:
        return f"<Run(id={self.id}, task_id={self.task_id}, status='{self.status}', model='{self.model_name}')>"
