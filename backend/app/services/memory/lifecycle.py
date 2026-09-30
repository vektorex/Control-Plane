"""
Memory lifecycle state machine: creation, deduplication, conflict detection,
confirmation, archiving, restoration, expiration, and merging.
"""
from datetime import datetime, timezone
import difflib
from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import select, and_, or_, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.memory import (
    Memory,
    MemoryConflict,
    MemorySuggestion,
)
from backend.app.services.memory.errors import (
    MemoryConflictError,
    MemoryNotFoundError,
    MemoryValidationError,
)
from backend.app.services.memory.schemas import (
    ConflictResolveRequest,
    MemoryStatus,
)


class MemoryLifecycleService:
    """
    Coordinates memory transitions, similarity deduplication, and conflict tracking.
    """

    @classmethod
    def calculate_text_similarity(cls, a: str, b: str) -> float:
        """Computes quick SequenceMatcher similarity ratio [0.0 - 1.0]."""
        if not a or not b:
            return 0.0
        return difflib.SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()

    @classmethod
    async def check_duplicates(
        cls,
        session: AsyncSession,
        workspace_id: UUID,
        title: str,
        normalized_content: str,
        scope: str,
        user_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        threshold: float = 0.85,
    ) -> Optional[Memory]:
        """
        Scans active memories in the same workspace and scope to detect near-duplicates.
        """
        filters = [
            Memory.workspace_id == workspace_id,
            Memory.scope == scope,
            Memory.status == MemoryStatus.ACTIVE.value,
        ]
        if user_id and scope == "user":
            filters.append(Memory.user_id == user_id)
        if project_id and scope == "project":
            filters.append(Memory.project_id == project_id)

        stmt = select(Memory).where(and_(*filters))
        res = await session.execute(stmt)
        existing = res.scalars().all()

        for mem in existing:
            # Check title similarity
            title_sim = cls.calculate_text_similarity(mem.title, title)
            # Check content similarity
            content_sim = cls.calculate_text_similarity(mem.normalized_content, normalized_content)
            # Treat as duplicate only if content is essentially identical (>= 0.90) or both title & content are very high
            if content_sim >= 0.90 or (title_sim >= 0.95 and content_sim >= 0.88):
                return mem
        return None

    @classmethod
    async def detect_and_record_conflict(
        cls,
        session: AsyncSession,
        workspace_id: UUID,
        new_memory: Memory,
    ) -> Optional[MemoryConflict]:
        """
        Detects if a new memory directly opposes an existing active memory
        in the same type, category, or scope, and registers a MemoryConflict.
        """
        filters = [
            Memory.workspace_id == workspace_id,
            Memory.id != new_memory.id,
            Memory.scope == new_memory.scope,
            Memory.type == new_memory.type,
            Memory.status == MemoryStatus.ACTIVE.value,
        ]
        if new_memory.scope == "user" and new_memory.user_id:
            filters.append(Memory.user_id == new_memory.user_id)
        if new_memory.scope == "project" and new_memory.project_id:
            filters.append(Memory.project_id == new_memory.project_id)

        stmt = select(Memory).where(and_(*filters))
        res = await session.execute(stmt)
        candidates = res.scalars().all()

        # Check for directive contradictions (e.g. use X vs use Y)
        for existing_mem in candidates:
            # If titles or types are identical/near but contents differ
            t_sim = cls.calculate_text_similarity(existing_mem.title, new_memory.title)
            c_sim = cls.calculate_text_similarity(existing_mem.content, new_memory.content)
            if t_sim >= 0.6 and c_sim < 0.88:
                # Contradiction suspected! Check if conflict record already exists
                conf_stmt = select(MemoryConflict).where(
                    and_(
                        MemoryConflict.workspace_id == workspace_id,
                        or_(
                            and_(MemoryConflict.memory_a_id == existing_mem.id, MemoryConflict.memory_b_id == new_memory.id),
                            and_(MemoryConflict.memory_a_id == new_memory.id, MemoryConflict.memory_b_id == existing_mem.id),
                        ),
                    )
                )
                conf_res = await session.execute(conf_stmt)
                existing_conf = conf_res.scalars().first()
                if not existing_conf:
                    conflict = MemoryConflict(
                        workspace_id=workspace_id,
                        memory_a_id=existing_mem.id,
                        memory_b_id=new_memory.id,
                        status="unresolved",
                        resolution=f"Conflicting preferences detected between memory '{existing_mem.title}' and '{new_memory.title}'.",
                    )
                    session.add(conflict)
                    return conflict
        return None

    @classmethod
    async def resolve_conflict(
        cls,
        session: AsyncSession,
        conflict: MemoryConflict,
        request: ConflictResolveRequest,
    ) -> MemoryConflict:
        """
        Resolves a detected conflict:
        - 'keep_winner': archives the non-winner memory and keeps the winner
        - 'merge': updates one memory with merged content and archives the other
        - 'dismiss': leaves both active but marks conflict dismissed
        """
        now = datetime.now(timezone.utc)
        mem_a = await session.get(Memory, conflict.memory_a_id)
        mem_b = await session.get(Memory, conflict.memory_b_id)

        if not mem_a or not mem_b:
            conflict.status = "resolved"
            conflict.resolved_at = now
            conflict.resolution = "One or both memories were deleted."
            return conflict

        if request.action == "keep_winner":
            winner_id = request.winner_memory_id or mem_b.id  # Default to newer
            loser = mem_a if winner_id == mem_b.id else mem_b
            winner = mem_b if winner_id == mem_b.id else mem_a

            loser.status = MemoryStatus.ARCHIVED.value
            conflict.status = "resolved"
            conflict.resolved_at = now
            conflict.resolution = f"Resolved: Memory '{winner.title}' retained. Memory '{loser.title}' archived."

        elif request.action == "merge":
            if not request.merged_content:
                raise MemoryValidationError("Merged content must be provided when merging conflicting memories.")
            mem_b.content = request.merged_content
            mem_b.normalized_content = request.merged_content
            mem_a.status = MemoryStatus.ARCHIVED.value
            conflict.status = "resolved"
            conflict.resolved_at = now
            conflict.resolution = f"Resolved: Merged into '{mem_b.title}'."

        elif request.action == "dismiss":
            conflict.status = "dismissed"
            conflict.resolved_at = now
            conflict.resolution = request.resolution_note or "Dismissed by user without state changes."

        return conflict

    @classmethod
    async def expire_stale_memories(cls, session: AsyncSession, workspace_id: UUID) -> int:
        """
        Checks for any active memories whose expires_at timestamp has passed and marks them expired.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            update(Memory)
            .where(
                and_(
                    Memory.workspace_id == workspace_id,
                    Memory.status == MemoryStatus.ACTIVE.value,
                    Memory.expires_at.is_not(None),
                    Memory.expires_at < now,
                )
            )
            .values(status=MemoryStatus.EXPIRED.value)
        )
        res = await session.execute(stmt)
        return res.rowcount or 0
