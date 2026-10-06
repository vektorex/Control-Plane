"""
Primary Outcome Service for Step 43:
AI Outcome Intelligence & Work Impact Layer.
Unified orchestration for Objectives, Targets, Milestones, Outcomes, Evidence, Measurements, Decisions, Impact, and Graph.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.events.constants import SystemEventType
from backend.app.services.outcomes.errors import (
    ObjectiveNotFoundError,
    OutcomeNotFoundError,
    OutcomeTargetNotFoundError,
    MilestoneNotFoundError,
    WorkDecisionNotFoundError,
    EvidenceNotFoundError,
    OutcomeTenantViolationError,
)
from backend.app.services.outcomes.events import OutcomeEventPublisher
from backend.app.services.outcomes.graph import OutcomeGraphService
from backend.app.services.outcomes.health import HealthEvaluator
from backend.app.services.outcomes.impact import ImpactCalculator
from backend.app.services.outcomes.lifecycle import OutcomeLifecycle
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
)
from backend.app.services.outcomes.policies import OutcomePolicyEngine
from backend.app.services.outcomes.recommendations import OutcomeRecommendationService
from backend.app.services.outcomes.registry import (
    EvidenceStatus,
    MilestoneStatus,
    OutcomeConfidence,
    OutcomeHealthStatus,
    OutcomeStatus,
    WorkDecisionStatus,
    WorkDecisionType,
)
from backend.app.services.outcomes.repository import OutcomeRepository
from backend.app.services.outcomes.schemas import (
    ObjectiveCreate,
    ObjectiveUpdate,
    OutcomeTargetCreate,
    OutcomeTargetUpdate,
    OutcomeMilestoneCreate,
    OutcomeMilestoneUpdate,
    OutcomeCreate,
    OutcomeUpdate,
    OutcomeEvidenceCreate,
    OutcomeMeasurementCreate,
    OutcomeWorkLinkCreate,
    WorkDecisionCreate,
    WorkDecisionUpdate,
    OutcomeAttributionCreate,
    ImpactAnalysisCreate,
    OutcomeVerifyRequest,
    OutcomeDisputeRequest,
    OutcomeHealthResponse,
    OutcomeWorkMapResponse,
    OutcomeRecommendationResponse,
)
from backend.app.services.outcomes.validators import OutcomeValidator
from backend.app.services.outcomes.verification import OutcomeVerificationService


class OutcomeService:
    """
    Unified domain service for Outcome Intelligence.
    Preserves strict tenant boundaries and policy governance.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = OutcomeRepository(session)
        self.events = OutcomeEventPublisher(session)
        self.graph = OutcomeGraphService(session)
        self.verification = OutcomeVerificationService(session)
        self.recommendations = OutcomeRecommendationService(session)

    # =========================================================================
    # Objectives
    # =========================================================================

    async def create_objective(self, workspace_id: str, created_by: str, data: ObjectiveCreate) -> Objective:
        OutcomeValidator.validate_objective_type(data.objective_type)
        OutcomePolicyEngine.validate_no_subjective_scores(data.requirements)

        obj = Objective(
            workspace_id=workspace_id,
            project_id=data.project_id,
            name=data.name,
            description=data.description,
            objective_type=data.objective_type,
            status="draft",
            priority=data.priority,
            owner_user_id=data.owner_user_id,
            created_by=created_by,
            requirements=data.requirements or {},
            start_at=data.start_at,
            target_at=data.target_at,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        created = await self.repo.create_objective(obj)
        await self.events.emit_objective_event(
            event_type="objective.created",
            workspace_id=workspace_id,
            objective_id=created.id,
            payload={"name": created.name, "type": created.objective_type},
            project_id=created.project_id,
            actor_id=created_by,
        )
        return created

    async def get_objective(self, objective_id: str, workspace_id: str) -> Objective:
        obj = await self.repo.get_objective(objective_id, workspace_id)
        if not obj:
            raise ObjectiveNotFoundError(objective_id)
        OutcomePolicyEngine.enforce_tenant_isolation(obj.workspace_id, workspace_id)
        return obj

    async def list_objectives(
        self,
        workspace_id: str,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
        objective_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Objective]:
        return await self.repo.list_objectives(
            workspace_id=workspace_id,
            project_id=project_id,
            status=status,
            objective_type=objective_type,
            limit=limit,
            offset=offset,
        )

    async def update_objective(self, objective_id: str, workspace_id: str, data: ObjectiveUpdate) -> Objective:
        obj = await self.get_objective(objective_id, workspace_id)

        if data.status and data.status != obj.status:
            OutcomeLifecycle.validate_objective_transition(obj.status, data.status)
            obj.status = data.status
            if data.status == "completed":
                obj.completed_at = datetime.now(timezone.utc)

        if data.name is not None:
            obj.name = data.name
        if data.description is not None:
            obj.description = data.description
        if data.objective_type is not None:
            OutcomeValidator.validate_objective_type(data.objective_type)
            obj.objective_type = data.objective_type
        if data.priority is not None:
            obj.priority = data.priority
        if data.owner_user_id is not None:
            obj.owner_user_id = data.owner_user_id
        if data.requirements is not None:
            OutcomePolicyEngine.validate_no_subjective_scores(data.requirements)
            obj.requirements = data.requirements
        if data.start_at is not None:
            obj.start_at = data.start_at
        if data.target_at is not None:
            obj.target_at = data.target_at
        if data.completed_at is not None:
            obj.completed_at = data.completed_at

        updated = await self.repo.update_objective(obj)
        await self.events.emit_objective_event(
            event_type="objective.updated",
            workspace_id=workspace_id,
            objective_id=updated.id,
            payload={"name": updated.name, "status": updated.status},
            project_id=updated.project_id,
        )
        return updated

    async def delete_objective(self, objective_id: str, workspace_id: str) -> None:
        obj = await self.get_objective(objective_id, workspace_id)
        await self.repo.delete_objective(obj)

    async def get_objective_health(self, objective_id: str, workspace_id: str) -> OutcomeHealthResponse:
        obj = await self.get_objective(objective_id, workspace_id)
        milestones = await self.repo.list_milestones_for_objective(objective_id)
        targets = await self.repo.list_targets_for_objective(objective_id)
        outcomes = await self.repo.list_outcomes(workspace_id=workspace_id, objective_id=objective_id)

        eval_res = HealthEvaluator.evaluate_objective_health(obj, milestones, targets, outcomes)
        return OutcomeHealthResponse(
            status=eval_res["status"],
            is_healthy=eval_res["is_healthy"],
            reasons=eval_res["reasons"],
            checked_at=eval_res["checked_at"],
            details=eval_res.get("details", {}),
        )

    async def get_objective_work_map(self, objective_id: str, workspace_id: str) -> OutcomeWorkMapResponse:
        await self.get_objective(objective_id, workspace_id)
        return await self.graph.get_objective_work_map(objective_id, workspace_id)

    async def get_objective_recommendations(self, objective_id: str, workspace_id: str) -> List[OutcomeRecommendationResponse]:
        obj = await self.get_objective(objective_id, workspace_id)
        return await self.recommendations.get_recommendations_for_objective(obj, workspace_id)

    # =========================================================================
    # Targets
    # =========================================================================

    async def create_target(self, objective_id: str, workspace_id: str, data: OutcomeTargetCreate) -> OutcomeTarget:
        obj = await self.get_objective(objective_id, workspace_id)
        OutcomeValidator.validate_metric_type(data.metric_type)
        OutcomeValidator.validate_measurement_source(data.measurement_source)

        target = OutcomeTarget(
            objective_id=obj.id,
            name=data.name,
            description=data.description,
            metric_type=data.metric_type,
            target_value=data.target_value,
            target_unit=data.target_unit,
            baseline_value=data.baseline_value,
            current_value=data.baseline_value,
            target_date=data.target_date,
            measurement_source=data.measurement_source,
            status="planned",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        return await self.repo.create_target(target)

    async def get_target(self, target_id: str, workspace_id: str) -> OutcomeTarget:
        target = await self.repo.get_target(target_id)
        if not target:
            raise OutcomeTargetNotFoundError(target_id)
        # Check parent objective workspace
        await self.get_objective(target.objective_id, workspace_id)
        return target

    async def list_targets(self, objective_id: str, workspace_id: str) -> List[OutcomeTarget]:
        await self.get_objective(objective_id, workspace_id)
        return await self.repo.list_targets_for_objective(objective_id)

    async def update_target(self, target_id: str, workspace_id: str, data: OutcomeTargetUpdate) -> OutcomeTarget:
        target = await self.get_target(target_id, workspace_id)
        if data.name is not None:
            target.name = data.name
        if data.description is not None:
            target.description = data.description
        if data.target_value is not None:
            target.target_value = data.target_value
        if data.target_unit is not None:
            target.target_unit = data.target_unit
        if data.baseline_value is not None:
            target.baseline_value = data.baseline_value
        if data.current_value is not None:
            target.current_value = data.current_value
        if data.target_date is not None:
            target.target_date = data.target_date
        if data.measurement_source is not None:
            OutcomeValidator.validate_measurement_source(data.measurement_source)
            target.measurement_source = data.measurement_source
        if data.status is not None:
            target.status = data.status

        return await self.repo.update_target(target)

    # =========================================================================
    # Milestones
    # =========================================================================

    async def create_milestone(self, objective_id: str, workspace_id: str, data: OutcomeMilestoneCreate) -> OutcomeMilestone:
        obj = await self.get_objective(objective_id, workspace_id)

        milestone = OutcomeMilestone(
            objective_id=obj.id,
            name=data.name,
            description=data.description,
            status=MilestoneStatus.PLANNED.value,
            due_at=data.due_at,
            owner_user_id=data.owner_user_id,
            connected_resource_type=data.connected_resource_type,
            connected_resource_id=data.connected_resource_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        created = await self.repo.create_milestone(milestone)
        await self.events.emit_objective_event(
            event_type="milestone.created",
            workspace_id=workspace_id,
            objective_id=obj.id,
            payload={"milestone_id": created.id, "name": created.name},
        )
        return created

    async def list_milestones(self, objective_id: str, workspace_id: str) -> List[OutcomeMilestone]:
        await self.get_objective(objective_id, workspace_id)
        return await self.repo.list_milestones_for_objective(objective_id)

    async def update_milestone(self, milestone_id: str, workspace_id: str, data: OutcomeMilestoneUpdate) -> OutcomeMilestone:
        milestone = await self.repo.get_milestone(milestone_id)
        if not milestone:
            raise MilestoneNotFoundError(milestone_id)
        await self.get_objective(milestone.objective_id, workspace_id)

        if data.status and data.status != milestone.status:
            OutcomeLifecycle.validate_milestone_transition(milestone.status, data.status)
            milestone.status = data.status
            if data.status == MilestoneStatus.COMPLETED.value:
                milestone.completed_at = datetime.now(timezone.utc)
                await self.events.emit_objective_event(
                    event_type="milestone.completed",
                    workspace_id=workspace_id,
                    objective_id=milestone.objective_id,
                    payload={"milestone_id": milestone.id, "name": milestone.name},
                )
            elif data.status == MilestoneStatus.BLOCKED.value:
                await self.events.emit_objective_event(
                    event_type="milestone.blocked",
                    workspace_id=workspace_id,
                    objective_id=milestone.objective_id,
                    payload={"milestone_id": milestone.id, "name": milestone.name},
                )

        if data.name is not None:
            milestone.name = data.name
        if data.description is not None:
            milestone.description = data.description
        if data.due_at is not None:
            milestone.due_at = data.due_at
        if data.completed_at is not None:
            milestone.completed_at = data.completed_at
        if data.owner_user_id is not None:
            milestone.owner_user_id = data.owner_user_id
        if data.connected_resource_type is not None:
            milestone.connected_resource_type = data.connected_resource_type
        if data.connected_resource_id is not None:
            milestone.connected_resource_id = data.connected_resource_id

        return await self.repo.update_milestone(milestone)

    # =========================================================================
    # Outcomes
    # =========================================================================

    async def create_outcome(self, workspace_id: str, created_by: str, data: OutcomeCreate) -> Outcome:
        OutcomeValidator.validate_outcome_type(data.outcome_type)
        OutcomePolicyEngine.validate_no_subjective_scores(data.requirements)

        if data.objective_id:
            await self.get_objective(data.objective_id, workspace_id)

        outcome = Outcome(
            workspace_id=workspace_id,
            project_id=data.project_id,
            objective_id=data.objective_id,
            name=data.name,
            description=data.description,
            outcome_type=data.outcome_type,
            status=OutcomeStatus.PLANNED.value,
            confidence=OutcomeConfidence.UNVERIFIED.value,
            owner_user_id=data.owner_user_id,
            created_by=created_by,
            requirements=data.requirements or {},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        created = await self.repo.create_outcome(outcome)
        await self.events.emit_outcome_event(
            event_type="outcome.created",
            workspace_id=workspace_id,
            outcome_id=created.id,
            payload={"name": created.name, "type": created.outcome_type},
            project_id=created.project_id,
            actor_id=created_by,
        )
        return created

    async def get_outcome(self, outcome_id: str, workspace_id: str) -> Outcome:
        outcome = await self.repo.get_outcome(outcome_id, workspace_id)
        if not outcome:
            raise OutcomeNotFoundError(outcome_id)
        OutcomePolicyEngine.enforce_tenant_isolation(outcome.workspace_id, workspace_id)
        return outcome

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
        return await self.repo.list_outcomes(
            workspace_id=workspace_id,
            project_id=project_id,
            objective_id=objective_id,
            status=status,
            outcome_type=outcome_type,
            limit=limit,
            offset=offset,
        )

    async def update_outcome(self, outcome_id: str, workspace_id: str, data: OutcomeUpdate) -> Outcome:
        outcome = await self.get_outcome(outcome_id, workspace_id)

        if data.status and data.status != outcome.status:
            OutcomeLifecycle.validate_outcome_transition(outcome.status, data.status)
            outcome.status = data.status
            if data.status == OutcomeStatus.OBSERVED.value:
                outcome.observed_at = datetime.now(timezone.utc)
                await self.events.emit_outcome_event(
                    event_type="outcome.observed",
                    workspace_id=workspace_id,
                    outcome_id=outcome.id,
                    payload={"status": outcome.status},
                )

        if data.name is not None:
            outcome.name = data.name
        if data.description is not None:
            outcome.description = data.description
        if data.outcome_type is not None:
            OutcomeValidator.validate_outcome_type(data.outcome_type)
            outcome.outcome_type = data.outcome_type
        if data.owner_user_id is not None:
            outcome.owner_user_id = data.owner_user_id
        if data.requirements is not None:
            OutcomePolicyEngine.validate_no_subjective_scores(data.requirements)
            outcome.requirements = data.requirements

        updated = await self.repo.update_outcome(outcome)
        await self.events.emit_outcome_event(
            event_type="outcome.updated",
            workspace_id=workspace_id,
            outcome_id=updated.id,
            payload={"name": updated.name, "status": updated.status},
            project_id=updated.project_id,
        )
        return updated

    async def delete_outcome(self, outcome_id: str, workspace_id: str) -> None:
        outcome = await self.get_outcome(outcome_id, workspace_id)
        await self.repo.delete_outcome(outcome)

    # =========================================================================
    # Evidence & Measurements
    # =========================================================================

    async def add_evidence(self, outcome_id: str, workspace_id: str, data: OutcomeEvidenceCreate) -> OutcomeEvidence:
        outcome = await self.get_outcome(outcome_id, workspace_id)
        OutcomeValidator.validate_evidence_type(data.evidence_type)
        OutcomePolicyEngine.validate_no_subjective_scores(data.snapshot)

        evidence = OutcomeEvidence(
            outcome_id=outcome.id,
            source_type=data.source_type,
            source_id=data.source_id,
            evidence_type=data.evidence_type,
            description=data.description,
            snapshot=data.snapshot or {},
            status=EvidenceStatus.UNREVIEWED.value,
            is_human_confirmed=data.is_human_confirmed,
            is_ai_generated=data.is_ai_generated,
            observed_at=data.observed_at or datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
        )
        created = await self.repo.create_evidence(evidence)

        # Update outcome status to observed if it was planned
        if outcome.status == OutcomeStatus.PLANNED.value:
            outcome.status = OutcomeStatus.IN_PROGRESS.value
            await self.repo.update_outcome(outcome)

        await self.events.emit_outcome_event(
            event_type="outcome.evidence_added",
            workspace_id=workspace_id,
            outcome_id=outcome.id,
            payload={"evidence_id": created.id, "type": created.evidence_type},
        )
        return created

    async def list_evidence(self, outcome_id: str, workspace_id: str) -> List[OutcomeEvidence]:
        await self.get_outcome(outcome_id, workspace_id)
        return await self.repo.list_evidence_for_outcome(outcome_id)

    async def add_measurement(self, outcome_id: str, workspace_id: str, data: OutcomeMeasurementCreate) -> OutcomeMeasurement:
        outcome = await self.get_outcome(outcome_id, workspace_id)
        OutcomeValidator.validate_measurement_source(data.measurement_source)

        measurement = OutcomeMeasurement(
            outcome_id=outcome.id,
            target_id=data.target_id,
            metric_name=data.metric_name,
            value=data.value,
            unit=data.unit,
            measurement_source=data.measurement_source,
            observed_at=data.observed_at or datetime.now(timezone.utc),
            evidence_id=data.evidence_id,
            created_at=datetime.now(timezone.utc),
        )
        created = await self.repo.create_measurement(measurement)

        # If connected to a target, update current_value
        if data.target_id:
            target = await self.repo.get_target(data.target_id)
            if target:
                target.current_value = data.value
                if target.target_value is not None:
                    target.status = "achieved" if target.current_value >= target.target_value else "on_track"
                await self.repo.update_target(target)

        await self.events.emit_outcome_event(
            event_type="outcome.measurement_added",
            workspace_id=workspace_id,
            outcome_id=outcome.id,
            payload={"metric_name": created.metric_name, "value": created.value, "unit": created.unit},
        )
        return created

    async def list_measurements(self, outcome_id: str, workspace_id: str) -> List[OutcomeMeasurement]:
        await self.get_outcome(outcome_id, workspace_id)
        return await self.repo.list_measurements_for_outcome(outcome_id)

    # =========================================================================
    # Work Links & Attributions
    # =========================================================================

    async def add_work_link(self, outcome_id: str, workspace_id: str, data: OutcomeWorkLinkCreate) -> OutcomeWorkLink:
        outcome = await self.get_outcome(outcome_id, workspace_id)
        OutcomeValidator.validate_work_link_resource_type(data.resource_type)

        link = OutcomeWorkLink(
            outcome_id=outcome.id,
            resource_type=data.resource_type,
            resource_id=data.resource_id,
            relationship_type=data.relationship_type,
            evidence_ids=data.evidence_ids or [],
            created_at=datetime.now(timezone.utc),
        )
        return await self.repo.create_work_link(link)

    async def list_work_links(self, outcome_id: str, workspace_id: str) -> List[OutcomeWorkLink]:
        await self.get_outcome(outcome_id, workspace_id)
        return await self.repo.list_work_links_for_outcome(outcome_id)

    async def add_attribution(self, outcome_id: str, workspace_id: str, data: OutcomeAttributionCreate) -> OutcomeAttribution:
        outcome = await self.get_outcome(outcome_id, workspace_id)
        OutcomePolicyEngine.validate_attribution_safety(
            attribution_type=data.attribution_type,
            attribution_source=data.attribution_source,
            has_causal_evidence=bool(data.evidence_ids and data.attribution_source != "AI_GENERATED_ATTRIBUTION"),
            explanation=data.explanation,
        )

        attribution = OutcomeAttribution(
            outcome_id=outcome.id,
            resource_type=data.resource_type,
            resource_id=data.resource_id,
            attribution_type=data.attribution_type,
            evidence_ids=data.evidence_ids or [],
            explanation=data.explanation,
            attribution_source=data.attribution_source,
            attribution_confidence=data.attribution_confidence,
            created_at=datetime.now(timezone.utc),
        )
        created = await self.repo.create_attribution(attribution)
        await self.events.emit_outcome_event(
            event_type="outcome.attribution_created",
            workspace_id=workspace_id,
            outcome_id=outcome.id,
            payload={"resource_type": created.resource_type, "attribution_type": created.attribution_type},
        )
        return created

    async def list_attributions(self, outcome_id: str, workspace_id: str) -> List[OutcomeAttribution]:
        await self.get_outcome(outcome_id, workspace_id)
        return await self.repo.list_attributions_for_outcome(outcome_id)

    # =========================================================================
    # Impact Analyses
    # =========================================================================

    async def add_impact_analysis(self, outcome_id: str, workspace_id: str, data: ImpactAnalysisCreate) -> ImpactAnalysis:
        outcome = await self.get_outcome(outcome_id, workspace_id)
        OutcomePolicyEngine.validate_no_subjective_scores({"summary": data.summary})

        impact = ImpactAnalysis(
            outcome_id=outcome.id,
            analysis_type=data.analysis_type,
            summary=data.summary,
            evidence_ids=data.evidence_ids or [],
            observations=data.observations or [],
            limitations=data.limitations,
            attribution_confidence=data.attribution_confidence,
            baseline_value=data.baseline_value,
            observed_value=data.observed_value,
            difference_value=data.difference_value,
            unit=data.unit,
            created_at=datetime.now(timezone.utc),
        )
        return await self.repo.create_impact_analysis(impact)

    async def list_impact_analyses(self, outcome_id: str, workspace_id: str) -> List[ImpactAnalysis]:
        await self.get_outcome(outcome_id, workspace_id)
        return await self.repo.list_impact_for_outcome(outcome_id)

    # =========================================================================
    # Verification & Dispute
    # =========================================================================

    async def verify_outcome(
        self,
        outcome_id: str,
        workspace_id: str,
        user_id: str,
        data: OutcomeVerifyRequest,
    ) -> Outcome:
        outcome = await self.get_outcome(outcome_id, workspace_id)
        verified = await self.verification.verify_outcome(
            outcome=outcome,
            verified_by_user_id=user_id,
            provided_evidence_ids=data.evidence_ids,
            notes=data.notes,
            is_human_confirmation=data.human_confirmed,
        )
        await self.events.emit_outcome_event(
            event_type="outcome.verified",
            workspace_id=workspace_id,
            outcome_id=verified.id,
            payload={"verified_by": user_id, "confidence": verified.confidence},
            actor_id=user_id,
        )
        return verified

    async def dispute_outcome(
        self,
        outcome_id: str,
        workspace_id: str,
        user_id: str,
        data: OutcomeDisputeRequest,
    ) -> Outcome:
        outcome = await self.get_outcome(outcome_id, workspace_id)
        disputed = await self.verification.dispute_outcome(
            outcome=outcome,
            disputed_by_user_id=user_id,
            reason=data.reason,
            evidence_ids=data.evidence_ids,
        )
        await self.events.emit_outcome_event(
            event_type="outcome.disputed",
            workspace_id=workspace_id,
            outcome_id=disputed.id,
            payload={"disputed_by": user_id, "reason": data.reason},
            actor_id=user_id,
        )
        return disputed

    # =========================================================================
    # Health, Graph & Recommendations
    # =========================================================================

    async def get_outcome_health(self, outcome_id: str, workspace_id: str) -> OutcomeHealthResponse:
        outcome = await self.get_outcome(outcome_id, workspace_id)
        evidence_list = await self.repo.list_evidence_for_outcome(outcome_id)
        eval_res = HealthEvaluator.evaluate_outcome_health(outcome, evidence_list)
        return OutcomeHealthResponse(
            status=eval_res["status"],
            is_healthy=eval_res["is_healthy"],
            reasons=eval_res["reasons"],
            checked_at=eval_res["checked_at"],
            details=eval_res.get("details", {}),
        )

    async def get_outcome_work_map(self, outcome_id: str, workspace_id: str) -> OutcomeWorkMapResponse:
        await self.get_outcome(outcome_id, workspace_id)
        return await self.graph.get_outcome_work_map(outcome_id, workspace_id)

    async def get_outcome_recommendations(self, outcome_id: str, workspace_id: str) -> List[OutcomeRecommendationResponse]:
        outcome = await self.get_outcome(outcome_id, workspace_id)
        return await self.recommendations.get_recommendations_for_outcome(outcome, workspace_id)

    # =========================================================================
    # Decisions
    # =========================================================================

    async def create_decision(self, workspace_id: str, created_by: str, data: WorkDecisionCreate) -> WorkDecision:
        OutcomeValidator.validate_decision_provenance(data.decision_type, data.provenance)
        OutcomePolicyEngine.validate_decision_provenance(
            decision_type=data.decision_type,
            provenance=data.provenance or {},
            decision_owner=data.decision_owner,
        )

        decision = WorkDecision(
            workspace_id=workspace_id,
            project_id=data.project_id,
            objective_id=data.objective_id,
            outcome_id=data.outcome_id,
            title=data.title,
            description=data.description,
            decision_type=data.decision_type,
            status=WorkDecisionStatus.PROPOSED.value,
            decision_owner=data.decision_owner,
            evidence_ids=data.evidence_ids or [],
            provenance=data.provenance or {},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        created = await self.repo.create_decision(decision)
        await self.events.emit_decision_event(
            event_type="decision.created",
            workspace_id=workspace_id,
            decision_id=created.id,
            payload={"title": created.title, "type": created.decision_type},
            project_id=created.project_id,
            actor_id=created_by,
        )
        return created

    async def get_decision(self, decision_id: str, workspace_id: str) -> WorkDecision:
        decision = await self.repo.get_decision(decision_id, workspace_id)
        if not decision:
            raise WorkDecisionNotFoundError(decision_id)
        OutcomePolicyEngine.enforce_tenant_isolation(decision.workspace_id, workspace_id)
        return decision

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
        return await self.repo.list_decisions(
            workspace_id=workspace_id,
            project_id=project_id,
            objective_id=objective_id,
            outcome_id=outcome_id,
            status=status,
            limit=limit,
            offset=offset,
        )

    async def update_decision(self, decision_id: str, workspace_id: str, data: WorkDecisionUpdate) -> WorkDecision:
        decision = await self.get_decision(decision_id, workspace_id)

        if data.status and data.status != decision.status:
            OutcomeLifecycle.validate_decision_transition(decision.status, data.status)
            decision.status = data.status

        if data.title is not None:
            decision.title = data.title
        if data.description is not None:
            decision.description = data.description
        if data.decision_owner is not None:
            decision.decision_owner = data.decision_owner
        if data.evidence_ids is not None:
            decision.evidence_ids = data.evidence_ids
        if data.provenance is not None:
            OutcomePolicyEngine.validate_decision_provenance(
                decision_type=decision.decision_type,
                provenance=data.provenance,
                decision_owner=decision.decision_owner,
            )
            decision.provenance = data.provenance

        return await self.repo.update_decision(decision)

    async def approve_decision(self, decision_id: str, workspace_id: str, user_id: str) -> WorkDecision:
        decision = await self.get_decision(decision_id, workspace_id)
        OutcomeLifecycle.validate_decision_transition(decision.status, WorkDecisionStatus.APPROVED.value)
        decision.status = WorkDecisionStatus.APPROVED.value
        decision.updated_at = datetime.now(timezone.utc)
        # Record approver in provenance
        decision.provenance = {**(decision.provenance or {}), "approved_by": user_id, "approved_at": datetime.now(timezone.utc).isoformat()}
        updated = await self.repo.update_decision(decision)

        await self.events.emit_decision_event(
            event_type="decision.approved",
            workspace_id=workspace_id,
            decision_id=updated.id,
            payload={"approved_by": user_id},
            actor_id=user_id,
        )
        return updated

    async def reject_decision(self, decision_id: str, workspace_id: str, user_id: str, reason: Optional[str] = None) -> WorkDecision:
        decision = await self.get_decision(decision_id, workspace_id)
        OutcomeLifecycle.validate_decision_transition(decision.status, WorkDecisionStatus.REJECTED.value)
        decision.status = WorkDecisionStatus.REJECTED.value
        decision.updated_at = datetime.now(timezone.utc)
        decision.provenance = {**(decision.provenance or {}), "rejected_by": user_id, "rejection_reason": reason, "rejected_at": datetime.now(timezone.utc).isoformat()}
        updated = await self.repo.update_decision(decision)

        await self.events.emit_decision_event(
            event_type="decision.rejected",
            workspace_id=workspace_id,
            decision_id=updated.id,
            payload={"rejected_by": user_id, "reason": reason},
            actor_id=user_id,
        )
        return updated
