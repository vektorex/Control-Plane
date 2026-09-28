from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.config import settings
from backend.app.db.models.user import User
from backend.app.schemas.task import TaskRunRequest
from backend.app.services.llm.factory import LLMProviderFactory, get_llm_factory
from backend.app.services.orchestration.errors import ExecutionLimitExceededError, PlanValidationError
from backend.app.services.orchestration.plan import ExecutionPlan, StepType
from backend.app.services.tools.registry import ToolRegistry, get_tool_registry


class ValidationResult(BaseModel):
    """
    Structured outcome of a multi-layer plan validation check.
    """
    is_valid: bool = Field(default=True)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class PlanValidator:
    """
    Validates ExecutionPlans prior to execution across 6 architectural layers:
    1. Schema validation (valid types, unique IDs, final generate termination)
    2. Capability validation (registered tools in ToolRegistry, allowed retrieval strategies)
    3. Permission validation (tool execution permission for authenticated user)
    4. Security policy validation (rejects unauthorized tools, arbitrary shell/code execution)
    5. Execution limits (MAX_PLAN_STEPS, MAX_TOOL_CALLS_PER_PLAN, MAX_RETRIEVAL_CALLS_PER_PLAN)
    6. Task configuration validation (enforces task retrieval and tool disablement constraints)
    """

    ALLOWED_RETRIEVAL_STRATEGIES = {"hybrid", "vector", "keyword", "multi_query", "none"}
    ALLOWED_RETRIEVAL_SCOPES = {"project", "workspace"}

    def __init__(
        self,
        tool_registry: Optional[ToolRegistry] = None,
        llm_factory: Optional[LLMProviderFactory] = None,
    ) -> None:
        self.tool_registry = tool_registry or get_tool_registry()
        self.llm_factory = llm_factory or get_llm_factory()

    def validate_detailed(
        self,
        plan: ExecutionPlan,
        user: Optional[User] = None,
        request: Optional[TaskRunRequest] = None,
    ) -> ValidationResult:
        """
        Runs full 6-layer validation and collects all violations without immediately raising.
        Used for controlled LLM plan repair requests.
        """
        errors: List[str] = []
        warnings: List[str] = []

        if not plan or not plan.steps:
            return ValidationResult(is_valid=False, errors=["Execution plan must contain at least one step."])

        # Layer 5: Enforce Step Count Limit
        max_steps = settings.MAX_PLAN_STEPS
        if len(plan.steps) > max_steps:
            errors.append(f"Execution plan contains {len(plan.steps)} steps, exceeding max limit of {max_steps}.")

        # Check unique step IDs & count step types
        step_ids = set()
        tool_call_count = 0
        retrieval_call_count = 0

        for idx, step in enumerate(plan.steps):
            if not step.id:
                errors.append(f"Step at index {idx} has no step ID.")
            elif step.id in step_ids:
                errors.append(f"Duplicate step ID '{step.id}' detected in execution plan.")
            else:
                step_ids.add(step.id)

            # Layer 1: Validate step type
            try:
                step_type_str = str(step.type.value if hasattr(step.type, "value") else step.type)
                step_type = StepType(step_type_str)
            except ValueError:
                errors.append(f"Unsupported step type '{step.type}' in step '{step.id}'.")
                continue

            # Layer 2 & 6: Validate Retrieval Steps
            if step_type == StepType.RETRIEVE:
                retrieval_call_count += 1
                if retrieval_call_count > settings.MAX_RETRIEVAL_CALLS_PER_PLAN:
                    errors.append(
                        f"Execution plan exceeds max retrieval operations limit of {settings.MAX_RETRIEVAL_CALLS_PER_PLAN}."
                    )
                
                strategy = (step.strategy or "hybrid").lower()
                if strategy not in self.ALLOWED_RETRIEVAL_STRATEGIES:
                    errors.append(
                        f"Invalid retrieval strategy '{strategy}' in step '{step.id}'. Allowed: {sorted(list(self.ALLOWED_RETRIEVAL_STRATEGIES))}."
                    )

                scope = (step.scope or "project").lower()
                if scope not in self.ALLOWED_RETRIEVAL_SCOPES:
                    errors.append(
                        f"Invalid retrieval scope '{scope}' in step '{step.id}'. Allowed: {sorted(list(self.ALLOWED_RETRIEVAL_SCOPES))}."
                    )

                if step.top_k is not None and (step.top_k < 1 or step.top_k > 50):
                    errors.append(
                        f"Invalid retrieval top_k '{step.top_k}' in step '{step.id}'. Must be between 1 and 50."
                    )

                if request and request.retrieval_mode == "never":
                    errors.append(f"Retrieval step '{step.id}' is forbidden because retrieval is disabled (retrieval_mode='never').")

            # Layer 2, 3 & 4: Validate Tool Steps
            elif step_type == StepType.TOOL:
                tool_call_count += 1
                if tool_call_count > settings.MAX_TOOL_CALLS_PER_PLAN:
                    errors.append(
                        f"Execution plan exceeds max tool calls limit of {settings.MAX_TOOL_CALLS_PER_PLAN}."
                    )
                if not step.tool:
                    errors.append(f"Tool step '{step.id}' does not specify a tool name.")
                elif not self.tool_registry.has_tool(step.tool):
                    errors.append(f"Tool '{step.tool}' in step '{step.id}' is not registered in ToolRegistry.")
                else:
                    tool_instance = self.tool_registry.get(step.tool)
                    if step.tool_input is not None:
                        try:
                            tool_instance.validate_input(step.tool_input)
                        except Exception as tool_val_err:
                            errors.append(f"Invalid input arguments for tool '{step.tool}' in step '{step.id}': {tool_val_err}")

                    if user is not None and tool_instance.requires_auth:
                        raw_input = step.tool_input or {}
                        if not tool_instance.check_permission(raw_input, user):
                            errors.append(f"User lacks required permissions to execute tool '{step.tool}' in step '{step.id}'.")

                if request:
                    tools_disabled = request.tool_mode == "disabled" and not request.enable_web_search and not request.tools_enabled
                    if tools_disabled:
                        errors.append(f"Tool step '{step.id}' is forbidden because tools are disabled (tool_mode='disabled').")

            # Layer 1 & 6: Validate Generation Steps
            elif step_type == StepType.GENERATE:
                if step.temperature is not None and (step.temperature < 0.0 or step.temperature > 2.0):
                    errors.append(f"Invalid temperature '{step.temperature}' in step '{step.id}'. Must be between 0.0 and 2.0.")

                target_model = step.model or settings.OPENAI_DEFAULT_MODEL
                if self.llm_factory and not self.llm_factory.has_provider_for_model(target_model):
                    warnings.append(f"Model '{target_model}' in step '{step.id}' will use default provider fallback.")

        # Layer 1: Final step must be a generation step
        final_step = plan.steps[-1]
        final_step_type_str = str(final_step.type.value if hasattr(final_step.type, "value") else final_step.type)
        if final_step_type_str != StepType.GENERATE.value:
            errors.append(
                f"Execution plan must terminate with a '{StepType.GENERATE.value}' step, got '{final_step_type_str}'."
            )

        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)

    def validate(
        self,
        plan: ExecutionPlan,
        user: Optional[User] = None,
        request: Optional[TaskRunRequest] = None,
    ) -> bool:
        """
        Validates the ExecutionPlan. Raises PlanValidationError or ExecutionLimitExceededError on failure.
        """
        res = self.validate_detailed(plan, user=user, request=request)
        if not res.is_valid:
            error_msg = "; ".join(res.errors)
            if "exceeding max limit" in error_msg or "exceeds max" in error_msg:
                raise ExecutionLimitExceededError(error_msg)
            raise PlanValidationError(error_msg)

        return True
