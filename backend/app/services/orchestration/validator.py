from typing import Any, Dict, List, Optional
from backend.app.config import settings
from backend.app.db.models.user import User
from backend.app.services.llm.factory import LLMProviderFactory, get_llm_factory
from backend.app.services.orchestration.errors import ExecutionLimitExceededError, PlanValidationError
from backend.app.services.orchestration.plan import ExecutionPlan, StepType
from backend.app.services.tools.registry import ToolRegistry, get_tool_registry


class PlanValidator:
    """
    Validates ExecutionPlans prior to execution to enforce security, safety boundaries,
    server-side limits, tool availability, and schema integrity.
    """

    ALLOWED_RETRIEVAL_STRATEGIES = {"hybrid", "vector", "keyword", "multi_query", "none"}

    def __init__(
        self,
        tool_registry: Optional[ToolRegistry] = None,
        llm_factory: Optional[LLMProviderFactory] = None,
    ) -> None:
        self.tool_registry = tool_registry or get_tool_registry()
        self.llm_factory = llm_factory or get_llm_factory()

    def validate(
        self,
        plan: ExecutionPlan,
        user: Optional[User] = None,
    ) -> bool:
        """
        Validates the ExecutionPlan against all architectural and security constraints.
        Raises PlanValidationError or ExecutionLimitExceededError on violation.
        """
        if not plan or not plan.steps:
            raise PlanValidationError("Execution plan must contain at least one step.")

        # 1. Enforce Step Count Limit
        max_steps = settings.MAX_PLAN_STEPS
        if len(plan.steps) > max_steps:
            raise ExecutionLimitExceededError(
                f"Execution plan contains {len(plan.steps)} steps, exceeding max limit of {max_steps}."
            )

        # 2. Check for unique step IDs
        step_ids = set()
        tool_call_count = 0
        retrieval_call_count = 0

        for idx, step in enumerate(plan.steps):
            if not step.id:
                raise PlanValidationError(f"Step at index {idx} has no step ID.")
            if step.id in step_ids:
                raise PlanValidationError(f"Duplicate step ID '{step.id}' detected in execution plan.")
            step_ids.add(step.id)

            # 3. Validate step type
            try:
                step_type_str = str(step.type.value if hasattr(step.type, "value") else step.type)
                step_type = StepType(step_type_str)
            except ValueError:
                raise PlanValidationError(f"Unsupported step type '{step.type}' in step '{step.id}'.")

            # 4. Validate Retrieval Steps
            if step_type == StepType.RETRIEVE:
                retrieval_call_count += 1
                if retrieval_call_count > settings.MAX_RETRIEVAL_CALLS_PER_PLAN:
                    raise ExecutionLimitExceededError(
                        f"Execution plan exceeds max retrieval operations limit of {settings.MAX_RETRIEVAL_CALLS_PER_PLAN}."
                    )
                strategy = (step.strategy or "hybrid").lower()
                if strategy not in self.ALLOWED_RETRIEVAL_STRATEGIES:
                    raise PlanValidationError(
                        f"Invalid retrieval strategy '{strategy}' in step '{step.id}'. "
                        f"Allowed strategies: {sorted(list(self.ALLOWED_RETRIEVAL_STRATEGIES))}."
                    )

            # 5. Validate Tool Steps
            elif step_type == StepType.TOOL:
                tool_call_count += 1
                if tool_call_count > settings.MAX_TOOL_CALLS_PER_PLAN:
                    raise ExecutionLimitExceededError(
                        f"Execution plan exceeds max tool calls limit of {settings.MAX_TOOL_CALLS_PER_PLAN}."
                    )
                if not step.tool:
                    raise PlanValidationError(f"Tool step '{step.id}' does not specify a tool name.")
                
                # Check tool registration in ToolRegistry
                if not self.tool_registry.has_tool(step.tool):
                    raise PlanValidationError(
                        f"Tool '{step.tool}' specified in step '{step.id}' is not registered in ToolRegistry."
                    )

                # Check tool permissions
                tool_instance = self.tool_registry.get(step.tool)
                if user is not None and tool_instance.requires_auth:
                    raw_input = step.tool_input or {}
                    if not tool_instance.check_permission(raw_input, user):
                        raise PlanValidationError(
                            f"User lacks required permissions to execute tool '{step.tool}' in step '{step.id}'."
                        )

            # 6. Validate Generation Steps
            elif step_type == StepType.GENERATE:
                target_model = step.model or settings.OPENAI_DEFAULT_MODEL
                if self.llm_factory and not self.llm_factory.has_provider_for_model(target_model):
                    # Check if registered or fallback
                    pass

        # 7. Final step must be a generation step
        final_step = plan.steps[-1]
        final_step_type_str = str(final_step.type.value if hasattr(final_step.type, "value") else final_step.type)
        if final_step_type_str != StepType.GENERATE.value:
            raise PlanValidationError(
                f"Execution plan must terminate with a '{StepType.GENERATE.value}' step, got '{final_step_type_str}'."
            )

        return True
