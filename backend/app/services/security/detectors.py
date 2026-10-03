"""
Deterministic Security Detectors for Step 34.
Implements the 16 required detectors analyzing normalized SecurityEvent objects.
Never uses non-deterministic or LLM-generated security decisions.
"""
import re
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from backend.app.services.data_governance.redaction import detect_findings
from backend.app.services.security.schemas import SecurityEventNormalized, SecuritySignalCreate
from backend.app.services.security.severity import calculate_signal_severity


class BaseDetector:
    """Base interface for all deterministic security detectors."""
    detector_name: str = "base_detector"

    def detect(self, event: SecurityEventNormalized) -> List[SecuritySignalCreate]:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# 1. Authentication Detector
# ---------------------------------------------------------------------------
class AuthenticationDetector(BaseDetector):
    detector_name = "authentication_detector"

    def detect(self, event: SecurityEventNormalized) -> List[SecuritySignalCreate]:
        signals: List[SecuritySignalCreate] = []
        if event.source_type == "auth" and event.result in {"failed", "denied"}:
            failure_count = event.risk_metadata.get("failure_count", 1)
            sig_type = "authentication_anomaly" if failure_count >= 5 else "authentication_failure"

            sev, reasons = calculate_signal_severity(
                signal_type=sig_type,
                repetition_count=failure_count,
                metadata=event.risk_metadata,
            )

            signals.append(
                SecuritySignalCreate(
                    organization_id=event.organization_id,
                    workspace_id=event.workspace_id,
                    project_id=event.project_id,
                    signal_type=sig_type,
                    source_type="auth",
                    source_id=event.source_id,
                    actor_type=event.actor_type,
                    actor_id=event.actor_id,
                    resource_type=event.resource_type,
                    resource_id=event.resource_id,
                    severity=sev,
                    confidence=0.95,
                    timestamp=event.timestamp,
                    request_id=event.request_id,
                    correlation_id=event.correlation_id,
                    metadata={
                        "reasons": reasons,
                        "failure_count": failure_count,
                        "action": event.action,
                    },
                )
            )
        return signals


# ---------------------------------------------------------------------------
# 2. Authorization Detector
# ---------------------------------------------------------------------------
class AuthorizationDetector(BaseDetector):
    detector_name = "authorization_detector"

    def detect(self, event: SecurityEventNormalized) -> List[SecuritySignalCreate]:
        signals: List[SecuritySignalCreate] = []
        if event.result == "denied" or event.action == "access_denied":
            denial_count = event.risk_metadata.get("denial_count", 1)
            classification = event.risk_metadata.get("data_classification")
            is_admin = event.risk_metadata.get("is_admin", False)

            sig_type = "authorization_anomaly" if denial_count >= 3 else "authorization_denied"
            sev, reasons = calculate_signal_severity(
                signal_type=sig_type,
                resource_classification=classification,
                repetition_count=denial_count,
                is_admin_actor=is_admin,
            )

            signals.append(
                SecuritySignalCreate(
                    organization_id=event.organization_id,
                    workspace_id=event.workspace_id,
                    project_id=event.project_id,
                    signal_type=sig_type,
                    source_type=event.source_type,
                    source_id=event.source_id,
                    actor_type=event.actor_type,
                    actor_id=event.actor_id,
                    resource_type=event.resource_type,
                    resource_id=event.resource_id,
                    severity=sev,
                    confidence=1.0,
                    timestamp=event.timestamp,
                    request_id=event.request_id,
                    correlation_id=event.correlation_id,
                    metadata={"reasons": reasons, "denial_count": denial_count},
                )
            )
        return signals


