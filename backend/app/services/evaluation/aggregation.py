import logging
from typing import List

from backend.app.services.evaluation.policies import EvaluationPolicy
from backend.app.services.evaluation.schemas import (
    CheckResult,
    CheckType,
    EvaluationFindingItem,
    EvaluationRecommendation,
    EvaluationResult,
    EvaluationStatus,
    FindingStatus,
    UnsupportedClaim,
)

logger = logging.getLogger("evaluation.aggregation")


class EvaluationAggregator:
    """
    Aggregates individual evaluation check results into a structured EvaluationResult
    without generating arbitrary subjective global numeric scores.
    """

    @classmethod
    def aggregate(
        cls,
        checks: List[CheckResult],
        policy: EvaluationPolicy,
        attempt: int = 1,
        duration_ms: int = 0,
    ) -> EvaluationResult:
        all_findings: List[EvaluationFindingItem] = []
        unsupported_claims: List[UnsupportedClaim] = []
        missing_requirements: List[str] = []
        format_issues: List[str] = []
        citation_issues: List[str] = []
        safety_issues: List[str] = []
        revision_reasons: List[str] = []

        has_failed = False
        has_warning = False
        has_safety_fail = False

        for check in checks:
            all_findings.extend(check.findings)

            if check.status == FindingStatus.FAILED:
                has_failed = True
                if check.type == CheckType.SAFETY:
                    has_safety_fail = True
            elif check.status == FindingStatus.WARNING:
                has_warning = True

            # Harvest category-specific issues
            formatted_issues = [str(i.description if hasattr(i, "description") else i) for i in check.issues]

            if check.type == CheckType.GROUNDING:
                claims_data = check.metadata.get("unsupported_claims", [])
                for c in claims_data:
                    unsupported_claims.append(
                        UnsupportedClaim(
                            claim=c.get("claim", ""),
                            reason=c.get("reason", ""),
                            confidence=c.get("confidence", 1.0),
                            evidence_ids=c.get("evidence_ids", []),
                        )
                    )
                if check.status != FindingStatus.PASSED and formatted_issues:
                    revision_reasons.extend(formatted_issues)

            elif check.type == CheckType.COMPLETENESS:
                missing = check.metadata.get("missing_requirements", [])
                missing_requirements.extend(missing)
                if check.status != FindingStatus.PASSED and formatted_issues:
                    revision_reasons.extend(formatted_issues)

            elif check.type == CheckType.FORMAT:
                format_issues.extend(formatted_issues)
                if check.status != FindingStatus.PASSED and formatted_issues:
                    revision_reasons.extend(formatted_issues)

            elif check.type == CheckType.CITATION:
                citation_issues.extend(formatted_issues)
                if check.status != FindingStatus.PASSED and formatted_issues:
                    revision_reasons.extend(formatted_issues)

            elif check.type == CheckType.SAFETY:
                safety_issues.extend(formatted_issues)
                if check.status != FindingStatus.PASSED and formatted_issues:
                    revision_reasons.extend(formatted_issues)

        # Determine overall status
        if has_failed:
            overall_status = EvaluationStatus.FAILED
        elif has_warning:
            if policy.strict_mode:
                overall_status = EvaluationStatus.FAILED
            else:
                overall_status = EvaluationStatus.WARNING
        else:
            overall_status = EvaluationStatus.PASSED

        # Determine orchestrator recommendation
        can_revise = attempt <= policy.max_revision_attempts and policy.auto_revise_on_fail

        if overall_status == EvaluationStatus.PASSED:
            recommendation = EvaluationRecommendation.ACCEPT

        elif overall_status == EvaluationStatus.WARNING:
            if policy.strict_mode:
                if can_revise:
                    recommendation = EvaluationRecommendation.REVISE
                else:
                    recommendation = EvaluationRecommendation.FAIL
            else:
                if policy.allow_warning_completion:
                    recommendation = EvaluationRecommendation.ACCEPT
                elif can_revise:
                    recommendation = EvaluationRecommendation.REVISE
                else:
                    recommendation = EvaluationRecommendation.ACCEPT

        else:  # FAILED
            if has_safety_fail:
                # Fatal safety failure cannot be blindly retried if unsafe
                recommendation = EvaluationRecommendation.FAIL
            elif can_revise:
                recommendation = EvaluationRecommendation.REVISE
            else:
                recommendation = EvaluationRecommendation.FAIL

        # Build concise human-readable summary
        passed_count = sum(1 for c in checks if c.status == FindingStatus.PASSED)
        total_checks = len(checks)

        if overall_status == EvaluationStatus.PASSED:
            summary = f"All {total_checks} verification checks passed successfully."
        elif overall_status == EvaluationStatus.WARNING:
            summary = f"Verification passed with warnings ({passed_count}/{total_checks} passed)."
        else:
            summary = f"Verification failed ({passed_count}/{total_checks} checks passed)."

        return EvaluationResult(
            status=overall_status,
            recommendation=recommendation,
            mode=policy.mode,
            attempt=attempt,
            checks=checks,
            findings=all_findings,
            summary=summary,
            duration_ms=duration_ms,
            revision_suggested=(recommendation == EvaluationRecommendation.REVISE),
            revision_reasons=revision_reasons,
            unsupported_claims=unsupported_claims,
            missing_requirements=missing_requirements,
            format_issues=format_issues,
            citation_issues=citation_issues,
            safety_issues=safety_issues,
        )
