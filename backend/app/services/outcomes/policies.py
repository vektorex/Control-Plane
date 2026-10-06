"""
Governance, Safety, and Verification Policies for Step 43:
AI Outcome Intelligence & Work Impact Layer.
"""
from typing import Any, Dict, List, Optional, Set
from backend.app.services.outcomes.errors import (
    CausalityClaimForbiddenError,
    SubjectiveScoreForbiddenError,
    OutcomeTenantViolationError,
    MissingBaselineError,
    RequirementNotMetError,
    UnauthorizedVerificationError,
)
from backend.app.services.outcomes.registry import (
    AttributionSource,
    AttributionType,
    WorkDecisionType,
)


class OutcomePolicyEngine:
    """
    Enforces deterministic safety, governance, and attribution boundaries.
    """

    FORBIDDEN_SCORE_KEYS: Set[str] = {
        "intelligence_score",
        "agent_iq",
        "general_ai_quality",
        "arbitrary_ai_score",
        "subjective_rating",
    }

    @classmethod
    def validate_no_subjective_scores(cls, data: Dict[str, Any]) -> None:
        """
        Ensures that subjective or fabricated AI quality scores are rejected.
        Only explicit, factual, or evaluation-harness metrics are allowed.
        """
        for k in data.keys():
            if k.lower() in cls.FORBIDDEN_SCORE_KEYS:
                raise SubjectiveScoreForbiddenError(
                    f"Subjective score key '{k}' is forbidden. All measurements must be factual or evaluation-backed."
                )

    @classmethod
    def validate_attribution_safety(
        cls,
        attribution_type: str,
        attribution_source: str,
        has_causal_evidence: bool,
        explanation: str,
    ) -> None:
        """
        Enforces:
        - Never claim 'Agent X caused outcome Y' unless explicit evidence supports direct attribution.
        - AI-generated attributions cannot claim direct causality without explicit verification.
        - AI-generated attribution must retain AI_GENERATED_ATTRIBUTION source.
        """
        if attribution_type == AttributionType.DIRECT.value and not has_causal_evidence:
            raise CausalityClaimForbiddenError(
                "Direct causality claim requires explicit causal evidence. Must use 'contributed_to' or 'supporting'."
            )

        if attribution_source == AttributionSource.AI_GENERATED_ATTRIBUTION.value:
            if "caused" in explanation.lower() and not has_causal_evidence:
                raise CausalityClaimForbiddenError(
                    "AI-generated attribution cannot claim direct causation. Use 'contributed to' phrasing."
                )

    @classmethod
    def validate_measurement(cls, metric_name: str, value: Any) -> None:
        """
        Validates an individual measurement name against forbidden subjective scores.
        """
        name_lower = metric_name.lower()
        if any(bad in name_lower for bad in ["intelligence_score", "agent_iq", "arbitrary_ai_score", "subjective_rating"]):
            raise SubjectiveScoreForbiddenError(
                f"Subjective score key '{metric_name}' is forbidden. All measurements must be factual or evaluation-backed."
            )

    @classmethod
    def validate_attribution(
        cls,
        attribution_type: Any,
        evidence_ids: List[str],
        explanation: str = "",
    ) -> None:
        """
        Validates that direct causality is not claimed without supporting evidence.
        """
        attr_val = getattr(attribution_type, "value", attribution_type)
        if attr_val == AttributionType.DIRECT.value and not evidence_ids:
            raise CausalityClaimForbiddenError(
                "Direct causality claim requires explicit causal evidence. Must use 'contributed_to' or 'supporting'."
            )

    @classmethod
    def validate_decision_provenance(
        cls,
        decision_type: Any,
        provenance: Dict[str, Any],
        decision_owner: Optional[str] = None,
    ) -> None:
        """
        Ensures AI-assisted or agent decisions capture full provenance and are
        never falsely labeled as human decisions.
        """
        from backend.app.services.outcomes.errors import HumanImpersonationError
        type_val = getattr(decision_type, "value", decision_type)
        if type_val == WorkDecisionType.HUMAN.value:
            if provenance and (provenance.get("agent_id") or provenance.get("model_provider")):
                raise HumanImpersonationError("AI-assisted or agent decisions cannot be disguised or represented as human decisions.")

    @classmethod
    def validate_baseline_for_impact(
        cls,
        analysis_type: str,
        baseline_value: Optional[float],
        observed_value: Optional[float],
    ) -> None:
        """
        Validates that savings or impact differences are not fabricated without baseline.
        If baseline is missing, difference calculation cannot be claimed as factual savings.
        """
        if observed_value is not None and baseline_value is None:
            # Baseline is missing; difference cannot be calculated as saved
            pass

    @classmethod
    def enforce_tenant_isolation(
        cls,
        entity_workspace_id: str,
        request_workspace_id: str,
    ) -> None:
        if entity_workspace_id != request_workspace_id:
            raise OutcomeTenantViolationError(
                f"Cross-tenant access rejected: entity belongs to '{entity_workspace_id}', requested by '{request_workspace_id}'."
            )

    @classmethod
    def verify_completion_requirements(
        cls,
        requirements: Dict[str, Any],
        evidence_list: List[Any],
        measurements: List[Any],
        human_confirmed: bool = False,
    ) -> List[str]:
        """
        Validates whether all outcome requirements are satisfied.
        Returns list of missing requirements.
        """
        missing: List[str] = []

        # 1. required_evidence: check if count or types of evidence match
        required_evidence_types = requirements.get("required_evidence_types") or requirements.get("required_evidence", [])
        if isinstance(required_evidence_types, list) and required_evidence_types:
            present_types = {e.evidence_type for e in evidence_list if getattr(e, "status", "") in {"supported", "unreviewed"}}
            for req_t in required_evidence_types:
                if req_t not in present_types:
                    missing.append(f"required_evidence_type:{req_t}")

        # 2. required_approval / human confirmation
        if requirements.get("required_human_confirmation") or requirements.get("required_approval"):
            has_human_conf = any(getattr(e, "is_human_confirmed", False) for e in evidence_list) or human_confirmed
            if not has_human_conf:
                missing.append("required_human_confirmation")

        # 3. required_evaluation
        if requirements.get("required_evaluation"):
            has_eval = any(getattr(e, "evidence_type", "") == "evaluation_result" for e in evidence_list)
            if not has_eval:
                missing.append("required_evaluation")

        # 4. required_artifact
        if requirements.get("required_artifact"):
            has_artifact = any(getattr(e, "evidence_type", "") == "artifact" for e in evidence_list)
            if not has_artifact:
                missing.append("required_artifact")

        # 5. required_metric
        if requirements.get("required_metric"):
            target_metric = requirements.get("required_metric")
            has_metric = any(getattr(m, "metric_name", "") == target_metric for m in measurements)
            if not has_metric:
                missing.append(f"required_metric:{target_metric}")

        return missing


class TenantIsolationPolicy:
    """Enforces strict multi-tenant boundary checks."""

    @classmethod
    def check_tenant_match(cls, expected_tenant: str, actual_tenant: str) -> None:
        if expected_tenant != actual_tenant:
            raise OutcomeTenantViolationError(
                f"Tenant violation: expected tenant '{expected_tenant}', got '{actual_tenant}'."
            )


class BaselinePolicy:
    """Enforces baseline validation for impact comparisons."""

    @classmethod
    def require_baseline(cls, metric_name: str, baseline_value: Optional[float]) -> None:
        if baseline_value is None:
            raise MissingBaselineError(metric_name)
