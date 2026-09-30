"""
Creation and context sanitization for Human Intervention Requests (Step 18).
"""
import copy
from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.hitl import HumanAction, HumanInterventionRequest
from backend.app.services.hitl.notifications import NotificationService
from backend.app.services.hitl.policies import ApprovalPolicyEngine
from backend.app.services.hitl.schemas import (
    InterventionCreateRequest,
    InterventionPriority,
    InterventionStatus,
    InterventionType,
    RiskAssessment,
)
from backend.app.services.memory.sanitizer import SecretDetector

logger = logging.getLogger(__name__)


class InterventionRequestManager:
    """
    Manages safe context construction and lifecycle instantiation of intervention requests.
    """

    @classmethod
    def sanitize_payload(cls, data: Any) -> Any:
        """
        Recursively strips passwords, API keys, credentials, and bearer tokens.
        """
        if isinstance(data, dict):
            clean = {}
            for k, v in data.items():
                k_lower = str(k).lower()
                if any(sec in k_lower for sec in ["secret", "password", "token", "auth", "credential", "private_key", "api_key"]):
                    clean[k] = "[REDACTED_CREDENTIAL]"
                elif isinstance(v, (dict, list)):
                    clean[k] = cls.sanitize_payload(v)
                elif isinstance(v, str):
                    secrets = SecretDetector.detect_secrets(v)
                    if secrets:
                        clean[k] = f"[REDACTED_SECRET_{secrets[0].upper()}]"
                    else:
                        clean[k] = v
                else:
                    clean[k] = v
            return clean
        elif isinstance(data, list):
            return [cls.sanitize_payload(item) for item in data]
        elif isinstance(data, str):
            secrets = SecretDetector.detect_secrets(data)
            if secrets:
                return f"[REDACTED_SECRET_{secrets[0].upper()}]"
            return data
        return data

    @classmethod
    def build_safe_context(
        cls,
        target_system: str,
        operation: str,
        input_payload: Dict[str, Any],
        risk: RiskAssessment,
        workflow_name: Optional[str] = None,
        step_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Builds user-safe, explanatory context for the approval UI without hidden reasoning or secrets.
        """
        sanitized_input = cls.sanitize_payload(copy.deepcopy(input_payload))

        # Extract high-level preview fields (e.g. repository, query, issue title)
        preview_fields = {}
        for key in ["repository", "repo", "query", "title", "issue_number", "pull_number", "path", "branch", "url"]:
            if key in sanitized_input:
                preview_fields[key] = sanitized_input[key]

        return {
            "target_system": target_system,
            "operation": operation,
            "workflow_name": workflow_name,
            "step_name": step_name,
            "risk_level": risk.level.value,
            "is_destructive": risk.is_destructive,
            "risk_reasons": risk.reasons,
            "preview_fields": preview_fields,
            "sanitized_input": sanitized_input,
            "approval_meaning": (
                f"Approving will authorize the platform to execute '{operation}' against '{target_system}' "
                f"with the specified inputs."
            ),
        }

    @classmethod
    async def create_request(
        cls,
        session: AsyncSession,
        workspace_id: UUID,
        request: InterventionCreateRequest,
        requested_by: Optional[UUID] = None,
    ) -> HumanInterventionRequest:
        """
        Persists a HumanInterventionRequest with safe context, expiration, and audit logging.
        """
        now = datetime.now(timezone.utc)
        timeout = request.timeout_seconds or 3600
        expires_at = now + timedelta(seconds=timeout)

        # Sanitize input snapshot and context
        clean_snapshot = cls.sanitize_payload(copy.deepcopy(request.input_snapshot))
        clean_context = cls.sanitize_payload(copy.deepcopy(request.safe_context))

        intervention = HumanInterventionRequest(
            workspace_id=workspace_id,
            project_id=request.project_id,
            workflow_id=request.workflow_id,
            workflow_run_id=request.workflow_run_id,
            run_id=request.run_id,
            step_id=request.step_id,
            requested_by=requested_by,
            assigned_to=request.assigned_to,
            intervention_type=request.intervention_type.value,
            title=request.title,
            description=request.description,
            status=InterventionStatus.PENDING.value,
            priority=request.priority.value,
            requested_action=request.requested_action,
            input_snapshot=clean_snapshot,
            safe_context=clean_context,
            available_actions=request.available_actions,
            created_at=now,
            expires_at=expires_at,
        )
        session.add(intervention)
        await session.flush()

        # Audit action
        audit = HumanAction(
            workspace_id=workspace_id,
            intervention_id=intervention.id,
            user_id=requested_by or intervention.assigned_to or workspace_id,
            action_type="request_created",
            target_type="intervention",
            target_id=str(intervention.id),
            metadata_json={
                "requested_action": intervention.requested_action,
                "priority": intervention.priority,
                "workflow_run_id": str(intervention.workflow_run_id) if intervention.workflow_run_id else None,
            },
            created_at=now,
        )
        session.add(audit)

        # Dispatch In-App Notification
        await NotificationService.notify_approval_required(session, intervention)

        logger.info(
            f"[InterventionManager] Created intervention '{intervention.id}' "
            f"(action={intervention.requested_action}, priority={intervention.priority}, expires_in={timeout}s)"
        )
        return intervention
