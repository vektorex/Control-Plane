import logging
import time
from typing import Any, Dict, Optional, Tuple

from backend.app.config import settings
from backend.app.services.task_intelligence.confidence import ConfidenceCalculator
from backend.app.services.task_intelligence.errors import AnalyzerError, AnalyzerTimeoutError
from backend.app.services.task_intelligence.llm_analyzer import LLMTaskAnalyzer
from backend.app.services.task_intelligence.policies import ExecutionRequirementsValidator
from backend.app.services.task_intelligence.requirements import TaskRequirementResolver
from backend.app.services.task_intelligence.rules import RuleBasedTaskAnalyzer
from backend.app.services.task_intelligence.schemas import (
    ExecutionRequirements,
    TaskAnalysis,
    TaskRequirements,
    TaskType,
)

logger = logging.getLogger("task_intelligence.hybrid")


class HybridTaskAnalyzer:
    """
    Hybrid analyzer coordinating deterministic rule matching and LLM-powered analysis.
    Uses LLM only when deterministic rules cannot confidently resolve the task.
    Provides fail-safe fallback to deterministic analysis if the LLM encounters errors or timeouts.
    """

    def __init__(
        self,
        rule_analyzer: Optional[RuleBasedTaskAnalyzer] = None,
        llm_analyzer: Optional[LLMTaskAnalyzer] = None,
    ) -> None:
        self.rule_analyzer = rule_analyzer or RuleBasedTaskAnalyzer()
        self.llm_analyzer = llm_analyzer or LLMTaskAnalyzer()

    async def analyze(
        self,
        task_text: str,
        context_text: Optional[str] = None,
        mode: Optional[str] = None,
        user_overrides: Optional[Dict[str, Any]] = None,
        workspace_policy: Optional[Dict[str, Any]] = None,
        workspace_id: Optional[str] = None,
    ) -> Tuple[TaskAnalysis, TaskRequirements, bool]:
        """
        Executes hybrid task analysis.
        Returns: (TaskAnalysis, TaskRequirements, fallback_occurred: bool).
        """
        configured_mode = (mode or getattr(settings, "TASK_INTELLIGENCE_MODE", "hybrid")).lower()
        if configured_mode == "auto":
            configured_mode = "hybrid"

        fallback_occurred = False

        # 1. Deterministic Analysis always runs first (zero LLM token cost)
        det_analysis, det_reqs = self.rule_analyzer.analyze(
            task_text=task_text,
            context_text=context_text,
            user_overrides=user_overrides,
        )

        # If deterministic mode requested, return immediately
        if configured_mode == "deterministic":
            final_reqs = TaskRequirementResolver.merge_requirements(
                deterministic_reqs=det_reqs,
                llm_reqs=None,
                user_overrides=user_overrides,
                workspace_policy=workspace_policy,
            )
            return det_analysis, final_reqs, False

        # 2. Check if deterministic confidence is high enough to skip LLM call
        confidence_threshold = getattr(settings, "TASK_ANALYSIS_CONFIDENCE_THRESHOLD", 0.8)
        is_confident = (
            ConfidenceCalculator.is_confidence_sufficient(det_analysis.confidence, confidence_threshold)
            and det_analysis.task_type != TaskType.UNKNOWN
        )

        # In hybrid mode, if deterministic is already confident, save tokens & latency
        if configured_mode == "hybrid" and is_confident:
            logger.info(
                f"[HybridTaskAnalyzer] Deterministic analysis confident ({det_analysis.confidence:.2f}) "
                f"for type '{det_analysis.task_type.value}'. Skipping LLM analysis."
            )
            final_reqs = TaskRequirementResolver.merge_requirements(
                deterministic_reqs=det_reqs,
                llm_reqs=None,
                user_overrides=user_overrides,
                workspace_policy=workspace_policy,
            )
            return det_analysis, final_reqs, False

        # 3. Invoke LLM analysis
        llm_analysis: Optional[TaskAnalysis] = None
        llm_reqs: Optional[TaskRequirements] = None

        try:
            llm_analysis, llm_reqs = await self.llm_analyzer.analyze(
                task_text=task_text,
                context_text=context_text,
                workspace_id=workspace_id,
            )
        except (AnalyzerError, AnalyzerTimeoutError, Exception) as exc:
            logger.warning(
                f"[HybridTaskAnalyzer] LLM analysis failed or timed out: {exc}. "
                "Failing back safely to deterministic analysis."
            )
            fallback_occurred = True

        # 4. Merge results
        if llm_analysis and llm_reqs and not fallback_occurred:
            # Use LLM analysis as primary baseline, with deterministic signals backing it up
            final_analysis = llm_analysis
            final_reqs = TaskRequirementResolver.merge_requirements(
                deterministic_reqs=det_reqs,
                llm_reqs=llm_reqs,
                user_overrides=user_overrides,
                workspace_policy=workspace_policy,
            )
        else:
            final_analysis = det_analysis
            final_reqs = TaskRequirementResolver.merge_requirements(
                deterministic_reqs=det_reqs,
                llm_reqs=None,
                user_overrides=user_overrides,
                workspace_policy=workspace_policy,
            )

        return final_analysis, final_reqs, fallback_occurred
