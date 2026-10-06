"""
Impact Analysis Engine for Step 43:
AI Outcome Intelligence & Work Impact Layer.
Computes factual, evidence-backed impact across time, cost, quality, risk, and operations.
Strictly prohibits fabricated baselines, imaginary savings, and subjective scores.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.app.services.outcomes.errors import MissingBaselineError, SubjectiveScoreForbiddenError
from backend.app.services.outcomes.models import ImpactAnalysis
from backend.app.services.outcomes.registry import (
    AttributionConfidence,
    ImpactAnalysisType,
)


class ImpactCalculator:
    """
    Computes evidence-backed comparisons across operational categories.
    """

    @classmethod
    def calculate_time_saved(
        cls, baseline_minutes: Optional[float], observed_minutes: Optional[float]
    ) -> float:
        """Calculates time difference. Raises MissingBaselineError if baseline is missing."""
        if baseline_minutes is None:
            raise MissingBaselineError("duration_minutes")
        if observed_minutes is None:
            return 0.0
        return observed_minutes - baseline_minutes

    @classmethod
    def calculate_cost_impact(
        cls, baseline_cost: Optional[float], observed_cost: Optional[float]
    ) -> float:
        """Calculates cost difference. Raises MissingBaselineError if baseline is missing."""
        if baseline_cost is None:
            raise MissingBaselineError("business_cost")
        if observed_cost is None:
            return 0.0
        return observed_cost - baseline_cost

    @staticmethod
    def analyze_time_impact(
        outcome_id: str,
        baseline_duration_ms: Optional[float],
        observed_duration_ms: Optional[float],
        evidence_ids: List[str],
        unit: str = "ms",
    ) -> ImpactAnalysis:
        """
        Compares baseline duration vs observed duration.
        If baseline is missing, reports observed duration without claiming fabricated time savings.
        """
        observations = []
        limitations = None
        diff_value = None
        confidence = AttributionConfidence.OBSERVED.value

        if observed_duration_ms is not None:
            observations.append({"metric": "observed_duration", "value": observed_duration_ms, "unit": unit})

        if baseline_duration_ms is not None and observed_duration_ms is not None:
            diff_value = baseline_duration_ms - observed_duration_ms
            observations.append({"metric": "baseline_duration", "value": baseline_duration_ms, "unit": unit})
            observations.append({"metric": "duration_difference", "value": diff_value, "unit": unit})
            summary = f"Observed duration of {observed_duration_ms} {unit} compared to baseline of {baseline_duration_ms} {unit} (difference: {diff_value} {unit})."
        elif observed_duration_ms is not None:
            limitations = "No baseline duration provided; difference cannot be calculated as saved time."
            summary = f"Observed execution duration: {observed_duration_ms} {unit}."
            confidence = AttributionConfidence.ESTIMATED.value
        else:
            limitations = "Insufficient execution duration observations."
            summary = "Execution duration data unavailable."
            confidence = AttributionConfidence.INFERRED.value

        return ImpactAnalysis(
            outcome_id=outcome_id,
            analysis_type=ImpactAnalysisType.TIME_SAVED.value,
            summary=summary,
            evidence_ids=evidence_ids or [],
            observations=observations,
            limitations=limitations,
            attribution_confidence=confidence,
            baseline_value=baseline_duration_ms,
            observed_value=observed_duration_ms,
            difference_value=diff_value,
            unit=unit,
            created_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def analyze_cost_impact(
        outcome_id: str,
        observed_platform_cost: float,
        baseline_business_cost: Optional[float],
        evidence_ids: List[str],
        currency: str = "USD",
    ) -> ImpactAnalysis:
        """
        Reports observed platform execution cost and compares to baseline if present.
        Explicitly forbids fabricating business savings if baseline is unavailable.
        """
        observations = [
            {"category": "observed_platform_cost", "value": observed_platform_cost, "currency": currency}
        ]
        diff = None
        limitations = None
        confidence = AttributionConfidence.OBSERVED.value

        if baseline_business_cost is not None:
            diff = baseline_business_cost - observed_platform_cost
            observations.append({"category": "baseline_cost", "value": baseline_business_cost, "currency": currency})
            observations.append({"category": "estimated_cost_delta", "value": diff, "currency": currency})
            summary = f"Platform execution cost: ${observed_platform_cost:.4f} {currency} vs baseline ${baseline_business_cost:.4f} {currency}."
        else:
            limitations = "Baseline business cost not established; no monetary savings claimed."
            summary = f"Platform execution cost recorded at ${observed_platform_cost:.4f} {currency}."

        return ImpactAnalysis(
            outcome_id=outcome_id,
            analysis_type=ImpactAnalysisType.COST_CHANGE.value,
            summary=summary,
            evidence_ids=evidence_ids or [],
            observations=observations,
            limitations=limitations,
            attribution_confidence=confidence,
            baseline_value=baseline_business_cost,
            observed_value=observed_platform_cost,
            difference_value=diff,
            unit=currency,
            created_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def analyze_quality_impact(
        outcome_id: str,
        assertions_passed: int,
        assertions_failed: int,
        evidence_ids: List[str],
        citation_findings: Optional[List[Dict[str, Any]]] = None,
        grounding_findings: Optional[List[Dict[str, Any]]] = None,
        format_compliance: bool = True,
    ) -> ImpactAnalysis:
        """
        Factual quality metrics derived from Evaluation Lab and verification assertions.
        Does NOT invent arbitrary quality numbers.
        """
        total = assertions_passed + assertions_failed
        observations = [
            {"metric": "assertions_passed", "value": assertions_passed},
            {"metric": "assertions_failed", "value": assertions_failed},
            {"metric": "format_compliance", "value": format_compliance},
        ]
        if citation_findings:
            observations.append({"metric": "citation_count", "value": len(citation_findings)})
        if grounding_findings:
            observations.append({"metric": "grounding_findings_count", "value": len(grounding_findings)})

        pass_rate = (assertions_passed / total * 100.0) if total > 0 else None
        summary = (
            f"Evaluation verified {assertions_passed}/{total} assertions passed "
            f"({pass_rate:.1f}% assertion pass rate) with format_compliance={format_compliance}."
            if total > 0
            else f"Evaluation completed with format_compliance={format_compliance}."
        )

        return ImpactAnalysis(
            outcome_id=outcome_id,
            analysis_type=ImpactAnalysisType.QUALITY_CHANGE.value,
            summary=summary,
            evidence_ids=evidence_ids or [],
            observations=observations,
            limitations=None if total > 0 else "No assertions evaluated.",
            attribution_confidence=AttributionConfidence.OBSERVED.value,
            baseline_value=None,
            observed_value=float(assertions_passed),
            difference_value=None,
            unit="assertions",
            created_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def analyze_risk_impact(
        outcome_id: str,
        security_findings_count: int,
        policy_violations_count: int,
        permissions_changed: List[str],
        evidence_ids: List[str],
    ) -> ImpactAnalysis:
        """
        Factual observations from Security Operations & Governance.
        """
        observations = [
            {"metric": "security_findings", "count": security_findings_count},
            {"metric": "policy_violations", "count": policy_violations_count},
            {"metric": "permissions_modified", "permissions": permissions_changed},
        ]
        summary = (
            f"Security & Governance review: {security_findings_count} security findings, "
            f"{policy_violations_count} policy violations, {len(permissions_changed)} permission adjustments."
        )

        return ImpactAnalysis(
            outcome_id=outcome_id,
            analysis_type=ImpactAnalysisType.RISK_CHANGE.value,
            summary=summary,
            evidence_ids=evidence_ids or [],
            observations=observations,
            limitations=None,
            attribution_confidence=AttributionConfidence.OBSERVED.value,
            baseline_value=0.0,
            observed_value=float(security_findings_count + policy_violations_count),
            difference_value=None,
            unit="findings",
            created_at=datetime.now(timezone.utc),
        )
