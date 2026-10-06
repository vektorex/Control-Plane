"""
Outcome Verification Service for Step 43:
AI Outcome Intelligence & Work Impact Layer.
Executes deterministic verification flows, requirement checking, and human confirmation audits.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.outcomes.errors import (
    RequirementNotMetError,
    UnauthorizedVerificationError,
    EvidenceNotFoundError,
)
from backend.app.services.outcomes.models import Outcome, OutcomeEvidence
from backend.app.services.outcomes.policies import OutcomePolicyEngine
from backend.app.services.outcomes.registry import (
    OutcomeConfidence,
    OutcomeStatus,
    EvidenceStatus,
)
from backend.app.services.outcomes.repository import OutcomeRepository


class OutcomeVerificationService:
    """
    Deterministic verification engine for outcomes.
    Ensures that an outcome is never verified without required supporting evidence and governance checks.
    """

    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session
        self.repo = OutcomeRepository(session) if session else None

    def verify_outcome_sync(
        self,
        outcome: Any,
        human_user_id: Optional[str] = None,
    ) -> Any:
        """Synchronous/in-memory verification check."""
        if isinstance(outcome, dict):
            reqs = outcome.get("requirements") or {}
            evs = outcome.get("evidence") or []
            if reqs.get("required_evidence") and not evs:
                raise RequirementNotMetError("An outcome cannot be verified without required evidence.")
            if reqs.get("required_human_confirmation") and not human_user_id:
                raise RequirementNotMetError("An outcome cannot be verified without required human confirmation.")
            outcome["status"] = OutcomeStatus.VERIFIED.value
            return outcome
        return outcome

    async def verify_outcome(
        self,
        outcome: Any,
        verified_by_user_id: Optional[str] = None,
        provided_evidence_ids: Optional[List[str]] = None,
        notes: Optional[str] = None,
        is_human_confirmation: bool = True,
        human_user_id: Optional[str] = None,
    ) -> Any:
        """
        Executes verification flow:
        Outcome -> Gather Evidence -> Validate Evidence -> Check Requirements -> Mark Verified.
        """
        user_id = verified_by_user_id or human_user_id
        if self.repo is None or isinstance(outcome, dict):
            return self.verify_outcome_sync(outcome, human_user_id=user_id)

        return await self._verify_outcome_db(
            outcome=outcome,
            verified_by_user_id=user_id,
            provided_evidence_ids=provided_evidence_ids,
            notes=notes,
            is_human_confirmation=is_human_confirmation,
        )

    async def _verify_outcome_db(
        self,
        outcome: Outcome,
        verified_by_user_id: str,
        provided_evidence_ids: Optional[List[str]] = None,
        notes: Optional[str] = None,
        is_human_confirmation: bool = True,
    ) -> Outcome:
        # 1. Gather evidence
        evidence_list = await self.repo.list_evidence_for_outcome(outcome.id)
        if provided_evidence_ids:
            # Filter or ensure provided evidence exists
            evidence_subset = [e for e in evidence_list if e.id in provided_evidence_ids]
            if not evidence_subset and provided_evidence_ids:
                raise EvidenceNotFoundError(provided_evidence_ids[0])
        else:
            evidence_subset = evidence_list

        # Must have at least one supporting evidence item
        valid_evidence = [
            e for e in evidence_subset
            if e.status in {EvidenceStatus.SUPPORTED.value, EvidenceStatus.UNREVIEWED.value}
        ]
        if not valid_evidence and not is_human_confirmation:
            raise RequirementNotMetError(
                "An outcome cannot be verified without at least one valid supporting evidence record.",
                missing_requirements=["supporting_evidence"],
            )

        # 2. Check requirements
        measurements = await self.repo.list_measurements_for_outcome(outcome.id)
        missing_reqs = OutcomePolicyEngine.verify_completion_requirements(
            requirements=outcome.requirements or {},
            evidence_list=evidence_subset,
            measurements=measurements,
            human_confirmed=is_human_confirmation,
        )

        if missing_reqs:
            raise RequirementNotMetError(
                f"Outcome '{outcome.id}' does not satisfy all verification requirements: {', '.join(missing_reqs)}",
                missing_requirements=missing_reqs,
            )

        # 3. If human confirmation is provided, mark human confirmation in evidence or add snapshot
        now = datetime.now(timezone.utc)
        outcome.status = OutcomeStatus.VERIFIED.value
        outcome.confidence = (
            OutcomeConfidence.VERIFIED.value
            if is_human_confirmation
            else OutcomeConfidence.STRONGLY_SUPPORTED.value
        )
        outcome.verified_at = now
        outcome.verified_by = verified_by_user_id
        outcome.observed_at = outcome.observed_at or now

        # Also mark evidence as supported/human-confirmed
        for ev in valid_evidence:
            if is_human_confirmation:
                ev.is_human_confirmed = True
                ev.status = EvidenceStatus.SUPPORTED.value

        await self.repo.update_outcome(outcome)
        return outcome

    async def dispute_outcome(
        self,
        outcome: Outcome,
        disputed_by_user_id: str,
        reason: str,
        evidence_ids: Optional[List[str]] = None,
    ) -> Outcome:
        """
        Disputes an outcome, reverting verification and recording the dispute reason.
        """
        now = datetime.now(timezone.utc)
        outcome.status = OutcomeStatus.DISPUTED.value
        outcome.confidence = OutcomeConfidence.DISPUTED.value
        outcome.updated_at = now

        # Add dispute evidence record
        dispute_evidence = OutcomeEvidence(
            outcome_id=outcome.id,
            source_type="User",
            source_id=disputed_by_user_id,
            evidence_type="human_confirmation",
            description=f"Outcome disputed by user {disputed_by_user_id}: {reason}",
            snapshot={"disputed_by": disputed_by_user_id, "reason": reason, "evidence_ids": evidence_ids or []},
            status=EvidenceStatus.SUPPORTED.value,
            is_human_confirmed=True,
            is_ai_generated=False,
            observed_at=now,
        )
        await self.repo.create_evidence(dispute_evidence)
        await self.repo.update_outcome(outcome)
        return outcome
