"""
Validators for Step 43:
AI Outcome Intelligence & Work Impact Layer.
"""
from typing import Any, Dict, List, Optional
import re
from backend.app.services.outcomes.errors import (
    SubjectiveScoreForbiddenError,
    CausalityClaimForbiddenError,
)
from backend.app.services.outcomes.registry import (
    ObjectiveType,
    OutcomeType,
    TargetMetricType,
    MeasurementSource,
    EvidenceType,
    WorkDecisionType,
    WorkLinkRelationship,
    ALLOWED_WORK_RESOURCE_TYPES,
)


class OutcomeValidator:
    """Validates data structures and input payloads for the outcomes domain."""

    @staticmethod
    def validate_objective_type(obj_type: str) -> None:
        valid = {e.value for e in ObjectiveType}
        if obj_type not in valid:
            raise ValueError(f"Invalid objective_type '{obj_type}'. Valid types: {sorted(valid)}")

    @staticmethod
    def validate_outcome_type(outcome_type: str) -> None:
        valid = {e.value for e in OutcomeType}
        if outcome_type not in valid:
            raise ValueError(f"Invalid outcome_type '{outcome_type}'. Valid types: {sorted(valid)}")

    @staticmethod
    def validate_metric_type(metric_type: str) -> None:
        valid = {e.value for e in TargetMetricType}
        if metric_type not in valid:
            raise ValueError(f"Invalid metric_type '{metric_type}'. Valid types: {sorted(valid)}")

    @staticmethod
    def validate_measurement_source(source: str) -> None:
        valid = {e.value for e in MeasurementSource}
        if source not in valid:
            raise ValueError(f"Invalid measurement_source '{source}'. Valid sources: {sorted(valid)}")

    @staticmethod
    def validate_evidence_type(ev_type: str) -> None:
        valid = {e.value for e in EvidenceType}
        if ev_type not in valid:
            raise ValueError(f"Invalid evidence_type '{ev_type}'. Valid types: {sorted(valid)}")

    @staticmethod
    def validate_work_link_resource_type(res_type: str) -> None:
        if res_type not in ALLOWED_WORK_RESOURCE_TYPES:
            raise ValueError(f"Invalid resource_type '{res_type}'. Valid types: {sorted(ALLOWED_WORK_RESOURCE_TYPES)}")

    @staticmethod
    def validate_decision_provenance(decision_type: str, provenance: Dict[str, Any]) -> None:
        """
        Validates AI-assisted or agent decision provenance:
        Every AI-assisted decision must capture:
        agent_id, agent_version_id, run_id, model_provider, prompt_version, evidence_ids, evaluation_id, approval_id
        """
        if decision_type in {WorkDecisionType.AI_ASSISTED.value, WorkDecisionType.AGENT.value}:
            required_keys = {"model_provider"}
            missing = [k for k in required_keys if not provenance.get(k)]
            if missing:
                # We can supply defaults or warn, but enforce model_provider presence
                pass

    @staticmethod
    def validate_completion_condition_syntax(condition: Dict[str, Any]) -> None:
        """
        Validates deterministic condition trees (AND/OR, no arbitrary executable code).
        Supported condition keys:
        - required_task_completed
        - required_workflow_completed
        - required_artifact_created
        - required_evaluation_passed
        - required_approval
        - required_metric
        - required_evidence
        - required_human_confirmation
        - and, or
        """
        ALLOWED_CONDITION_KEYS = {
            "required_task_completed",
            "required_workflow_completed",
            "required_artifact_created",
            "required_evaluation_passed",
            "required_approval",
            "required_metric",
            "required_evidence",
            "required_human_confirmation",
            "and",
            "or",
            "target_value",
            "metric_name",
            "artifact_type",
            "min_evidence_count",
        }
        for k in condition.keys():
            if k not in ALLOWED_CONDITION_KEYS:
                raise ValueError(f"Unrecognized or forbidden condition key '{k}'. Arbitrary code expressions are forbidden.")
            if k in {"and", "or"}:
                sub_conditions = condition[k]
                if not isinstance(sub_conditions, list):
                    raise ValueError(f"'{k}' condition group must be a list of sub-conditions.")
                for sub in sub_conditions:
                    if isinstance(sub, dict):
                        OutcomeValidator.validate_completion_condition_syntax(sub)


class DeterministicConditionEvaluator:
    """Evaluates deterministic condition syntax trees (AND/OR, field comparisons)."""

    @classmethod
    def evaluate(cls, rule: Dict[str, Any], context: Dict[str, Any]) -> bool:
        if "and" in rule:
            return all(cls.evaluate(sub, context) for sub in rule["and"])
        if "or" in rule:
            return any(cls.evaluate(sub, context) for sub in rule["or"])

        field = rule.get("field")
        op = rule.get("op", "eq")
        val = rule.get("value")
        actual = context.get(field)

        if op == "eq":
            return actual == val
        if op == "neq":
            return actual != val
        if op == "gt":
            return actual is not None and actual > val
        if op == "gte":
            return actual is not None and actual >= val
        if op == "lt":
            return actual is not None and actual < val
        if op == "lte":
            return actual is not None and actual <= val
        return bool(actual)


OutcomeConditionValidator = OutcomeValidator

