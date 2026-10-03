"""
Deterministic failure classifier for Step 35: AI Reliability, Resilience & Chaos Engineering Layer.
Evaluates exceptions and failure metadata to determine retryability, recovery path, and human requirements.
Never lets LLMs determine retryability.
"""
from typing import Any, Dict, Optional
from backend.app.services.reliability.schemas import FailureClassificationResult


class FailureClassifier:
    """
    Deterministic rule-based failure classifier.
    Maps system exceptions and error codes into structured resilience directives.
    """

    @classmethod
    def classify(
        cls,
        error: Optional[Exception] = None,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None,
        status_code: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FailureClassificationResult:
        msg = (error_message or (str(error) if error else "")).lower()
        etype = (error_type or (error.__class__.__name__ if error else "")).lower()
        code = status_code or (metadata.get("status_code") if metadata else None)

        # 1. Authorization & Security (Permanent, non-retryable)
        if (
            "unauthorized" in etype
            or "forbidden" in etype
            or "permission" in msg
            or "access_denied" in msg
            or code in {401, 403}
        ):
            if "token_expired" in msg or "reauth" in msg:
                return FailureClassificationResult(
                    classification="authentication",
                    retryable=False,
                    recoverable=True,
                    requires_human=False,
                    recommended_action="refresh_credentials_and_reauthenticate",
                    rationale="Authentication token expired or rejected.",
                )
            return FailureClassificationResult(
                classification="authorization",
                retryable=False,
                recoverable=False,
                requires_human=True,
                recommended_action="escalate_to_admin_or_request_rbac_grant",
                rationale="Permission or tenant boundary check denied access; retry is strictly prohibited.",
            )

        # 2. Policy Denied & Governance
        if "governance" in msg or "policy_bypass" in msg or "guardrail" in msg:
            return FailureClassificationResult(
                classification="policy_denied",
                retryable=False,
                recoverable=False,
                requires_human=True,
                recommended_action="review_governance_policy_or_request_exemption",
                rationale="Execution blocked by Step 32 AI Governance policy.",
            )

        # 3. Human in the Loop Required
        if "hitl" in msg or "approval_required" in msg or "human_approval" in msg:
            return FailureClassificationResult(
                classification="human_required",
                retryable=False,
                recoverable=True,
                requires_human=True,
                recommended_action="await_human_approval_in_step_18_approvals",
                rationale="Action requires explicit human authorization before proceeding.",
            )

        # 4. Rate Limiting & Capacity
        if "rate_limit" in msg or "429" in msg or code == 429 or "quota_exceeded" in msg:
            return FailureClassificationResult(
                classification="rate_limited",
                retryable=True,
                recoverable=True,
                requires_human=False,
                recommended_action="apply_exponential_backoff_and_jitter",
                rationale="Target service or AI provider returned HTTP 429 Rate Limit.",
            )

        if "overloaded" in msg or "capacity" in msg or "503" in msg or code == 503:
            return FailureClassificationResult(
                classification="capacity",
                retryable=True,
                recoverable=True,
                requires_human=False,
                recommended_action="route_to_fallback_provider_or_backoff",
                rationale="Target service or model provider is temporarily saturated.",
            )

        # 5. Timeouts & Network Interruptions
        if "timeout" in msg or "timed out" in msg or "deadline" in msg or code in {408, 504}:
            return FailureClassificationResult(
                classification="timeout",
                retryable=True,
                recoverable=True,
                requires_human=False,
                recommended_action="retry_with_extended_timeout_or_resume_checkpoint",
                rationale="Execution exceeded bounded operation timeout.",
            )

        if "connection" in msg or "econnrefused" in msg or "network" in msg or "disconnected" in msg:
            return FailureClassificationResult(
                classification="network",
                retryable=True,
                recoverable=True,
                requires_human=False,
                recommended_action="reconnect_and_retry_bounded",
                rationale="Underlying network socket connection severed or unreachable.",
            )

        # 6. Model & AI Gateway Specific
        if "model_not_found" in msg or "model_decommissioned" in msg:
            return FailureClassificationResult(
                classification="model_unavailable",
                retryable=False,
                recoverable=True,
                requires_human=False,
                recommended_action="trigger_model_fallback_router",
                rationale="Requested model is deprecated or unavailable in target region.",
            )

        if "provider_down" in msg or "bad_gateway" in msg or code == 502:
            return FailureClassificationResult(
                classification="provider_unavailable",
                retryable=True,
                recoverable=True,
                requires_human=False,
                recommended_action="open_circuit_breaker_and_activate_fallback",
                rationale="External AI provider service outage detected.",
            )

        # 7. Connector & Tool Outages
        if "connector" in msg or "connector_error" in etype:
            return FailureClassificationResult(
                classification="connector_failure",
                retryable=True,
                recoverable=True,
                requires_human=False,
                recommended_action="retry_idempotent_operation_or_pause_workflow",
                rationale="External connector API or service returned error.",
            )

        if "tool" in msg or "tool_error" in etype:
            return FailureClassificationResult(
                classification="tool_failure",
                retryable=False,
                recoverable=True,
                requires_human=False,
                recommended_action="fall_back_to_alternate_tool_or_deterministic_mode",
                rationale="Internal tool execution threw exception.",
            )

        # 8. Database Failures
        if "operationalerror" in etype or "deadlock" in msg or "database" in msg:
            return FailureClassificationResult(
                classification="database_failure",
                retryable=True,
                recoverable=True,
                requires_human=False,
                recommended_action="retry_transaction_with_backoff",
                rationale="Database connection or transaction conflict encountered.",
            )

        # 9. Validation & Request Malformation (Permanent)
        if "validation" in msg or "valueerror" in etype or code in {400, 422}:
            return FailureClassificationResult(
                classification="validation",
                retryable=False,
                recoverable=False,
                requires_human=False,
                recommended_action="fail_fast_and_correct_input_schema",
                rationale="Input payload is malformed or invalid against schema.",
            )

        # 10. Default / Unknown Fallback
        return FailureClassificationResult(
            classification="unknown",
            retryable=False,
            recoverable=True,
            requires_human=True,
            recommended_action="record_telemetry_and_await_investigation",
            rationale="Unclassified failure pattern.",
        )
