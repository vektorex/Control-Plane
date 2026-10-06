"""
Outcome Graph Service for Step 43:
AI Outcome Intelligence & Work Impact Layer.
Integrates with Step 29 Knowledge Graph and constructs bounded work-to-outcome graphs.
Enforces bounded hops (1-3 hops max) and tenant isolation.
"""
from typing import Any, Dict, List, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.outcomes.models import (
    Objective,
    Outcome,
    OutcomeMilestone,
    OutcomeTarget,
    OutcomeWorkLink,
    OutcomeEvidence,
    OutcomeMeasurement,
    WorkDecision,
    OutcomeAttribution,
)
from backend.app.services.outcomes.repository import OutcomeRepository
from backend.app.services.outcomes.schemas import WorkMapEdge, WorkMapNode, OutcomeWorkMapResponse


class OutcomeGraphService:
    """
    Answers graph queries over objectives, outcomes, work executions, evidence, and decisions.
    Bounded traversal: 1-3 hops maximum.
    """

    MAX_HOPS: int = 3
    DEFAULT_HOPS: int = 2

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = OutcomeRepository(session)

    async def get_outcome_work_map(
        self,
        outcome_id: str,
        workspace_id: str,
        max_hops: int = DEFAULT_HOPS,
    ) -> OutcomeWorkMapResponse:
        """
        Builds the visual work-to-outcome graph for an outcome within bounded hops.
        Nodes: Objective, Milestone, WorkLink (Task/Run/Agent), Artifact, Evidence, Outcome, Measurement, Decision.
        Edges: supports, contributes_to, achieved_by, produced, validated_by, measures, decided_by.
        """
        effective_hops = min(max(1, max_hops), self.MAX_HOPS)
        nodes: Dict[str, WorkMapNode] = {}
        edges: List[WorkMapEdge] = []

        outcome = await self.repo.get_outcome(outcome_id, workspace_id)
        if not outcome:
            return OutcomeWorkMapResponse(root_id=outcome_id, root_type="outcome", nodes=[], edges=[])

        # 1. Root Outcome node
        nodes[f"outcome:{outcome.id}"] = WorkMapNode(
            id=f"outcome:{outcome.id}",
            label=outcome.name,
            node_type="outcome",
            status=outcome.status,
            metadata={"type": outcome.outcome_type, "confidence": outcome.confidence},
        )

        # 2. Objective & Milestones (Hop 1)
        if outcome.objective_id:
            obj = await self.repo.get_objective(outcome.objective_id, workspace_id)
            if obj:
                obj_node_id = f"objective:{obj.id}"
                nodes[obj_node_id] = WorkMapNode(
                    id=obj_node_id,
                    label=obj.name,
                    node_type="objective",
                    status=obj.status,
                    metadata={"priority": obj.priority, "type": obj.objective_type},
                )
                edges.append(WorkMapEdge(
                    source=f"outcome:{outcome.id}",
                    target=obj_node_id,
                    relationship="achieves",
                ))

                for m in obj.milestones[:10]:
                    m_node_id = f"milestone:{m.id}"
                    nodes[m_node_id] = WorkMapNode(
                        id=m_node_id,
                        label=m.name,
                        node_type="milestone",
                        status=m.status,
                        metadata={"due_at": m.due_at.isoformat() if m.due_at else None},
                    )
                    edges.append(WorkMapEdge(
                        source=obj_node_id,
                        target=m_node_id,
                        relationship="has_milestone",
                    ))

        # 3. Work Links (Hop 1)
        work_links = await self.repo.list_work_links_for_outcome(outcome_id)
        for wl in work_links[:25]:
            wl_node_id = f"work:{wl.resource_type}:{wl.resource_id}"
            nodes[wl_node_id] = WorkMapNode(
                id=wl_node_id,
                label=f"{wl.resource_type} #{wl.resource_id[:8]}",
                node_type=wl.resource_type.lower(),
                status="linked",
                metadata={"resource_id": wl.resource_id, "resource_type": wl.resource_type},
            )
            edges.append(WorkMapEdge(
                source=wl_node_id,
                target=f"outcome:{outcome.id}",
                relationship=wl.relationship_type,
                evidence_ids=wl.evidence_ids or [],
            ))

        # 4. Evidence (Hop 1 / Hop 2)
        evidence_list = await self.repo.list_evidence_for_outcome(outcome_id)
        for ev in evidence_list[:25]:
            ev_node_id = f"evidence:{ev.id}"
            nodes[ev_node_id] = WorkMapNode(
                id=ev_node_id,
                label=ev.description[:40] + ("..." if len(ev.description) > 40 else ""),
                node_type="evidence",
                status=ev.status,
                metadata={
                    "evidence_type": ev.evidence_type,
                    "is_human_confirmed": ev.is_human_confirmed,
                    "is_ai_generated": ev.is_ai_generated,
                },
            )
            edges.append(WorkMapEdge(
                source=ev_node_id,
                target=f"outcome:{outcome.id}",
                relationship="validates",
                evidence_ids=[ev.id],
            ))

        # 5. Measurements (Hop 1)
        measurements = await self.repo.list_measurements_for_outcome(outcome_id)
        for meas in measurements[:15]:
            meas_node_id = f"measurement:{meas.id}"
            nodes[meas_node_id] = WorkMapNode(
                id=meas_node_id,
                label=f"{meas.metric_name}: {meas.value} {meas.unit}",
                node_type="measurement",
                status="observed",
                metadata={"source": meas.measurement_source, "value": meas.value, "unit": meas.unit},
            )
            edges.append(WorkMapEdge(
                source=meas_node_id,
                target=f"outcome:{outcome.id}",
                relationship="measures",
            ))

        # 6. Decisions (Hop 1 / Hop 2)
        decisions = await self.repo.list_decisions(workspace_id=workspace_id, outcome_id=outcome_id)
        for dec in decisions[:10]:
            dec_node_id = f"decision:{dec.id}"
            nodes[dec_node_id] = WorkMapNode(
                id=dec_node_id,
                label=dec.title,
                node_type="decision",
                status=dec.status,
                metadata={"decision_type": dec.decision_type, "owner": dec.decision_owner},
            )
            edges.append(WorkMapEdge(
                source=dec_node_id,
                target=f"outcome:{outcome.id}",
                relationship="governs",
            ))

        return OutcomeWorkMapResponse(
            root_id=outcome.id,
            root_type="outcome",
            nodes=list(nodes.values()),
            edges=edges,
        )

    async def get_objective_work_map(
        self,
        objective_id: str,
        workspace_id: str,
        max_hops: int = DEFAULT_HOPS,
    ) -> OutcomeWorkMapResponse:
        """
        Builds the visual work map rooted at an Objective.
        """
        nodes: Dict[str, WorkMapNode] = {}
        edges: List[WorkMapEdge] = []

        obj = await self.repo.get_objective(objective_id, workspace_id)
        if not obj:
            return OutcomeWorkMapResponse(root_id=objective_id, root_type="objective", nodes=[], edges=[])

        obj_node_id = f"objective:{obj.id}"
        nodes[obj_node_id] = WorkMapNode(
            id=obj_node_id,
            label=obj.name,
            node_type="objective",
            status=obj.status,
            metadata={"priority": obj.priority, "type": obj.objective_type},
        )

        # Targets
        for t in obj.targets:
            t_node_id = f"target:{t.id}"
            nodes[t_node_id] = WorkMapNode(
                id=t_node_id,
                label=t.name,
                node_type="outcome_target",
                status=t.status,
                metadata={"current": t.current_value, "target": t.target_value, "unit": t.target_unit},
            )
            edges.append(WorkMapEdge(source=obj_node_id, target=t_node_id, relationship="measures"))

        # Milestones
        for m in obj.milestones:
            m_node_id = f"milestone:{m.id}"
            nodes[m_node_id] = WorkMapNode(
                id=m_node_id,
                label=m.name,
                node_type="milestone",
                status=m.status,
                metadata={"due_at": m.due_at.isoformat() if m.due_at else None},
            )
            edges.append(WorkMapEdge(source=obj_node_id, target=m_node_id, relationship="has_milestone"))

        # Outcomes
        for o in obj.outcomes:
            o_node_id = f"outcome:{o.id}"
            nodes[o_node_id] = WorkMapNode(
                id=o_node_id,
                label=o.name,
                node_type="outcome",
                status=o.status,
                metadata={"type": o.outcome_type, "confidence": o.confidence},
            )
            edges.append(WorkMapEdge(source=o_node_id, target=obj_node_id, relationship="achieves"))

        return OutcomeWorkMapResponse(
            root_id=obj.id,
            root_type="objective",
            nodes=list(nodes.values()),
            edges=edges,
        )
