"""
Advisory Planning Recommendations for Step 44.
Recommendations never directly execute privileged actions.
"""
from typing import Any, Dict, List, Optional
from backend.app.services.planning.models import (
    PlanningBlocker,
    PlanningItem,
    WorkResource,
)
from backend.app.services.planning.policies import PlanningPolicyEngine


class PlanningRecommendationGenerator:
    """
    Generates non-privileged, evidence-backed advisory recommendations.
    """

    @classmethod
    def generate_recommendations(
        cls,
        items: List[PlanningItem],
        blockers: List[PlanningBlocker],
        resources: List[WorkResource],
    ) -> List[Dict[str, Any]]:
        recommendations: List[Dict[str, Any]] = []

        # 1. Check for unassigned items or capability mismatches
        for item in items:
            req_caps = item.required_capabilities or []
            if req_caps:
                has_match = any(
                    all(c.lower() in [rc.lower() for rc in (r.capabilities or [])] for c in req_caps)
                    for r in resources if r.status == "active"
                )
                if not has_match:
                    reason = f"Item '{item.name}' requires capabilities {req_caps}, but no active resource provides them all."
                    PlanningPolicyEngine.validate_no_subjective_rankings(reason)
                    recommendations.append({
                        "recommendation_type": "use_another_agent",
                        "description": f"Assign or register an agent/resource with capabilities {req_caps}.",
                        "reason": reason,
                        "evidence_ids": [item.id],
                        "affected_resources": [],
                        "affected_items": [item.id],
                        "risk": "Item execution will be blocked until a suitable resource is configured.",
                        "assumptions": ["Resource registration follows existing Governance and RBAC policies."],
                    })

        # 2. Check for active blockers
        for blk in blockers:
            if blk.status == "open":
                rec_type = "resolve_blocker"
                if blk.type == "approval":
                    rec_type = "request_approval"
                elif blk.type == "deadline":
                    rec_type = "update_deadline"

                reason = f"Blocker ({blk.type}): {blk.description}"
                PlanningPolicyEngine.validate_no_subjective_rankings(reason)
                recommendations.append({
                    "recommendation_type": rec_type,
                    "description": f"Resolve open blocker on item: {blk.description}",
                    "reason": reason,
                    "evidence_ids": blk.evidence_ids or [],
                    "affected_resources": [],
                    "affected_items": [blk.planning_item_id] if blk.planning_item_id else [],
                    "risk": f"High risk of schedule delay if severity '{blk.severity}' is unresolved.",
                    "assumptions": ["Manual or workflow resolution is required."],
                })

        return recommendations
