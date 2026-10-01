import logging
import time
from typing import Any, Dict, Optional
from uuid import UUID

from backend.app.services.observability.events import TraceEventStatus, TraceEventType
from backend.app.services.task_intelligence.hybrid import HybridTaskAnalyzer
from backend.app.services.task_intelligence.policies import ExecutionRequirementsValidator
from backend.app.services.task_intelligence.requirements import TaskRequirementResolver
from backend.app.services.task_intelligence.rules import RuleBasedTaskAnalyzer
from backend.app.services.task_intelligence.schemas import (
    ExecutionPreviewResponse,
    ExecutionRequirements,
    TaskAnalysis,
    TaskAnalysisResponse,
    TaskRequirements,
)

logger = logging.getLogger("task_intelligence.service")


class TaskIntelligenceService:
    """
    Production-grade AI Task Intelligence layer facade.
    Analyzes incoming tasks, determines factual execution requirements,
    and produces a bounded execution configuration for the Orchestrator.

    INVARIANTS:
    - Task Intelligence recommends execution requirements; existing execution services remain authoritative.
    - Proposes execution requirements only; does not directly execute tools, connectors, or actions.
    - Does not expose chain-of-thought or internal prompts.
    - Does not create subjective "task quality" scores.
    - All requirements are validated and bounded by server-side policies.
    """

    def __init__(
        self,
        hybrid_analyzer: Optional[HybridTaskAnalyzer] = None,
    ) -> None:
        self.hybrid_analyzer = hybrid_analyzer or HybridTaskAnalyzer()

    async def analyze(
        self,
        task_text: str,
        context_text: Optional[str] = None,
        mode: Optional[str] = "auto",
        user_overrides: Optional[Dict[str, Any]] = None,
        workspace_policy: Optional[Dict[str, Any]] = None,
        workspace_id: Optional[str] = None,
        tracer: Optional[Any] = None,
    ) -> TaskAnalysisResponse:
        """
        Analyzes a task without executing it. Returns TaskAnalysisResponse.
        """
        start_time = time.perf_counter()

        if tracer:
            tracer.record_event(
                TraceEventType.TASK_ANALYSIS_STARTED,
                status=TraceEventStatus.STARTED,
                metadata={"mode": mode, "has_context": bool(context_text)},
            )

        analysis, reqs, fallback = await self.hybrid_analyzer.analyze(
            task_text=task_text,
            context_text=context_text,
            mode=mode,
            user_overrides=user_overrides,
            workspace_policy=workspace_policy,
            workspace_id=workspace_id,
        )

        resolved = TaskRequirementResolver.resolve_execution_requirements(
            analysis=analysis,
            requirements=reqs,
            user_overrides=user_overrides,
            workspace_policy=workspace_policy,
        )

        # Validate resolved requirements against policy
        try:
            ExecutionRequirementsValidator.validate(resolved, workspace_policy=workspace_policy)
        except Exception as val_err:
            if tracer:
                tracer.record_event(
                    TraceEventType.TASK_REQUIREMENT_VALIDATION_FAILED,
                    status=TraceEventStatus.FAILED,
                    metadata={"error": str(val_err)},
                )
            raise val_err

        duration_ms = int((time.perf_counter() - start_time) * 1000)

        if tracer:
            tracer.record_event(
                TraceEventType.TASK_ANALYSIS_COMPLETED,
                status=TraceEventStatus.COMPLETED,
                duration_ms=duration_ms,
                metadata={
                    "task_type": analysis.task_type.value,
                    "execution_mode": resolved.execution_mode,
                    "complexity": resolved.complexity,
                    "fallback_occurred": fallback,
                },
            )

        return TaskAnalysisResponse(
            analysis=analysis,
            requirements=reqs,
            execution_mode=resolved.execution_mode,
            complexity=resolved.complexity,
        )

    async def preview_execution(
        self,
        task_text: str,
        context_text: Optional[str] = None,
        mode: Optional[str] = "auto",
        user_overrides: Optional[Dict[str, Any]] = None,
        workspace_policy: Optional[Dict[str, Any]] = None,
        workspace_id: Optional[str] = None,
    ) -> ExecutionPreviewResponse:
        """
        Provides a safe, user-friendly execution preview without executing any steps.
        """
        analysis_resp = await self.analyze(
            task_text=task_text,
            context_text=context_text,
            mode=mode,
            user_overrides=user_overrides,
            workspace_policy=workspace_policy,
            workspace_id=workspace_id,
        )

        resolved = TaskRequirementResolver.resolve_execution_requirements(
            analysis=analysis_resp.analysis,
            requirements=analysis_resp.requirements,
            user_overrides=user_overrides,
            workspace_policy=workspace_policy,
        )

        return ExecutionPreviewResponse(
            task_type=resolved.task_type,
            execution_mode=resolved.execution_mode,
            complexity=resolved.complexity,
            retrieval=resolved.retrieval,
            tools=resolved.tools,
            connectors=resolved.connectors,
            memory=resolved.memory,
            model_requirements=resolved.model_requirements,
            evaluation=resolved.evaluation,
            human_approval=resolved.human_approval,
            workflow=resolved.workflow,
            limits=resolved.limits,
            explanation=analysis_resp.analysis.explanation,
        )

    async def resolve_execution_requirements(
        self,
        task_text: str,
        context_text: Optional[str] = None,
        mode: Optional[str] = "auto",
        user_overrides: Optional[Dict[str, Any]] = None,
        workspace_policy: Optional[Dict[str, Any]] = None,
        workspace_id: Optional[str] = None,
        tracer: Optional[Any] = None,
    ) -> ExecutionRequirements:
        """
        Resolves, merges, and validates authoritative ExecutionRequirements for task execution.
        """
        analysis_resp = await self.analyze(
            task_text=task_text,
            context_text=context_text,
            mode=mode,
            user_overrides=user_overrides,
            workspace_policy=workspace_policy,
            workspace_id=workspace_id,
            tracer=tracer,
        )

        resolved = TaskRequirementResolver.resolve_execution_requirements(
            analysis=analysis_resp.analysis,
            requirements=analysis_resp.requirements,
            user_overrides=user_overrides,
            workspace_policy=workspace_policy,
        )

        ExecutionRequirementsValidator.validate(resolved, workspace_policy=workspace_policy)
        return resolved


# Singleton instance
default_task_intelligence_service = TaskIntelligenceService()
