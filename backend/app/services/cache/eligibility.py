"""
Cache Eligibility Engine for Step 31: Semantic Cache and Intelligent Reuse Layer.
Determines whether an AI task or workflow step is safe for caching and reuse.
Strictly forbids caching operations with side-effects, external mutations, or HITL approvals.
"""
from typing import Any, Dict, List, Optional, Tuple

from backend.app.db.models.task import Task
from backend.app.services.cache.constants import (
    CacheMode,
    WorkflowCachePolicy,
)
from backend.app.services.task_intelligence.schemas import (
    TaskAnalysis,
    TaskRequirements,
    TaskType,
)
from backend.app.services.workflows.schemas import StepType


class CacheEligibilityService:
    """
    Evaluates whether tasks, steps, and outputs are eligible for cache lookup and admission.
    Prevents caching side-effects, destructive operations, and time-sensitive queries.
    """

    ELIGIBLE_TASK_TYPES = {
        TaskType.SUMMARIZATION.value,
        TaskType.DOCUMENT_ANALYSIS.value,
        TaskType.DATA_ANALYSIS.value,
        TaskType.EXTRACTION.value,
        TaskType.TRANSFORMATION.value,
        TaskType.QUESTION_ANSWERING.value,
        TaskType.RESEARCH.value,
        TaskType.CONTENT_GENERATION.value,
    }

    INELIGIBLE_TOOL_KEYWORDS = {
        "write",
        "delete",
        "create",
        "mutate",
        "update",
        "deploy",
        "send",
        "post",
        "trigger",
        "commit",
        "push",
        "drop",
        "execute_code",
    }

    @classmethod
    def is_cacheable(
        cls,
        task_type: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        has_side_effects: bool = False,
        requires_hitl: bool = False,
        cache_mode: Optional[Any] = None,
    ) -> Tuple[bool, str]:
        """
        Generic eligibility check evaluating task type, parameters, side-effects, and cache_mode.
        """
        mode_val = getattr(cache_mode, "value", str(cache_mode or "")).lower()
        if mode_val in ("disabled", "refresh"):
            return False, "Cache bypassed or disabled by request mode."

        if has_side_effects:
            return False, "Operation involves external side effects or write mutations."

        if requires_hitl:
            return False, "Operation involves human authorization/approval."

        params = parameters or {}
        prompt_text = str(params.get("prompt", "")).lower()
        if "no-cache" in prompt_text or "no_cache" in prompt_text or "do not cache" in prompt_text:
            return False, "Request explicitly specified no-cache."

        if any(term in prompt_text for term in ("live price", "breaking news", "current weather", "real-time stock")):
            return False, "Request requires live, time-sensitive external state."

        return True, "Operation is eligible for cache lookup and reuse."

    @classmethod
    def is_task_eligible(
        cls,
        task: Task,
        requirements: Optional[TaskRequirements] = None,
        cache_mode: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Determines whether a Task execution is eligible for cache lookup and reuse.
        Returns (is_eligible, reason).
        """
        mode = (cache_mode or getattr(task, "cache_mode", None) or CacheMode.AUTO.value).lower()
        if mode == CacheMode.DISABLED.value:
            return False, "Cache explicitly disabled for this task."

        # Check explicit no-cache instructions
        instructions = (task.instructions or "").lower()
        if "no-cache" in instructions or "no_cache" in instructions or "do not cache" in instructions:
            return False, "Task instructions explicitly request no caching."

        if requirements:
            # 1. External write or destructive action required
            if requirements.human_approval_required and requirements.human_approval_required.value:
                return False, "Task involves external actions requiring human approval (HITL)."

            # 2. Check for connector mutation
            if requirements.connector_required and requirements.connector_required.value:
                conn_name = (instructions or "").lower()
                if any(w in conn_name for w in cls.INELIGIBLE_TOOL_KEYWORDS):
                    return False, "Task includes external connector mutations."

            # 3. Check for mutating tools
            if requirements.tools_required and requirements.tools_required.value:
                if any(w in instructions for w in cls.INELIGIBLE_TOOL_KEYWORDS):
                    return False, "Task plans destructive or side-effecting tool calls."

            # 4. Check time-sensitive directives (live data)
            if any(term in instructions for term in ("latest", "breaking news", "live price", "current weather", "real-time", "now")):
                return False, "Task requires live or time-sensitive data."

        return True, "Task is eligible for caching."

    @classmethod
    def is_step_eligible(
        cls,
        step_type: str,
        step_config: Optional[Dict[str, Any]] = None,
        workflow_policy: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Determines whether a Workflow step is eligible for cache reuse.
        """
        w_policy = (workflow_policy or WorkflowCachePolicy.SAFE.value).lower()
        if w_policy == WorkflowCachePolicy.DISABLED.value:
            return False, "Caching is disabled for this workflow."

        config = step_config or {}
        if config.get("cache_mode") == CacheMode.DISABLED.value:
            return False, "Cache explicitly disabled for this step."

        s_type = str(step_type).lower()

        # Ineligible step types by design
        if s_type in (
            StepType.TOOL.value,
            StepType.CONNECTOR.value,
            "external_action",
            "approval",
            "webhook",
            "condition",
        ):
            return False, f"Step type '{s_type}' is side-effecting or dynamic and ineligible for caching."

        # Eligible step types
        if s_type in (
            StepType.GENERATE.value,
            StepType.TRANSFORM.value,
            StepType.EVALUATE.value,
            StepType.CONTEXT.value,
            "artifact_analyze",
        ):
            return True, f"Step type '{s_type}' is read-only and eligible for caching."

        return False, f"Step type '{s_type}' is not recognized as cache-eligible."
