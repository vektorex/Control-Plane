"""
Dependency resolution, ordering, and topology for Step 36: Disaster Recovery.
"""
from typing import Any, Dict, List, Set


DEFAULT_RESTORE_ORDER: List[str] = [
    "organization",
    "workspace",
    "project",
    "user_reference",
    "governance_policy",
    "governance_policy_version",
    "prompt",
    "prompt_version",
    "prompt_release",
    "document",
    "document_chunk",
    "artifact",
    "artifact_part",
    "workflow",
    "workflow_version",
    "task",
    "run",
    "workflow_run",
    "evaluation_dataset",
    "evaluation_case",
    "evaluation_experiment",
    "evaluation_run",
    "memory",
    "knowledge_graph_entity",
    "knowledge_graph_relationship",
    "trigger",
    "trigger_run",
    "job",
    "connector_configuration",
    "notification",
    "reliability_configuration",
    "compliance_evidence",
]

RECOVERY_SERVICE_DEPENDENCIES: Dict[str, List[str]] = {
    "database": [],
    "authentication": ["database"],
    "governance": ["database", "authentication"],
    "security": ["database", "authentication", "governance"],
    "jobs": ["database", "security"],
    "events": ["database", "jobs"],
    "ai_gateway": ["database", "governance", "security"],
    "workflows": ["database", "ai_gateway", "jobs", "events"],
    "connectors": ["database", "governance", "workflows"],
    "documents": ["database", "workflows"],
    "memory": ["database", "workflows"],
    "knowledge_graph": ["database", "memory"],
    "notifications": ["database", "events"],
    "analytics": ["database", "workflows", "events"],
}


def get_type_priority(resource_type: str) -> int:
    """Return topological index priority for given resource type."""
    try:
        return DEFAULT_RESTORE_ORDER.index(resource_type)
    except ValueError:
        return len(DEFAULT_RESTORE_ORDER) + 10


def sort_resources_by_dependencies(resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sort a list of resource metadata dicts using a hybrid of type priority
    and explicit ID dependencies (topological sort).
    """
    # Build lookup
    res_by_id = {r.get("resource_id", str(idx)): r for idx, r in enumerate(resources)}
    
    # Simple dependency graph
    adj: Dict[str, List[str]] = {}
    in_degree: Dict[str, int] = {}
    
    for r_id, r in res_by_id.items():
        adj[r_id] = []
        in_degree[r_id] = 0

    for r_id, r in res_by_id.items():
        deps = r.get("dependencies", [])
        for dep in deps:
            if dep in res_by_id:
                adj[dep].append(r_id)
                in_degree[r_id] += 1

    # Kahn's algorithm with priority queue
    queue = [r_id for r_id, deg in in_degree.items() if deg == 0]
    # Sort queue initially by type priority
    queue.sort(key=lambda rid: get_type_priority(res_by_id[rid].get("resource_type", "")))

    ordered: List[Dict[str, Any]] = []
    while queue:
        curr_id = queue.pop(0)
        ordered.append(res_by_id[curr_id])

        for neighbor in adj.get(curr_id, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
                queue.sort(key=lambda rid: get_type_priority(res_by_id[rid].get("resource_type", "")))

    # Append any remaining circular or disconnected
    if len(ordered) < len(resources):
        seen_ids = {r.get("resource_id") for r in ordered}
        remainder = [r for r in resources if r.get("resource_id") not in seen_ids]
        remainder.sort(key=lambda r: get_type_priority(r.get("resource_type", "")))
        ordered.extend(remainder)

    return ordered


def resolve_recovery_service_order(critical_services: List[str]) -> List[str]:
    """
    Return topologically sorted sequence of service restoration.
    """
    visited: Set[str] = set()
    result: List[str] = []

    def visit(svc: str):
        if svc in visited:
            return
        visited.add(svc)
        for dep in RECOVERY_SERVICE_DEPENDENCIES.get(svc, []):
            if dep in critical_services:
                visit(dep)
        result.append(svc)

    for service in critical_services:
        visit(service)

    return result
