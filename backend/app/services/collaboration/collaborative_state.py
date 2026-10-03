"""
Collaborative Shared State and Snapshot Service for Step 39: Collaboration.
Manages bounded shared state, change auditing, and cryptographic snapshots.
"""
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.services.collaboration.conflicts import ConflictResolver
from backend.app.services.collaboration.exceptions import CollaborationException
from backend.app.services.collaboration.models import (
    CollaborationChange,
    CollaborationSnapshot,
    CollaborativeState,
)


class CollaborativeStateManager:
    """Handles versioned collaborative state updates, change audit records, and snapshots."""

    def __init__(self, session: AsyncSession):
        self.db = session
        self.conflicts = ConflictResolver(session)

    async def get_state(
        self,
        session_id: str,
        resource_type: str,
        resource_id: str,
    ) -> Optional[CollaborativeState]:
        """Retrieves active collaborative state for a resource."""
        query = select(CollaborativeState).where(
            CollaborativeState.session_id == session_id,
            CollaborativeState.resource_type == resource_type,
            CollaborativeState.resource_id == resource_id,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_state(
        self,
        session_id: str,
        resource_type: str,
        resource_id: str,
        expected_version: int,
        new_state: Dict[str, Any],
        actor_id: str,
        change_summary: str = "Updated collaborative state",
    ) -> CollaborativeState:
        """
        Updates collaborative state with strict optimistic concurrency check.
        Records an audit change and increments version.
        """
        existing = await self.get_state(session_id, resource_type, resource_id)
        now = datetime.now(timezone.utc)

        if existing:
            # Check version match
            await self.conflicts.check_optimistic_concurrency(
                session_id=session_id,
                resource_type=resource_type,
                resource_id=resource_id,
                current_version=existing.version,
                expected_version=expected_version,
                actor_id=actor_id,
                incoming_state=new_state,
            )

            before_ver = existing.version
            existing.version += 1
            existing.state = new_state
            existing.updated_by = actor_id
            existing.updated_at = now
            state_obj = existing
            after_ver = existing.version
        else:
            if expected_version != 0:
                await self.conflicts.check_optimistic_concurrency(
                    session_id=session_id,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    current_version=0,
                    expected_version=expected_version,
                    actor_id=actor_id,
                )

            state_obj = CollaborativeState(
                session_id=session_id,
                resource_type=resource_type,
                resource_id=resource_id,
                version=1,
                state=new_state,
                updated_by=actor_id,
                updated_at=now,
            )
            self.db.add(state_obj)
            before_ver = 0
            after_ver = 1

        # Record Change
        change = CollaborationChange(
            session_id=session_id,
            resource_type=resource_type,
            resource_id=resource_id,
            actor_id=actor_id,
            change_type="update",
            before_version=before_ver,
            after_version=after_ver,
            summary=change_summary[:512],
            created_at=now,
        )
        self.db.add(change)
        await self.db.flush()
        return state_obj

    async def create_snapshot(
        self,
        session_id: str,
        resource_type: str,
        resource_id: str,
    ) -> CollaborationSnapshot:
        """Creates an immutable state snapshot with SHA-256 hash."""
        state = await self.get_state(session_id, resource_type, resource_id)
        if not state:
            raise CollaborationException("Cannot create snapshot for non-existent collaborative state.")

        serialized = json.dumps(state.state, sort_keys=True, separators=(",", ":"))
        state_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

        snapshot = CollaborationSnapshot(
            session_id=session_id,
            resource_type=resource_type,
            resource_id=resource_id,
            version=state.version,
            state_hash=state_hash,
            state=state.state,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(snapshot)
        await self.db.flush()
        return snapshot