# ---------------------------------------------------------------------------
# 3. Rate Limit Detector
# ---------------------------------------------------------------------------
class RateLimitDetector(BaseDetector):
    detector_name = "rate_limit_detector"

    def detect(self, event: SecurityEventNormalized) -> List[SecuritySignalCreate]:
        signals: List[SecuritySignalCreate] = []
        if event.result == "rate_limited" or "rate_limit" in event.action:
            count = event.risk_metadata.get("rate_limit_exceeded_count", 1)
            sev, reasons = calculate_signal_severity(
                signal_type="rate_limit_violation",
                repetition_count=count,
            )

            signals.append(
                SecuritySignalCreate(
                    organization_id=event.organization_id,
                    workspace_id=event.workspace_id,
                    project_id=event.project_id,
                    signal_type="rate_limit_violation",
                    source_type=event.source_type,
                    source_id=event.source_id,
                    actor_type=event.actor_type,
                    actor_id=event.actor_id,
                    resource_type=event.resource_type,
                    resource_id=event.resource_id,
                    severity=sev,
                    confidence=1.0,
                    timestamp=event.timestamp,
                    request_id=event.request_id,
                    correlation_id=event.correlation_id,
                    metadata={"reasons": reasons, "count": count},
                )
            )
        return signals


# ---------------------------------------------------------------------------
# 4. Secret Exposure Detector (Reusing Step 33 Deterministic Redaction)
# ---------------------------------------------------------------------------
class SecretExposureDetector(BaseDetector):
    detector_name = "secret_exposure_detector"

    def detect(self, event: SecurityEventNormalized) -> List[SecuritySignalCreate]:
        signals: List[SecuritySignalCreate] = []
        text_payload = ""

        # Extract textual fields from payload
        for k, v in event.payload.items():
            if isinstance(v, str):
                text_payload += f" {v}"
            elif isinstance(v, dict):
                text_payload += f" {str(v)}"

        if text_payload:
            findings = detect_findings(text_payload)
            secret_findings = [f for f in findings if f.get("is_secret")]
            pii_findings = [f for f in findings if f.get("is_personal_data")]

            if secret_findings:
                sev, reasons = calculate_signal_severity(
                    signal_type="secret_detection",
                    resource_classification=event.risk_metadata.get("data_classification", "confidential"),
                )
                signals.append(
                    SecuritySignalCreate(
                        organization_id=event.organization_id,
                        workspace_id=event.workspace_id,
                        project_id=event.project_id,
                        signal_type="secret_detection",
                        source_type=event.source_type,
                        source_id=event.source_id,
                        actor_type=event.actor_type,
                        actor_id=event.actor_id,
                        resource_type=event.resource_type,
                        resource_id=event.resource_id,
                        severity=sev,
                        confidence=1.0,
                        timestamp=event.timestamp,
                        request_id=event.request_id,
                        correlation_id=event.correlation_id,
                        metadata={
                            "reasons": reasons,
                            "detected_secret_count": len(secret_findings),
                            "types": [f["finding_type"] for f in secret_findings],
                        },
                    )
                )

            if pii_findings:
                sev, reasons = calculate_signal_severity(
                    signal_type="pii_exposure",
                    resource_classification=event.risk_metadata.get("data_classification", "internal"),
                )
                signals.append(
                    SecuritySignalCreate(
                        organization_id=event.organization_id,
                        workspace_id=event.workspace_id,
                        project_id=event.project_id,
                        signal_type="pii_exposure",
                        source_type=event.source_type,
                        source_id=event.source_id,
                        actor_type=event.actor_type,
                        actor_id=event.actor_id,
                        resource_type=event.resource_type,
                        resource_id=event.resource_id,
                        severity=sev,
                        confidence=0.9,
                        timestamp=event.timestamp,
                        request_id=event.request_id,
                        correlation_id=event.correlation_id,
                        metadata={
                            "reasons": reasons,
                            "detected_pii_count": len(pii_findings),
                            "types": [f["finding_type"] for f in pii_findings],
                        },
                    )
                )
        return signals


