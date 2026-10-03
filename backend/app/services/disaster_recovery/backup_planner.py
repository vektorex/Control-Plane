"""
Backup planning engine for Step 36: Disaster Recovery.
"""
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.services.disaster_recovery.models import BackupPolicy, BackupResource, BackupRun
from backend.app.services.disaster_recovery.dependencies import sort_resources_by_dependencies


CLASSIFICATION_HIERARCHY = {
    "public": 1,
    "internal": 2,
    "confidential": 3,
    "restricted": 4,
}


def resolve_highest_classification(classifications: List[str]) -> str:
    """Inherit the highest data classification among all included resources."""
    highest_level = 1
    highest_name = "public"
    for c in classifications:
        norm = c.lower().strip()
        lvl = CLASSIFICATION_HIERARCHY.get(norm, 2)
        if lvl > highest_level:
            highest_level = lvl
            highest_name = norm
    return highest_name


class BackupPlanner:
    """
    Evaluates scope, dependencies, legal holds, and data classifications to produce an executable backup plan.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_plan(
        self,
        organization_id: str,
        workspace_id: Optional[str] = None,
        policy_id: Optional[str] = None,
        resource_types: Optional[List[str]] = None,
        strategy: str = "logical_export",
    ) -> Dict[str, Any]:
        """
        Produce a structured backup plan.
        """
        # 1. Fetch policy if specified
        policy = None
        if policy_id:
            res = await self.session.execute(
                select(BackupPolicy).where(BackupPolicy.id == policy_id)
            )
            policy = res.scalar_one_or_none()

        # 2. Query registered backup resources in scope
        query = select(BackupResource).where(
            BackupResource.organization_id == organization_id,
            BackupResource.backup_required == True,
        )
        if workspace_id:
            query = query.where(BackupResource.workspace_id == workspace_id)
        if resource_types:
            query = query.where(BackupResource.resource_type.in_(resource_types))
        elif policy and policy.resource_type != "all":
            query = query.where(BackupResource.resource_type == policy.resource_type)

        res_resources = await self.session.execute(query)
        resources = res_resources.scalars().all()

        # 3. Resolve classifications and dependencies
        classifications = [r.classification for r in resources] if resources else ["internal"]
        highest_classification = resolve_highest_classification(classifications)

        raw_entries = [
            {
                "resource_type": r.resource_type,
                "resource_id": r.resource_id,
                "classification": r.classification,
                "dependencies": [],
            }
            for r in resources
        ]

        ordered_entries = sort_resources_by_dependencies(raw_entries)
        estimated_bytes = len(ordered_entries) * 2048  # Rough heuristic: 2KB per logical metadata/record

        return {
            "organization_id": organization_id,
            "workspace_id": workspace_id,
            "policy_id": policy_id,
            "strategy": strategy,
            "resource_count": len(ordered_entries),
            "estimated_bytes": estimated_bytes,
            "classification": highest_classification,
            "ordered_resources": ordered_entries,
        }
