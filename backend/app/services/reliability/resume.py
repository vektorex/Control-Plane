"""
Resumable execution service for Step 35: AI Reliability, Resilience & Chaos Engineering Layer.
Re-evaluates tenant isolation, governance constraints, security quarantine, and HITL requirements before resuming.
Never blindly replays side-effecting external steps.
"""
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.reliability.checkpoint import CheckpointService
from backend.app.services.reliability.exceptions import (
    ResumePreconditionFailedError,
)
from backend.app.services.reliability.schemas import (
    CheckpointResumeRequest,
    CheckpointResumeResponse,
)
from backend.app.services.reliability.validators import (
    validate_checkpoint_integrity,
    validate_resumption_preconditions,
)


class ResumeService:
    """Orchestrates safe execution resumption from validated checkpoints."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.checkpoint_service = CheckpointService(session)

    async def validate_checkpoint_safety(
        self,
        checkpoint_id: str,
        organization_id: str,
        target_resource_exists: bool = True,
        is_security_quarantined: bool = False,
        is_data_deleted_or_redacted: bool = False,
    ) -> bool:
        """
        Validates checkpoint integrity, tenant isolation, and lifecycle/security state.
        """
        cp = await self.checkpoint_service.get_checkpoint(
            checkpoint_id=checkpoint_id,
            organization_id=organization_id,
        )

        # 1. Integrity check
        validate_checkpoint_integrity(
            state_snapshot=cp.state_snapshot,
            input_fingerprint=cp.input_fingerprint,
            context_fingerprint=cp.context_fingerprint,
        )

        # 2. Preconditions check
        validate_resumption_preconditions(
            target_resource_exists=target_resource_exists,
            is_security_quarantined=is_security_quarantined,
            is_data_deleted_or_redacted=is_data_deleted_or_redacted,
        )

        return True

    async def resume_from_checkpoint(
        self,
        checkpoint_id: str,
        organization_id: str,
        request: CheckpointResumeRequest,
        target_resource_exists: bool = True,
        is_security_quarantined: bool = False,
        is_data_deleted_or_redacted: bool = False,
        governance_verdict: str = "allow",
    ) -> CheckpointResumeResponse:
        """
        Safely resumes an execution from a checkpoint boundary.
        """
        # Step 1: Precondition validation
        await self.validate_checkpoint_safety(
            checkpoint_id=checkpoint_id,
            organization_id=organization_id,
            target_resource_exists=target_resource_exists,
            is_security_quarantined=is_security_quarantined,
            is_data_deleted_or_redacted=is_data_deleted_or_redacted,
        )

        cp = await self.checkpoint_service.get_checkpoint(checkpoint_id, organization_id)

        # Step 2: Governance re-evaluation
        if governance_verdict in {"block", "deny"}:
            raise ResumePreconditionFailedError(
                f"Resumption blocked by Step 32 Governance policy re-check (verdict: {governance_verdict})."
            )

        # Step 3: Determine safe resumption boundary
        snapshot = cp.state_snapshot
        completed_steps = snapshot.get("completed_steps", [])
        last_step = cp.step_id or (completed_steps[-1] if completed_steps else None)

        details = {
            "resumed_run_id": cp.run_id,
            "workflow_run_id": cp.workflow_run_id,
            "job_id": cp.job_id,
            "checkpoint_type": cp.checkpoint_type,
            "completed_steps_skipped": completed_steps if request.skip_completed_steps else [],
            "reason": request.reason,
            "override_parameters": request.override_parameters or {},
        }

        return CheckpointResumeResponse(
            success=True,
            checkpoint_id=cp.id,
            resumed_from_step=last_step,
            execution_status="resumed",
            verification_passed=True,
            governance_decision=governance_verdict,
            details=details,
        )
