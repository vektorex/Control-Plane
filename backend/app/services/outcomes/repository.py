"""
Database repository for Step 43:
AI Outcome Intelligence & Work Impact Layer.
Ensures tenant isolation and consistent querying across all outcome models.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import desc, select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.services.outcomes.models import (
    Objective,
    OutcomeTarget,
    Outcome,
    OutcomeWorkLink,
    OutcomeEvidence,
    OutcomeMeasurement,
    OutcomeMilestone,
    WorkDecision,
    OutcomeAttribution,
    ImpactAnalysis,
    OutcomeHealthRecord,
)


class OutcomeRepository:
    """Async repository for outcome entities with tenant isolation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # =========================================================================
    # Objectives
    # =========================================================================

    async def create_objective(self, objective: Objective) -> Objective:
        self.session.add(objective)
        await self.session.flush()
        return objective

    async def get_objective(self, objective_id: str, workspace_id: Optional[str] = None) -> Optional[Objective]:
        query = select(Objective).where(Objective.id == objective_id)
        if workspace_id:
            query = query.where(Objective.workspace_id == workspace_id)
        query = query.options(
            selectinload(Objective.targets),
            selectinload(Objective.milestones),
            selectinload(Objective.outcomes),
        )
        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    async def list_objectives(
        self,
        workspace_id: str,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
        objective_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Objective]:
        query = select(Objective).where(Objective.workspace_id == workspace_id)
        if project_id:
            query = query.where(Objective.project_id == project_id)
        if status:
            query = query.where(Objective.status == status)
        if objective_type:
            query = query.where(Objective.objective_type == objective_type)
        query = (
            query.options(
                selectinload(Objective.targets),
                selectinload(Objective.milestones),
                selectinload(Objective.outcomes),
            )
            .order_by(desc(Objective.created_at))
            .offset(offset)
            .limit(limit)
        )
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def update_objective(self, objective: Objective) -> Objective:
        objective.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return objective

    async def delete_objective(self, objective: Objective) -> None:
        await self.session.delete(objective)
        await self.session.flush()

    # =========================================================================
    # Targets
    # =========================================================================

    async def create_target(self, target: OutcomeTarget) -> OutcomeTarget:
        self.session.add(target)
        await self.session.flush()
        return target

    async def get_target(self, target_id: str) -> Optional[OutcomeTarget]:
        query = select(OutcomeTarget).where(OutcomeTarget.id == target_id).options(
            selectinload(OutcomeTarget.measurements)
        )
        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    async def list_targets_for_objective(self, objective_id: str) -> List[OutcomeTarget]:
        query = (
            select(OutcomeTarget)
            .where(OutcomeTarget.objective_id == objective_id)
            .order_by(OutcomeTarget.created_at)
        )
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def update_target(self, target: OutcomeTarget) -> OutcomeTarget:
        target.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return target

    # =========================================================================
    # Milestones
    # =========================================================================

    async def create_milestone(self, milestone: OutcomeMilestone) -> OutcomeMilestone:
        self.session.add(milestone)
        await self.session.flush()
        return milestone

    async def get_milestone(self, milestone_id: str) -> Optional[OutcomeMilestone]:
        query = select(OutcomeMilestone).where(OutcomeMilestone.id == milestone_id)
        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    async def list_milestones_for_objective(self, objective_id: str) -> List[OutcomeMilestone]:
        query = (
            select(OutcomeMilestone)
            .where(OutcomeMilestone.objective_id == objective_id)
            .order_by(OutcomeMilestone.created_at)
        )
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def update_milestone(self, milestone: OutcomeMilestone) -> OutcomeMilestone:
        milestone.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return milestone

    # =========================================================================
    # Outcomes
    # =========================================================================

    async def create_outcome(self, outcome: Outcome) -> Outcome:
        self.session.add(outcome)
        await self.session.flush()
        return outcome

    async def get_outcome(self, outcome_id: str, workspace_id: Optional[str] = None) -> Optional[Outcome]:
        query = select(Outcome).where(Outcome.id == outcome_id)
        if workspace_id:
            query = query.where(Outcome.workspace_id == workspace_id)
        query = query.options(
            selectinload(Outcome.objective),
            selectinload(Outcome.evidence),
            selectinload(Outcome.work_links),
            selectinload(Outcome.measurements),
            selectinload(Outcome.attributions),
            selectinload(Outcome.impact_analyses),
        )
        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    async def list_outcomes(
        self,
        workspace_id: str,
        project_id: Optional[str] = None,
        objective_id: Optional[str] = None,
        status: Optional[str] = None,
        outcome_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Outcome]:
        query = select(Outcome).where(Outcome.workspace_id == workspace_id)
        if project_id:
            query = query.where(Outcome.project_id == project_id)
        if objective_id:
            query = query.where(Outcome.objective_id == objective_id)
        if status:
            query = query.where(Outcome.status == status)
        if outcome_type:
            query = query.where(Outcome.outcome_type == outcome_type)
        query = (
            query.options(
                selectinload(Outcome.evidence),
                selectinload(Outcome.work_links),
                selectinload(Outcome.measurements),
                selectinload(Outcome.attributions),
                selectinload(Outcome.impact_analyses),
            )
            .order_by(desc(Outcome.created_at))
            .offset(offset)
            .limit(limit)
        )
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def update_outcome(self, outcome: Outcome) -> Outcome:
        outcome.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return outcome

    async def delete_outcome(self, outcome: Outcome) -> None:
        await self.session.delete(outcome)
        await self.session.flush()

    # =========================================================================
    # Evidence & Measurements
    # =========================================================================

    async def create_evidence(self, evidence: OutcomeEvidence) -> OutcomeEvidence:
        self.session.add(evidence)
        await self.session.flush()
        return evidence

    async def get_evidence(self, evidence_id: str) -> Optional[OutcomeEvidence]:
        query = select(OutcomeEvidence).where(OutcomeEvidence.id == evidence_id)
        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    async def list_evidence_for_outcome(self, outcome_id: str) -> List[OutcomeEvidence]:
        query = (
            select(OutcomeEvidence)
            .where(OutcomeEvidence.outcome_id == outcome_id)
            .order_by(desc(OutcomeEvidence.created_at))
        )
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def create_measurement(self, measurement: OutcomeMeasurement) -> OutcomeMeasurement:
        self.session.add(measurement)
        await self.session.flush()
        return measurement

    async def list_measurements_for_outcome(self, outcome_id: str) -> List[OutcomeMeasurement]:
        query = (
            select(OutcomeMeasurement)
            .where(OutcomeMeasurement.outcome_id == outcome_id)
            .order_by(desc(OutcomeMeasurement.created_at))
        )
        res = await self.session.execute(query)
        return list(res.scalars().all())

    # =========================================================================
    # Work Links & Attributions
    # =========================================================================

    async def create_work_link(self, link: OutcomeWorkLink) -> OutcomeWorkLink:
        self.session.add(link)
        await self.session.flush()
        return link

    async def list_work_links_for_outcome(self, outcome_id: str) -> List[OutcomeWorkLink]:
        query = (
            select(OutcomeWorkLink)
            .where(OutcomeWorkLink.outcome_id == outcome_id)
            .order_by(desc(OutcomeWorkLink.created_at))
        )
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def create_attribution(self, attribution: OutcomeAttribution) -> OutcomeAttribution:
        self.session.add(attribution)
        await self.session.flush()
        return attribution

    async def list_attributions_for_outcome(self, outcome_id: str) -> List[OutcomeAttribution]:
        query = (
            select(OutcomeAttribution)
            .where(OutcomeAttribution.outcome_id == outcome_id)
            .order_by(desc(OutcomeAttribution.created_at))
        )
        res = await self.session.execute(query)
        return list(res.scalars().all())

    # =========================================================================
    # Impact Analyses
    # =========================================================================

    async def create_impact_analysis(self, impact: ImpactAnalysis) -> ImpactAnalysis:
        self.session.add(impact)
        await self.session.flush()
        return impact

    async def list_impact_for_outcome(self, outcome_id: str) -> List[ImpactAnalysis]:
        query = (
            select(ImpactAnalysis)
            .where(ImpactAnalysis.outcome_id == outcome_id)
            .order_by(desc(ImpactAnalysis.created_at))
        )
        res = await self.session.execute(query)
        return list(res.scalars().all())

    # =========================================================================
    # Decisions
    # =========================================================================

    async def create_decision(self, decision: WorkDecision) -> WorkDecision:
        self.session.add(decision)
        await self.session.flush()
        return decision

    async def get_decision(self, decision_id: str, workspace_id: Optional[str] = None) -> Optional[WorkDecision]:
        query = select(WorkDecision).where(WorkDecision.id == decision_id)
        if workspace_id:
            query = query.where(WorkDecision.workspace_id == workspace_id)
        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    async def list_decisions(
        self,
        workspace_id: str,
        project_id: Optional[str] = None,
        objective_id: Optional[str] = None,
        outcome_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[WorkDecision]:
        query = select(WorkDecision).where(WorkDecision.workspace_id == workspace_id)
        if project_id:
            query = query.where(WorkDecision.project_id == project_id)
        if objective_id:
            query = query.where(WorkDecision.objective_id == objective_id)
        if outcome_id:
            query = query.where(WorkDecision.outcome_id == outcome_id)
        if status:
            query = query.where(WorkDecision.status == status)
        query = query.order_by(desc(WorkDecision.created_at)).offset(offset).limit(limit)
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def update_decision(self, decision: WorkDecision) -> WorkDecision:
        decision.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return decision
