"""
Resource Management, Suitability Matching, and Capability Alignment for Step 44.
"""
from typing import Any, Dict, List, Optional
from backend.app.services.planning.models import WorkResource
from backend.app.services.planning.policies import PlanningPolicyEngine


class ResourceMatchResult:
    def __init__(
        self,
        resource_id: str,
        resource_name: str,
        resource_type: str,
        matched: bool,
        matching_capabilities: List[str],
        missing_capabilities: List[str],
        explanation: str,
        is_available: bool = True,
        concurrency_ok: bool = True,
    ):
        self.resource_id = resource_id
        self.resource_name = resource_name
        self.resource_type = resource_type
        self.matched = matched
        self.matching_capabilities = matching_capabilities
        self.missing_capabilities = missing_capabilities
        self.explanation = explanation
        self.is_available = is_available
        self.concurrency_ok = concurrency_ok

    def to_dict(self) -> Dict[str, Any]:
        return {
            "resource_id": self.resource_id,
            "resource_name": self.resource_name,
            "resource_type": self.resource_type,
            "matched": self.matched,
            "matching_capabilities": self.matching_capabilities,
            "missing_capabilities": self.missing_capabilities,
            "explanation": self.explanation,
            "is_available": self.is_available,
            "concurrency_ok": self.concurrency_ok,
        }


class ResourceMatcher:
    """
    Factual capability and constraint matcher.
    Never uses subjective 'best' or 'worst' ratings.
    """

    @classmethod
    def match_item_to_resource(
        cls,
        item_capabilities: List[str],
        resource: WorkResource,
        current_concurrency: int = 0,
    ) -> ResourceMatchResult:
        res_caps = set(c.lower() for c in (resource.capabilities or []))
        required = set(c.lower() for c in item_capabilities)

        matched_caps = sorted(list(required.intersection(res_caps)))
        missing_caps = sorted(list(required.difference(res_caps)))

        is_active = (resource.status == "active")
        policy = resource.availability_policy or {}
        max_concurrency = policy.get("max_concurrent_runs", 5)
        concurrency_ok = current_concurrency < max_concurrency

        matched = len(missing_caps) == 0 and is_active and concurrency_ok

        # Factual explanation
        if matched:
            explanation = (
                f"Resource '{resource.name}' ({resource.resource_type}) matches all required capabilities: "
                f"[{', '.join(matched_caps)}], status is active, and current concurrency ({current_concurrency}) "
                f"is within configured limit ({max_concurrency})."
            )
        elif not is_active:
            explanation = f"Resource '{resource.name}' is inactive (status: {resource.status})."
        elif not concurrency_ok:
            explanation = (
                f"Resource '{resource.name}' has reached max concurrency limit ({max_concurrency})."
            )
        else:
            explanation = (
                f"Resource '{resource.name}' is missing required capabilities: [{', '.join(missing_caps)}]."
            )

        # Safety policy check: no subjective rankings
        PlanningPolicyEngine.validate_no_subjective_rankings(explanation)

        return ResourceMatchResult(
            resource_id=resource.id,
            resource_name=resource.name,
            resource_type=resource.resource_type,
            matched=matched,
            matching_capabilities=matched_caps,
            missing_capabilities=missing_caps,
            explanation=explanation,
            is_available=is_active,
            concurrency_ok=concurrency_ok,
        )

    @classmethod
    def find_matching_resources(
        cls,
        item_capabilities: List[str],
        resources: List[WorkResource],
        concurrency_map: Optional[Dict[str, int]] = None,
    ) -> List[ResourceMatchResult]:
        concurrency_map = concurrency_map or {}
        results: List[ResourceMatchResult] = []
        for res in resources:
            cur_conc = concurrency_map.get(res.id, 0)
            match = cls.match_item_to_resource(item_capabilities, res, cur_conc)
            results.append(match)
        return results
