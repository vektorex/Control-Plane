"""
Deterministic Severity Calculation Engine for Step 34.
Evaluates signals and incidents based on explicit rule-based policies.
Never uses subjective AI scoring.
"""
from typing import Any, Dict, List, Optional, Tuple


def calculate_signal_severity(
    signal_type: str,
    resource_classification: Optional[str] = None,
    repetition_count: int = 1,
    is_admin_actor: bool = False,
    tenant_boundary_crossed: bool = False,
    governance_violated: bool = False,
    has_active_legal_hold: bool = False,
    metadata: Optional[Dict[str, Any]] = None,
) -> Tuple[str, List[str]]:
    """
    Calculates deterministic severity level and exact list of justifying reasons.
    Levels: info, low, medium, high, critical.
    """
    reasons: List[str] = []
    base_severity = "low"
    meta = metadata or {}

    # 1. Critical triggers
    if tenant_boundary_crossed or signal_type == "tenant_isolation_violation":
        reasons.append("Cross-tenant isolation boundary violated")
        return "critical", reasons

    if has_active_legal_hold or "legal_hold" in signal_type or "retention_bypass" in signal_type:
        reasons.append("Attempted bypass or deletion of asset under active legal hold")
        return "critical", reasons

    if signal_type in {"privilege_escalation_attempt", "policy_bypass_attempt"} and is_admin_actor:
        reasons.append("Administrative actor attempted unauthorized privilege modification or bypass")
        return "critical", reasons

    # 2. High severity triggers
    if resource_classification == "restricted":
        base_severity = "high"
        reasons.append("Subject resource classification is 'restricted'")

    if signal_type in {"secret_detection", "pii_exposure"} and resource_classification in {"confidential", "restricted"}:
        base_severity = "high"
        reasons.append(f"Secret or PII exposure in {resource_classification} scope")

    if signal_type == "prompt_injection" and meta.get("category") in {"system_override", "secret_extraction"}:
        base_severity = "high"
        reasons.append(f"Prompt injection targeting {meta.get('category')}")

    if signal_type in {"bulk_deletion_attempt", "data_export_anomaly"} and resource_classification in {"confidential", "restricted"}:
        base_severity = "high"
        reasons.append(f"Mass lifecycle action targeting {resource_classification} data")

    # 3. Medium severity triggers
    if base_severity == "low":
        if signal_type in {
            "prompt_injection",
            "tool_abuse",
            "connector_abuse",
            "webhook_abuse",
            "suspicious_workflow",
            "rate_limit_violation",
            "cost_anomaly",
            "malicious_artifact",
        }:
            base_severity = "medium"
            reasons.append(f"Signal type '{signal_type}' represents elevated operational risk")

        if governance_violated:
            base_severity = "medium"
            reasons.append("Step 32 AI Governance policy violation recorded")

        if resource_classification == "confidential":
            base_severity = "medium"
            reasons.append("Subject resource classification is 'confidential'")

    # 4. Repetition escalation
    if repetition_count >= 10:
        if base_severity in {"low", "medium"}:
            base_severity = "high"
        reasons.append(f"High repetition detected ({repetition_count} occurrences)")
    elif repetition_count >= 5:
        if base_severity == "low":
            base_severity = "medium"
        reasons.append(f"Repeated occurrences detected ({repetition_count} times)")

    # 5. Fallback rationale
    if not reasons:
        reasons.append(f"Standard baseline evaluation for {signal_type}")

    return base_severity, reasons