# ---------------------------------------------------------------------------
# 5. Prompt Injection Detector (Deterministic Heuristics)
# ---------------------------------------------------------------------------
class PromptInjectionDetector(BaseDetector):
    detector_name = "prompt_injection_detector"

    INJECTION_PATTERNS = [
        (re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|directives|prompts)", re.IGNORECASE), "system_override", "high"),
        (re.compile(r"reveal\s+(your\s+)?(system\s+prompt|initial\s+instructions|developer\s+message)", re.IGNORECASE), "system_prompt_leak", "high"),
        (re.compile(r"you\s+are\s+now\s+(in\s+)?developer\s+mode|dan\s+mode|unrestricted\s+mode", re.IGNORECASE), "jailbreak_attempt", "high"),
        (re.compile(r"print\s+(all\s+)?(api[_\s]?keys?|secrets?|tokens?|passwords?)", re.IGNORECASE), "secret_extraction", "critical"),
        (re.compile(r"bypass\s+all\s+(security|governance|content\s+filters)", re.IGNORECASE), "policy_bypass", "critical"),
        (re.compile(r"<system_instructions>|<\/system_instructions>", re.IGNORECASE), "tag_injection", "medium"),
    ]

    def detect(self, event: SecurityEventNormalized) -> List[SecuritySignalCreate]:
        signals: List[SecuritySignalCreate] = []
        content = ""

        # Check prompt text, tool inputs, or connector inputs
        for field in ["prompt", "content", "query", "input", "message"]:
            if field in event.payload and isinstance(event.payload[field], str):
                content += f" {event.payload[field]}"

        for pattern, category, base_sev in self.INJECTION_PATTERNS:
            match = pattern.search(content)
            if match:
                sev, reasons = calculate_signal_severity(
                    signal_type="prompt_injection",
                    resource_classification=event.risk_metadata.get("data_classification", "internal"),
                    metadata={"category": category},
                )
                signals.append(
                    SecuritySignalCreate(
                        organization_id=event.organization_id,
                        workspace_id=event.workspace_id,
                        project_id=event.project_id,
                        signal_type="prompt_injection",
                        source_type=event.source_type,
                        source_id=event.source_id,
                        actor_type=event.actor_type,
                        actor_id=event.actor_id,
                        resource_type=event.resource_type,
                        resource_id=event.resource_id,
                        severity=sev,
                        confidence=0.92,
                        timestamp=event.timestamp,
                        request_id=event.request_id,
                        correlation_id=event.correlation_id,
                        metadata={
                            "reasons": reasons,
                            "category": category,
                            "matched_pattern": pattern.pattern,
                        },
                    )
                )
                break  # Record highest severity match
        return signals


# ---------------------------------------------------------------------------
# 6. Tool Abuse Detector
# ---------------------------------------------------------------------------
class ToolAbuseDetector(BaseDetector):
    detector_name = "tool_abuse_detector"

    def detect(self, event: SecurityEventNormalized) -> List[SecuritySignalCreate]:
        signals: List[SecuritySignalCreate] = []
        if event.source_type == "tool":
            spike_count = event.risk_metadata.get("invocation_count_last_minute", 1)
            is_denied = event.result in {"denied", "blocked"}

            if spike_count >= 30 or (is_denied and spike_count >= 5):
                sev, reasons = calculate_signal_severity(
                    signal_type="tool_abuse",
                    repetition_count=spike_count,
                    governance_violated=is_denied,
                )
                signals.append(
                    SecuritySignalCreate(
                        organization_id=event.organization_id,
                        workspace_id=event.workspace_id,
                        project_id=event.project_id,
                        signal_type="tool_abuse",
                        source_type="tool",
                        source_id=event.source_id,
                        actor_type=event.actor_type,
                        actor_id=event.actor_id,
                        resource_type="tool",
                        resource_id=event.resource_id,
                        severity=sev,
                        confidence=0.95,
                        timestamp=event.timestamp,
                        request_id=event.request_id,
                        correlation_id=event.correlation_id,
                        metadata={"reasons": reasons, "invocation_count": spike_count},
                    )
                )
        return signals


