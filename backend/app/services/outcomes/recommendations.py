"""
Outcome Recommendations and Task Proposal Engine for Step 43:
AI Outcome Intelligence & Work Impact Layer.
Generates advisory, non-privileged next actions and task proposals.
"""
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.outcomes.models import (
    Objective,
    Outcome,
    OutcomeMilestone,
    OutcomeEvidence,
    WorkDecision,
)
from backend.app.services.outcomes.registry import (
    MilestoneStatus,
    OutcomeStatus,
    WorkDecisionStatus,
)
from backend.app.services.outcomes.repository import OutcomeRepository
from backend.app.services.outcomes.schemas import OutcomeRecommendationResponse


class OutcomeRecommendationService:
    """
    Generates governed recommendations based on outcome health, evidence gaps, and blocked milestones.
    Never executes privileged actions directly; all recommendations require human or policy approval.
    """

    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session
        self.repo = OutcomeRepository(session) if session else None

    @classmethod
    def generate_recommendations(cls, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Advisory next-action proposals; never privileged execution."""
        recs: List[Dict[str, Any]] = []
        if context.get("missing_evidence"):
            recs.append({
                "action": "collect_missing_evidence",
                "reason": f"Missing evidence items: {context.get('missing_evidence')}",
                "is_privileged_execution": False,
            })
        if not context.get("has_human_review"):
            recs.append({
                "action": "request_human_review",
                "reason": "Human confirmation required to verify deliverable.",
                "is_privileged_execution": False,
            })
        return recs

    async def get_recommendations_for_outcome(
        self,
        outcome: Outcome,
        workspace_id: str,
    ) -> List[OutcomeRecommendationResponse]:
        recommendations: List[OutcomeRecommendationResponse] = []
        evidence_list = await self.repo.list_evidence_for_outcome(outcome.id)

        # 1. Check if outcome is observed but unverified and has evidence
        if outcome.status == OutcomeStatus.OBSERVED.value and outcome.status != OutcomeStatus.VERIFIED.value:
            recommendations.append(OutcomeRecommendationResponse(
                recommendation_id=str(uuid.uuid4()),
                outcome_id=outcome.id,
                action_type="request_human_review",
                title="Request Human Verification",
                reason=f"Outcome '{outcome.name}' has been observed and evidence collected. A human confirmation is recommended to mark it verified.",
                evidence_ids=[e.id for e in evidence_list[:5]],
                requires_approval=True,
            ))

        # 2. Check missing evidence requirements
        reqs = outcome.requirements or {}
        req_types = reqs.get("required_evidence_types") or reqs.get("required_evidence", [])
        if req_types:
            present_types = {e.evidence_type for e in evidence_list}
            missing = [rt for rt in req_types if rt not in present_types]
            for m in missing:
                recommendations.append(OutcomeRecommendationResponse(
                    recommendation_id=str(uuid.uuid4()),
                    outcome_id=outcome.id,
                    action_type="collect_missing_evidence",
                    title=f"Collect Required Evidence: {m}",
                    reason=f"Outcome requires evidence of type '{m}' before it can be verified.",
                    suggested_task={
                        "title": f"Gather {m} for outcome '{outcome.name}'",
                        "reason": f"Required evidence type '{m}' is missing.",
                        "required_capability": "retrieval_or_execution",
                    },
                    requires_approval=True,
                ))

        # 3. Check if disputed
        if outcome.status == OutcomeStatus.DISPUTED.value:
            recommendations.append(OutcomeRecommendationResponse(
                recommendation_id=str(uuid.uuid4()),
                outcome_id=outcome.id,
                action_type="resolve_blocker",
                title="Resolve Outcome Dispute",
                reason=f"Outcome '{outcome.name}' has been disputed. Review stakeholder findings and provide rebuttal evidence or revise deliverables.",
                requires_approval=True,
            ))

        return recommendations

    async def get_recommendations_for_objective(
        self,
        objective: Objective,
        workspace_id: str,
    ) -> List[OutcomeRecommendationResponse]:
        recommendations: List[OutcomeRecommendationResponse] = []

        # 1. Check blocked milestones
        milestones = await self.repo.list_milestones_for_objective(objective.id)
        for m in milestones:
            if m.status == MilestoneStatus.BLOCKED.value:
                recommendations.append(OutcomeRecommendationResponse(
                    recommendation_id=str(uuid.uuid4()),
                    objective_id=objective.id,
                    action_type="resolve_blocker",
                    title=f"Resolve Blocked Milestone: {m.name}",
                    reason=f"Milestone '{m.name}' is currently blocked, delaying progress toward objective '{objective.name}'.",
                    suggested_task={
                        "title": f"Investigate blocker for milestone '{m.name}'",
                        "reason": "Milestone is blocked in objective plan.",
                    },
                    requires_approval=True,
                ))

        # 2. Check pending decisions
        decisions = await self.repo.list_decisions(
            workspace_id=workspace_id,
            objective_id=objective.id,
            status=WorkDecisionStatus.PROPOSED.value,
        )
        for dec in decisions:
            recommendations.append(OutcomeRecommendationResponse(
                recommendation_id=str(uuid.uuid4()),
                objective_id=objective.id,
                action_type="review_decision",
                title=f"Review Proposed Decision: {dec.title}",
                reason=f"Decision '{dec.title}' by {dec.decision_owner} is awaiting human or policy review.",
                requires_approval=True,
            ))

        return recommendations
