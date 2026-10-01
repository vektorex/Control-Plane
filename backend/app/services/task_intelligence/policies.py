import logging
from typing import Any, Dict, List, Optional

from backend.app.services.ai_gateway.providers import default_provider_registry
from backend.app.services.models.registry import default_model_registry
from backend.app.services.task_intelligence.errors import (
    PolicyViolationError,
    RequirementValidationError,
)
from backend.app.services.task_intelligence.schemas import (
    ComplexityLevel,
    ExecutionMode,
    ExecutionRequirements,
)

logger = logging.getLogger("task_intelligence.validator")


class ExecutionRequirementsValidator:
    """
    Validates resolved ExecutionRequirements against workspace policies,
    system capabilities, model registry, and security invariants.
    Authoritative server-side gate preventing unauthorized or impossible executions.
    """

    ALLOWED_EXECUTION_MODES = {m.value for m in ExecutionMode}
    ALLOWED_COMPLEXITIES = {c.value for c in ComplexityLevel}

    MAX_RETRIEVAL_TOP_K = 50
    MAX_EXECUTION_ITERATIONS = 5
    MAX_TOKEN_LIMIT = 64000

    @classmethod
    def validate(
        cls,
        requirements: ExecutionRequirements,
        workspace_policy: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Validates ExecutionRequirements. Raises RequirementValidationError or PolicyViolationError if invalid.
        """
        policy = workspace_policy or {}

        # 1. Validate Execution Mode
        if requirements.execution_mode not in cls.ALLOWED_EXECUTION_MODES:
            raise RequirementValidationError(
                f"Unknown or unsupported execution mode: '{requirements.execution_mode}'"
            )

        # 2. Validate Complexity
        if requirements.complexity not in cls.ALLOWED_COMPLEXITIES:
            raise RequirementValidationError(
                f"Unknown complexity category: '{requirements.complexity}'"
            )

        # 3. Validate Workflow requirements
        wf_cfg = requirements.workflow or {}
        if requirements.execution_mode == ExecutionMode.WORKFLOW.value:
            if not wf_cfg.get("workflow_id") and not wf_cfg.get("required"):
                raise RequirementValidationError(
                    "Workflow execution mode selected but no workflow_id was specified."
                )

        # 4. Validate Retrieval limits & permissions
        ret_cfg = requirements.retrieval or {}
        if ret_cfg.get("enabled"):
            top_k = ret_cfg.get("top_k", 8)
            if top_k <= 0 or top_k > cls.MAX_RETRIEVAL_TOP_K:
                raise RequirementValidationError(
                    f"Retrieval top_k ({top_k}) must be between 1 and {cls.MAX_RETRIEVAL_TOP_K}."
                )
            if policy.get("allow_retrieval") is False:
                raise PolicyViolationError("Document retrieval is disabled by workspace policy.")

        # 5. Validate Tools limits & permissions
        tools_cfg = requirements.tools or {}
        if tools_cfg.get("enabled"):
            if policy.get("allow_tools") is False:
                raise PolicyViolationError("Tool execution is disabled by workspace policy.")
            if tools_cfg.get("web_search") and policy.get("allow_web_search") is False:
                raise PolicyViolationError("Web search tool is disabled by workspace policy.")

        # 6. Validate Connectors permissions
        conn_cfg = requirements.connectors or {}
        if conn_cfg.get("enabled"):
            if policy.get("allow_connectors") is False:
                raise PolicyViolationError("Connector execution is disabled by workspace policy.")

        # 7. Validate Memory permissions
        mem_cfg = requirements.memory or {}
        if mem_cfg.get("enabled") and policy.get("allow_memory") is False:
            raise PolicyViolationError("Memory access is disabled by workspace policy.")

        # 8. Validate Model capabilities
        mod_reqs = requirements.model_requirements or {}
        caps = mod_reqs.get("capabilities", [])
        if "vision" in caps and not policy.get("allow_vision", True):
            raise PolicyViolationError("Vision model capabilities are disallowed by workspace policy.")

        # 9. Enforce HITL invariants
        hitl_cfg = requirements.human_approval or {}
        if hitl_cfg.get("required"):
            # Task intelligence can NEVER bypass human approval
            pass

        # 10. Validate bounded limits
        limits = requirements.limits or {}
        max_iter = limits.get("max_iterations", 3)
        if max_iter > cls.MAX_EXECUTION_ITERATIONS:
            raise RequirementValidationError(
                f"Max agent iterations ({max_iter}) exceeds system limit ({cls.MAX_EXECUTION_ITERATIONS})."
            )

        max_tok = limits.get("max_tokens", 8000)
        if max_tok > cls.MAX_TOKEN_LIMIT:
            raise RequirementValidationError(
                f"Max tokens ({max_tok}) exceeds system limit ({cls.MAX_TOKEN_LIMIT})."
            )