# ---------------------------------------------------------------------------
# 7. Connector Abuse Detector
# ---------------------------------------------------------------------------
class ConnectorAbuseDetector(BaseDetector):
    detector_name = "connector_abuse_detector"

    def detect(self, event: SecurityEventNormalized) -> List[SecuritySignalCreate]:
        signals: List[SecuritySignalCreate] = []
        if event.source_type == "connector":
            dest_op = event.action in {"delete_repo", "purge_all", "delete_records"}
            is_denied = event.result in {"denied", "unauthorized"}
            query_volume = event.risk_metadata.get("query_volume", 1)

            if dest_op or (is_denied and query_volume >= 3) or query_volume >= 100:
                sev, reasons = calculate_signal_severity(
                    signal_type="connector_abuse",
                    repetition_count=query_volume,
                    governance_violated=is_denied,
                )
                signals.append(
                    SecuritySignalCreate(
                        organization_id=event.organization_id,
                        workspace_id=event.workspace_id,
                        project_id=event.project_id,
                        signal_type="connector_abuse",
                        source_type="connector",
                        source_id=event.source_id,
                        actor_type=event.actor_type,
                        actor_id=event.actor_id,
                        resource_type="connector",
                        resource_id=event.resource_id,
                        severity=sev,
                        confidence=0.95,
                        timestamp=event.timestamp,
                        request_id=event.request_id,
                        correlation_id=event.correlation_id,
                        metadata={
                            "reasons": reasons,
                            "destructive_op": dest_op,
                            "query_volume": query_volume,
                        },
                    )
                )
        return signals


# ---------------------------------------------------------------------------
# 8. Workflow Abuse Detector
# ---------------------------------------------------------------------------
class WorkflowAbuseDetector(BaseDetector):
    detector_name = "workflow_abuse_detector"

    def detect(self, event: SecurityEventNormalized) -> List[SecuritySignalCreate]:
        signals: List[SecuritySignalCreate] = []
        if event.source_type == "workflow":
            depth = event.risk_metadata.get("call_depth", 0)
            burst = event.risk_metadata.get("runs_in_last_minute", 1)

            if depth > 10 or burst > 20:
                sev, reasons = calculate_signal_severity(
                    signal_type="suspicious_workflow",
                    repetition_count=burst,
                )
                signals.append(
                    SecuritySignalCreate(
                        organization_id=event.organization_id,
                        workspace_id=event.workspace_id,
                        project_id=event.project_id,
                        signal_type="suspicious_workflow",
                        source_type="workflow",
                        source_id=event.source_id,
                        actor_type=event.actor_type,
                        actor_id=event.actor_id,
                        resource_type="workflow",
                        resource_id=event.resource_id,
                        severity=sev,
                        confidence=0.9,
                        timestamp=event.timestamp,
                        request_id=event.request_id,
                        correlation_id=event.correlation_id,
                        metadata={"reasons": reasons, "depth": depth, "burst": burst},
                    )
                )
        return signals


# ---------------------------------------------------------------------------
# 9. Data Export Detector
# ---------------------------------------------------------------------------
class DataExportDetector(BaseDetector):
    detector_name = "data_export_detector"

    def detect(self, event: SecurityEventNormalized) -> List[SecuritySignalCreate]:
        signals: List[SecuritySignalCreate] = []
        if "export" in event.action:
            classification = event.risk_metadata.get("data_classification")
            count = event.risk_metadata.get("export_count_last_hour", 1)

            if classification in {"confidential", "restricted"} or count >= 5:
                sev, reasons = calculate_signal_severity(
                    signal_type="data_export_anomaly",
                    resource_classification=classification,
                    repetition_count=count,
                )
                signals.append(
                    SecuritySignalCreate(
                        organization_id=event.organization_id,
                        workspace_id=event.workspace_id,
                        project_id=event.project_id,
                        signal_type="data_export_anomaly",
                        source_type="data_governance",
                        source_id=event.source_id,
                        actor_type=event.actor_type,
                        actor_id=event.actor_id,
                        resource_type="export",
                        resource_id=event.resource_id,
                        severity=sev,
                        confidence=0.95,
                        timestamp=event.timestamp,
                        request_id=event.request_id,
                        correlation_id=event.correlation_id,
                        metadata={
                            "reasons": reasons,
                            "classification": classification,
                            "export_count": count,
                        },
                    )
                )
        return signals


