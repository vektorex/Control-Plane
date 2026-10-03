"""
Optimistic Concurrency and Conflict Resolution Service for Step 39: Collaboration.
Enforces version checks and deterministic merge safety for shared resources.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.services.collaboration.exceptions import ConflictError, CollaborationException
from backend.app.services.collaboration.models import CollaborationConflict, CollaborativeState

# Resources that require explicit manual modification and must never be auto-merged
NON_MERGEABLE_RESOURCE_TYPES = {
    "governance_policy",
    "security_policy",
    "security_incident",
    "credential",
    "rbac_role",
    "legal_hold",
    "retention_policy",
    "workflow_version",
    "marketplace_package",
}


class ConflictResolver:
    """Detects version mismatches and manages conflict records and safe metadata merging."""

    def __init__(self, session: AsyncSession):
        self.db = session

    async def check_optimistic_concurrency(
        self,
        session_id: str,
        resource_type: str,
        resource_id: str,
        current_version: int,
        expected_version: int,
        actor_id: str,
        incoming_state: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Validates expected_version against current_version.
        If mismatched, creates a CollaborationConflict record and raises ConflictError (HTTP 409).
        """
        if current_version != expected_version:
            now = datetime.now(timezone.utc)
            conflict = CollaborationConflict(
                session_id=session_id,
                resource_type=resource_type,
                resource_id=resource_id,
                base_version=expected_version,
                current_version=current_version,
                incoming_version=expected_version + 1,
                actor_id=actor_id,
                status="open",
                created_at=now,
            )
            self.db.add(conflict)
            await self.db.flush()

            raise ConflictError(
                resource_id=resource_id,
                current_version=current_version,
                expected_version=expected_version,
                message=(
                    f"Resource '{resource_id}' version conflict. Current version is {current_version}, "
                    f"but update expected version {expected_version}."
                ),
            )

    @classmethod
    def can_auto_merge(cls, resource_type: str) -> bool:
        """Determines whether a resource type is safe for deterministic field-level auto-merge."""
        return resource_type not in NON_MERGEABLE_RESOURCE_TYPES

    @classmethod
    def safe_3way_merge(
        cls,
        base: Dict[str, Any],
        current: Dict[str, Any],
        incoming: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], List[str]]:
        """
        Performs safe 3-way non-destructive field merge for safe dictionary metadata.
        Returns (merged_dict, conflicts_list).
        """
        merged = dict(current)
        conflicts: List[str] = []
        all_keys = set(base.keys()) | set(current.keys()) | set(incoming.keys())

        for k in all_keys:
            base_val = base.get(k)
            curr_val = current.get(k)
            inc_val = incoming.get(k)

            # If incoming changed key and current kept base value
            if inc_val != base_val and curr_val == base_val:
                merged[k] = inc_val
            # If current changed key and incoming kept base value
            elif curr_val != base_val and inc_val == base_val:
                merged[k] = curr_val
            # If both changed and they match
            elif curr_val == inc_val:
                merged[k] = inc_val
            # If both changed differently relative to base
            elif inc_val != base_val and curr_val != base_val and inc_val != curr_val:
                conflicts.append(k)

        return merged, conflicts

    @classmethod
    def attempt_safe_field_merge(
        cls,
        resource_type: str,
        current_state: Dict[str, Any],
        incoming_state: Dict[str, Any],
        base_state: Dict[str, Any],
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Attempts 3-way non-destructive field merge for safe dictionary metadata.
        Returns (success, merged_state).
        Strictly refuses to auto-merge sensitive security/governance/workflow resources.
        """
        if not cls.can_auto_merge(resource_type):
            return False, current_state

        if not isinstance(current_state, dict) or not isinstance(incoming_state, dict):
            return False, current_state

        merged, conflicts = cls.safe_3way_merge(base_state, current_state, incoming_state)
        if conflicts:
            return False, current_state

        return True, merged

    async def resolve_conflict(
        self,
        conflict_id: str,
        strategy: str,  # keep_current, apply_changes, manual_merge
        merged_state: Optional[Dict[str, Any]] = None,
    ) -> CollaborationConflict:
        """Resolves an open conflict with the specified strategy."""
        query = select(CollaborationConflict).where(CollaborationConflict.id == conflict_id)
        result = await self.db.execute(query)
        conflict = result.scalar_one_or_none()

        if not conflict:
            raise CollaborationException(f"Conflict record '{conflict_id}' not found.")

        conflict.status = "resolved"
        conflict.resolution_strategy = strategy
        conflict.resolved_at = datetime.now(timezone.utc)
        await self.db.flush()
        return conflict
