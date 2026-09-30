"""
WorkflowValidator for structural, semantic, and resource limit validation.
"""
from typing import Any, Dict, List, Set
from backend.app.config import settings
from backend.app.services.workflows.schemas import (
    StepType,
    WorkflowDefinition,
    WorkflowStepDefinition,
    WorkflowValidationIssue,
    WorkflowValidationResponse,
)


class WorkflowValidator:
    """
    Validates workflow definitions against structural rules, schema constraints, and resource limits.
    """

    @classmethod
    def validate_workflow_definition(cls, definition: WorkflowDefinition) -> WorkflowValidationResponse:
        issues: List[WorkflowValidationIssue] = []
        steps = definition.steps or []

        max_steps = getattr(settings, "MAX_WORKFLOW_STEPS", 20)
        max_tool_calls = getattr(settings, "MAX_WORKFLOW_TOOL_CALLS", 10)
        max_retrieval_calls = getattr(settings, "MAX_WORKFLOW_RETRIEVAL_CALLS", 10)
        max_depth = getattr(settings, "MAX_WORKFLOW_DEPTH", 5)

        # 1. Step Count Validation
        if not steps:
            issues.append(WorkflowValidationIssue(
                level="error",
                message="Workflow must contain at least one step."
            ))
            return WorkflowValidationResponse(valid=False, issues=issues, step_count=0)

        if len(steps) > max_steps:
            issues.append(WorkflowValidationIssue(
                level="error",
                message=f"Workflow exceeds maximum allowed steps limit ({len(steps)} > {max_steps})."
            ))

        # 2. Step ID uniqueness and identification
        step_ids: Set[str] = set()
        step_id_list: List[str] = []
        tool_count = 0
        retrieval_count = 0

        for idx, step in enumerate(steps):
            s_id = (step.id or "").strip()
            if not s_id:
                issues.append(WorkflowValidationIssue(
                    level="error",
                    step_id=f"step_{idx}",
                    field="id",
                    message=f"Step at index {idx} must have a non-empty string ID."
                ))
                continue

            if s_id in step_ids:
                issues.append(WorkflowValidationIssue(
                    level="error",
                    step_id=s_id,
                    field="id",
                    message=f"Duplicate step ID '{s_id}'. Step IDs must be unique across the workflow."
                ))
            else:
                step_ids.add(s_id)
                step_id_list.append(s_id)

            # Count resource-intensive steps
            if step.type == StepType.TOOL:
                tool_count += 1
            elif step.type == StepType.RETRIEVE:
                retrieval_count += 1

            # Validate individual step configuration
            cls._validate_step_config(step, issues)

        # 3. Resource Call Limits
        if tool_count > max_tool_calls:
            issues.append(WorkflowValidationIssue(
                level="error",
                message=f"Workflow exceeds maximum tool call limit ({tool_count} > {max_tool_calls})."
            ))

        if retrieval_count > max_retrieval_calls:
            issues.append(WorkflowValidationIssue(
                level="error",
                message=f"Workflow exceeds maximum retrieval call limit ({retrieval_count} > {max_retrieval_calls})."
            ))

        # 4. Validate Branch References & Targets
        cls._validate_branch_references(steps, step_ids, max_depth, issues)

        # 5. Validate Input Schema Contract
        if definition.input_schema:
            cls._validate_input_schema(definition.input_schema, issues)

        has_errors = any(iss.level == "error" for iss in issues)
        return WorkflowValidationResponse(
            valid=not has_errors,
            issues=issues,
            step_count=len(steps),
            tool_call_count=tool_count,
            retrieval_call_count=retrieval_count,
        )

    @classmethod
    def _validate_step_config(cls, step: WorkflowStepDefinition, issues: List[WorkflowValidationIssue]) -> None:
        cfg = step.config or {}
        stype = step.type

        if stype == StepType.RETRIEVE:
            top_k = cfg.get("top_k")
            if top_k is not None and (not isinstance(top_k, int) or top_k < 1 or top_k > 50):
                issues.append(WorkflowValidationIssue(
                    level="error",
                    step_id=step.id,
                    field="config.top_k",
                    message="Retrieve step 'top_k' must be an integer between 1 and 50."
                ))

        elif stype == StepType.TOOL:
            tool_name = cfg.get("tool_name") or cfg.get("tool")
            if not tool_name or not isinstance(tool_name, str):
                issues.append(WorkflowValidationIssue(
                    level="error",
                    step_id=step.id,
                    field="config.tool_name",
                    message="Tool step requires a valid 'tool_name' string in config."
                ))

        elif stype == StepType.CONNECTOR:
            connector_name = cfg.get("connector") or cfg.get("connector_name")
            operation = cfg.get("operation")
            if not connector_name or not isinstance(connector_name, str):
                issues.append(WorkflowValidationIssue(
                    level="error",
                    step_id=step.id,
                    field="config.connector",
                    message="Connector step requires a valid 'connector' string in config (e.g. 'github')."
                ))
            if not operation or not isinstance(operation, str):
                issues.append(WorkflowValidationIssue(
                    level="error",
                    step_id=step.id,
                    field="config.operation",
                    message="Connector step requires a valid 'operation' string in config (e.g. 'search_issues')."
                ))

        elif stype == StepType.MEMORY:
            op = cfg.get("operation")
            allowed_ops = ["retrieve", "save_candidate", "create_explicit"]
            if not op or op not in allowed_ops:
                issues.append(WorkflowValidationIssue(
                    level="error",
                    step_id=step.id,
                    field="config.operation",
                    message=f"Memory step 'operation' must be one of {allowed_ops}."
                ))
            top_k = cfg.get("top_k")
            if top_k is not None and (not isinstance(top_k, int) or top_k < 1 or top_k > 50):
                issues.append(WorkflowValidationIssue(
                    level="error",
                    step_id=step.id,
                    field="config.top_k",
                    message="Memory step 'top_k' must be an integer between 1 and 50."
                ))

        elif stype == StepType.GENERATE:
            temp = cfg.get("temperature")
            if temp is not None and (not isinstance(temp, (int, float)) or temp < 0.0 or temp > 2.0):
                issues.append(WorkflowValidationIssue(
                    level="error",
                    step_id=step.id,
                    field="config.temperature",
                    message="Generate step 'temperature' must be a float between 0.0 and 2.0."
                ))

        elif stype == StepType.EVALUATE:
            mode = cfg.get("mode") or cfg.get("evaluation_mode")
            if mode is not None and mode not in ["off", "basic", "standard", "strict"]:
                issues.append(WorkflowValidationIssue(
                    level="error",
                    step_id=step.id,
                    field="config.mode",
                    message="Evaluate step 'mode' must be one of ['off', 'basic', 'standard', 'strict']."
                ))

        elif stype == StepType.TRANSFORM:
            op = cfg.get("operation")
            allowed_ops = ["select", "rename", "map", "filter", "join", "truncate"]
            if not op or op not in allowed_ops:
                issues.append(WorkflowValidationIssue(
                    level="error",
                    step_id=step.id,
                    field="config.operation",
                    message=f"Transform step operation must be one of {allowed_ops}."
                ))

        elif stype == StepType.CONDITION:
            op = cfg.get("operator")
            allowed_operators = ["==", "!=", ">", ">=", "<", "<=", "exists"]
            if not op or op not in allowed_operators:
                issues.append(WorkflowValidationIssue(
                    level="error",
                    step_id=step.id,
                    field="config.operator",
                    message=f"Condition step operator must be one of {allowed_operators}."
                ))
            if "left" not in cfg:
                issues.append(WorkflowValidationIssue(
                    level="error",
                    step_id=step.id,
                    field="config.left",
                    message="Condition step requires 'left' operand reference."
                ))

    @classmethod
    def _validate_branch_references(
        cls,
        steps: List[WorkflowStepDefinition],
        step_ids: Set[str],
        max_depth: int,
        issues: List[WorkflowValidationIssue]
    ) -> None:
        valid_control_keywords = {"stop", "continue", "next", "end"}
        condition_count = 0

        for step in steps:
            if step.type == StepType.CONDITION:
                condition_count += 1
                cfg = step.config or {}
                if_true = cfg.get("if_true")
                if_false = cfg.get("if_false")

                if if_true and if_true not in valid_control_keywords and if_true not in step_ids:
                    issues.append(WorkflowValidationIssue(
                        level="error",
                        step_id=step.id,
                        field="config.if_true",
                        message=f"Condition branch target 'if_true: {if_true}' does not match any valid step ID."
                    ))

                if if_false and if_false not in valid_control_keywords and if_false not in step_ids:
                    issues.append(WorkflowValidationIssue(
                        level="error",
                        step_id=step.id,
                        field="config.if_false",
                        message=f"Condition branch target 'if_false: {if_false}' does not match any valid step ID."
                    ))

        if condition_count > max_depth:
            issues.append(WorkflowValidationIssue(
                level="error",
                message=f"Workflow exceeds maximum conditional branching depth limit ({condition_count} > {max_depth})."
            ))

    @classmethod
    def _validate_input_schema(cls, input_schema: Dict[str, Any], issues: List[WorkflowValidationIssue]) -> None:
        allowed_types = {"string", "number", "boolean", "object", "array"}
        for field_name, spec in input_schema.items():
            if not isinstance(spec, dict):
                issues.append(WorkflowValidationIssue(
                    level="error",
                    field=f"input_schema.{field_name}",
                    message=f"Input schema for field '{field_name}' must be an object definition."
                ))
                continue
            ftype = spec.get("type", "string")
            if ftype not in allowed_types:
                issues.append(WorkflowValidationIssue(
                    level="error",
                    field=f"input_schema.{field_name}.type",
                    message=f"Invalid field type '{ftype}'. Allowed types: {sorted(list(allowed_types))}."
                ))

    @classmethod
    def validate_runtime_input(cls, input_schema: Dict[str, Any], runtime_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates runtime input dictionary against the workflow's input_schema contract.
        Returns a sanitized dictionary with defaults applied.
        """
        from backend.app.services.workflows.errors import WorkflowInputValidationError

        validated: Dict[str, Any] = {}
        schema = input_schema or {}

        # Check required fields and apply defaults
        for field_name, spec in schema.items():
            is_req = spec.get("required", False) if isinstance(spec, dict) else False
            ftype = spec.get("type", "string") if isinstance(spec, dict) else "string"
            default_val = spec.get("default") if isinstance(spec, dict) else None

            if field_name not in runtime_input or runtime_input[field_name] is None:
                if is_req and default_val is None:
                    raise WorkflowInputValidationError(
                        f"Missing required workflow input parameter: '{field_name}'"
                    )
                validated[field_name] = default_val
            else:
                val = runtime_input[field_name]
                cls._validate_type_compatibility(field_name, val, ftype)
                validated[field_name] = val

        # Include additional non-schema fields safely
        for k, v in runtime_input.items():
            if k not in validated:
                validated[k] = v

        return validated

    @classmethod
    def _validate_type_compatibility(cls, field_name: str, val: Any, expected_type: str) -> None:
        from backend.app.services.workflows.errors import WorkflowInputValidationError

        if expected_type == "string" and not isinstance(val, str):
            raise WorkflowInputValidationError(f"Input '{field_name}' expected string, got {type(val).__name__}.")
        elif expected_type == "number" and not isinstance(val, (int, float)) and not (isinstance(val, str) and val.replace(".", "", 1).isdigit()):
            raise WorkflowInputValidationError(f"Input '{field_name}' expected number, got {type(val).__name__}.")
        elif expected_type == "boolean" and not isinstance(val, bool):
            raise WorkflowInputValidationError(f"Input '{field_name}' expected boolean, got {type(val).__name__}.")
        elif expected_type == "object" and not isinstance(val, dict):
            raise WorkflowInputValidationError(f"Input '{field_name}' expected object, got {type(val).__name__}.")
        elif expected_type == "array" and not isinstance(val, list):
            raise WorkflowInputValidationError(f"Input '{field_name}' expected array/list, got {type(val).__name__}.")