# ---------------------------------------------------------------------------
# 10. Deletion Detector
# ---------------------------------------------------------------------------
class DeletionDetector(BaseDetector):
    detector_name = "deletion_detector"

    def detect(self, event: SecurityEventNormalized) -> List[SecuritySignalCreate]:
        signals: List[SecuritySignalCreate] = []
        if "delete" in event.action:
            under_hold = event.risk_metadata.get("active_legal_hold", False)
            bulk_count = event.risk_metadata.get("asset_count", 1)
            classification = event.risk_metadata.get("data_classification")

            sig_type = "legal_hold_bypass_attempt" if under_hold else "bulk_deletion_attempt"
            if under_hold or bulk_count >= 10 or classification == "restricted":
                sev, reasons = calculate_signal_severity(
                    signal_type=sig_type,
                    resource_classification=classification,
                    repetition_count=bulk_count,
                    has_active_legal_hold=under_hold,
                )
                signals.append(
                    SecuritySignalCreate(
                        organization_id=event.organization_id,
                        workspace_id=event.workspace_id,
                        project_id=event.project_id,
                        signal_type=sig_type,
                        source_type="data_governance",
                        source_id=event.source_id,
                        actor_type=event.actor_type,
                        actor_id=event.actor_id,
                        resource_type="data_asset",
                        resource_id=event.resource_id,
                        severity=sev,
                        confidence=1.0,
                        timestamp=event.timestamp,
                        request_id=event.request_id,
                        correlation_id=event.correlation_id,
                        metadata={
                            "reasons": reasons,
                            "under_legal_hold": under_hold,
                            "bulk_count": bulk_count,
                        },
                    )
                )
        return signals


# ---------------------------------------------------------------------------
# 11. Privilege Escalation Detector
# ---------------------------------------------------------------------------
class PrivilegeEscalationDetector(BaseDetector):
    detector_name = "privilege_escalation_detector"

    def detect(self, event: SecurityEventNormalized) -> List[SecuritySignalCreate]:
        signals: List[SecuritySignalCreate] = []
        if event.action in {"role_update", "permission_grant", "transfer_ownership", "member_role_changed"}:
            is_self = event.payload.get("target_user_id") == event.actor_id
            target_role = event.payload.get("new_role")

            if is_self or target_role in {"admin", "owner"}:
                sev, reasons = calculate_signal_severity(
                    signal_type="privilege_escalation_attempt",
                    is_admin_actor=True,
                )
                signals.append(
                    SecuritySignalCreate(
                        organization_id=event.organization_id,
                        workspace_id=event.workspace_id,
                        project_id=event.project_id,
                        signal_type="privilege_escalation_attempt",
                        source_type="access_control",
                        source_id=event.source_id,
                        actor_type=event.actor_type,
                        actor_id=event.actor_id,
                        resource_type="role",
                        resource_id=target_role,
                        severity=sev,
                        confidence=0.95,
                        timestamp=event.timestamp,
                        request_id=event.request_id,
                        correlation_id=event.correlation_id,
                        metadata={
                            "reasons": reasons,
                            "target_user": event.payload.get("target_user_id"),
                            "new_role": target_role,
                        },
                    )
                )
        return signals


# ---------------------------------------------------------------------------
# 12. Tenant Isolation Detector
# ---------------------------------------------------------------------------
class TenantIsolationDetector(BaseDetector):
    detector_name = "tenant_isolation_detector"

    def detect(self, event: SecurityEventNormalized) -> List[SecuritySignalCreate]:
        signals: List[SecuritySignalCreate] = []
        target_org = event.risk_metadata.get("target_organization_id")
        if target_org and str(target_org) != str(event.organization_id):
            sev, reasons = calculate_signal_severity(
                signal_type="tenant_isolation_violation",
                tenant_boundary_crossed=True,
            )
            signals.append(
                SecuritySignalCreate(
                    organization_id=event.organization_id,
                    workspace_id=event.workspace_id,
                    project_id=event.project_id,
                    signal_type="tenant_isolation_violation",
                    source_type=event.source_type,
                    source_id=event.source_id,
                    actor_type=event.actor_type,
                    actor_id=event.actor_id,
                    resource_type=event.resource_type,
                    resource_id=event.resource_id,
                    severity=sev,
                    confidence=1.0,
                    timestamp=event.timestamp,
                    request_id=event.request_id,
                    correlation_id=event.correlation_id,
                    metadata={
                        "reasons": reasons,
                        "origin_org": event.organization_id,
                        "target_org": target_org,
                    },
                )
            )
        return signals


# ---------------------------------------------------------------------------
# 13. Artifact Security Detector
# ---------------------------------------------------------------------------
class ArtifactSecurityDetector(BaseDetector):
    detector_name = "artifact_security_detector"

    DANGEROUS_EXTS = {".exe", ".bat", ".cmd", ".sh", ".ps1", ".vbs", ".dll", ".so", ".dylib"}

    def detect(self, event: SecurityEventNormalized) -> List[SecuritySignalCreate]:
        signals: List[SecuritySignalCreate] = []
        if event.source_type == "artifact":
            filename = str(event.payload.get("filename") or "").lower()
            path_traversal = ".." in filename or "/" in filename and filename.startswith("/")

            is_dangerous_ext = any(filename.endswith(ext) for ext in self.DANGEROUS_EXTS)

            if is_dangerous_ext or path_traversal:
                sev, reasons = calculate_signal_severity(
                    signal_type="malicious_artifact",
                )
                signals.append(
                    SecuritySignalCreate(
                        organization_id=event.organization_id,
                        workspace_id=event.workspace_id,
                        project_id=event.project_id,
                        signal_type="malicious_artifact",
                        source_type="artifact",
                        source_id=event.source_id,
                        actor_type=event.actor_type,
                        actor_id=event.actor_id,
                        resource_type="artifact",
                        resource_id=event.resource_id,
                        severity=sev,
                        confidence=1.0,
                        timestamp=event.timestamp,
                        request_id=event.request_id,
                        correlation_id=event.correlation_id,
                        metadata={
                            "reasons": reasons,
                            "filename": filename,
                            "path_traversal": path_traversal,
                        },
                    )
                )
        return signals


# ---------------------------------------------------------------------------
# 14. Webhook Security Detector
# ---------------------------------------------------------------------------
class WebhookSecurityDetector(BaseDetector):
    detector_name = "webhook_security_detector"

    def detect(self, event: SecurityEventNormalized) -> List[SecuritySignalCreate]:
        signals: List[SecuritySignalCreate] = []
        if event.source_type in {"webhook", "trigger"} and event.result in {"invalid_signature", "replay_detected"}:
            sev, reasons = calculate_signal_severity(
                signal_type="webhook_abuse",
            )
            signals.append(
                SecuritySignalCreate(
                    organization_id=event.organization_id,
                    workspace_id=event.workspace_id,
                    project_id=event.project_id,
                    signal_type="webhook_abuse",
                    source_type="webhook",
                    source_id=event.source_id,
                    actor_type=event.actor_type,
                    actor_id=event.actor_id,
                    resource_type="webhook_endpoint",
                    resource_id=event.resource_id,
                    severity=sev,
                    confidence=1.0,
                    timestamp=event.timestamp,
                    request_id=event.request_id,
                    correlation_id=event.correlation_id,
                    metadata={"reasons": reasons, "failure_mode": event.result},
                )
            )
        return signals


# ---------------------------------------------------------------------------
# 15. Cost Abuse Detector
# ---------------------------------------------------------------------------
class CostAbuseDetector(BaseDetector):
    detector_name = "cost_abuse_detector"

    def detect(self, event: SecurityEventNormalized) -> List[SecuritySignalCreate]:
        signals: List[SecuritySignalCreate] = []
        cost_usd = event.risk_metadata.get("cost_usd", 0.0)
        tokens = event.risk_metadata.get("total_tokens", 0)

        if cost_usd >= 50.0 or tokens >= 500000:
            sev, reasons = calculate_signal_severity(
                signal_type="cost_anomaly",
                repetition_count=int(cost_usd),
            )
            signals.append(
                SecuritySignalCreate(
                    organization_id=event.organization_id,
                    workspace_id=event.workspace_id,
                    project_id=event.project_id,
                    signal_type="cost_anomaly",
                    source_type=event.source_type,
                    source_id=event.source_id,
                    actor_type=event.actor_type,
                    actor_id=event.actor_id,
                    resource_type=event.resource_type,
                    resource_id=event.resource_id,
                    severity=sev,
                    confidence=0.9,
                    timestamp=event.timestamp,
                    request_id=event.request_id,
                    correlation_id=event.correlation_id,
                    metadata={"reasons": reasons, "cost_usd": cost_usd, "tokens": tokens},
                )
            )
        return signals


# ---------------------------------------------------------------------------
# 16. Configuration Change Detector
# ---------------------------------------------------------------------------
class ConfigurationChangeDetector(BaseDetector):
    detector_name = "configuration_change_detector"

    def detect(self, event: SecurityEventNormalized) -> List[SecuritySignalCreate]:
        signals: List[SecuritySignalCreate] = []
        if event.action in {"security_policy_updated", "detector_threshold_changed", "audit_config_modified"}:
            sev, reasons = calculate_signal_severity(
                signal_type="configuration_change",
                is_admin_actor=event.risk_metadata.get("is_admin", False),
            )
            signals.append(
                SecuritySignalCreate(
                    organization_id=event.organization_id,
                    workspace_id=event.workspace_id,
                    project_id=event.project_id,
                    signal_type="configuration_change",
                    source_type="governance",
                    source_id=event.source_id,
                    actor_type=event.actor_type,
                    actor_id=event.actor_id,
                    resource_type="policy",
                    resource_id=event.resource_id,
                    severity=sev,
                    confidence=0.95,
                    timestamp=event.timestamp,
                    request_id=event.request_id,
                    correlation_id=event.correlation_id,
                    metadata={"reasons": reasons, "changed_action": event.action},
                )
            )
        return signals


# ---------------------------------------------------------------------------
# SecurityDetectionEngine Registry
# ---------------------------------------------------------------------------
class SecurityDetectionEngine:
    """
    Central detection coordinator dispatching normalized security events to all 16 detectors.
    """
    def __init__(self):
        self.detectors: List[BaseDetector] = [
            AuthenticationDetector(),
            AuthorizationDetector(),
            RateLimitDetector(),
            SecretExposureDetector(),
            PromptInjectionDetector(),
            ToolAbuseDetector(),
            ConnectorAbuseDetector(),
            WorkflowAbuseDetector(),
            DataExportDetector(),
            DeletionDetector(),
            PrivilegeEscalationDetector(),
            TenantIsolationDetector(),
            ArtifactSecurityDetector(),
            WebhookSecurityDetector(),
            CostAbuseDetector(),
            ConfigurationChangeDetector(),
        ]

    def detect_signals(self, event: SecurityEventNormalized) -> List[SecuritySignalCreate]:
        """
        Runs all deterministic detectors over the normalized event.
        """
        emitted_signals: List[SecuritySignalCreate] = []
        for detector in self.detectors:
            try:
                res = detector.detect(event)
                if res:
                    emitted_signals.extend(res)
            except Exception:
                # Security detectors must never crash the pipeline
                continue
        return emitted_signals
