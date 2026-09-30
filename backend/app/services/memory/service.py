"""
Core MemoryService coordinating CRUD, deduplication, conflict resolution,
suggestions, settings, and telemetry.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID
from sqlalchemy import select, and_, or_, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.logging import logger
from backend.app.db.models.memory import (
    Memory,
    MemoryEmbedding,
    MemoryConflict,
    MemorySuggestion,
    UserMemorySettings,
)
from backend.app.db.models.user import User
from backend.app.services.embeddings.base import BaseEmbeddingProvider
from backend.app.services.embeddings.factory import get_embedding_provider
from backend.app.services.memory.classifier import MemoryClassifier
from backend.app.services.memory.errors import (
    MemoryNotFoundError,
    MemoryPermissionError,
    MemoryValidationError,
)
from backend.app.services.memory.lifecycle import MemoryLifecycleService
from backend.app.services.memory.policies import MemoryPolicy
from backend.app.services.memory.retriever import MemoryRetriever
from backend.app.services.memory.sanitizer import sanitize_memory
from backend.app.services.memory.schemas import (
    CandidateMemory,
    ConflictResolveRequest,
    MemoryCreateRequest,
    MemoryScope,
    MemoryStatus,
    MemoryUpdateRequest,
    UserMemorySettingsUpdateRequest,
)
from backend.app.services.observability.events import TraceEventStatus, TraceEventType
from backend.app.services.observability.service import ObservabilityService


class MemoryService:
    """
    Central service for persistent context intelligence, memory lifecycle, and privacy controls.
    """

    def __init__(
        self,
        session: AsyncSession,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
        retriever: Optional[MemoryRetriever] = None,
    ):
        self.session = session
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.retriever = retriever or MemoryRetriever(embedding_provider=self.embedding_provider)
        self.obs_service = ObservabilityService(session)

    # =========================================================================
    # 1. Memory CRUD Operations
    # =========================================================================

    async def create_memory(
        self,
        workspace_id: UUID,
        user: User,
        request: MemoryCreateRequest,
    ) -> Memory:
        """
        Creates, sanitizes, classifies, deduplicates, embeds, and persists a memory.
        """
        # Validate scope
        MemoryPolicy.validate_scope(
            scope=request.scope.value,
            user_id=str(user.id) if user else None,
            project_id=str(request.project_id) if request.project_id else None,
        )

        # Sanitize content (enforces no raw credentials or secrets)
        clean_title, clean_content, normalized_content, clean_meta = sanitize_memory(
            title=request.title,
            content=request.content,
            metadata=request.metadata,
            enforce_no_secrets=True,
        )

        # Classification check
        classification = MemoryClassifier.classify(
            title=clean_title,
            content=clean_content,
            source_type=request.source_type.value,
        )
        if classification.status == "rejected":
            raise MemoryValidationError(f"Memory creation rejected: {classification.reason}")

        # Check for near duplicates in the same scope
        existing_dup = await MemoryLifecycleService.check_duplicates(
            session=self.session,
            workspace_id=workspace_id,
            title=clean_title,
            normalized_content=normalized_content,
            scope=request.scope.value,
            user_id=user.id if request.scope == MemoryScope.USER else None,
            project_id=request.project_id if request.scope == MemoryScope.PROJECT else None,
        )
        if existing_dup:
            # Touch last used and return existing memory instead of creating an uncontrolled duplicate
            existing_dup.last_used_at = datetime.now(timezone.utc)
            existing_dup.updated_at = datetime.now(timezone.utc)
            await self.session.commit()
            return existing_dup

        # Calculate expiration
        expires_at = MemoryPolicy.calculate_expiration(
            expiration_pref=request.expiration,
            custom_expires_at=request.expires_at,
        )

        # Instantiate Memory
        memory = Memory(
            workspace_id=workspace_id,
            user_id=user.id if request.scope == MemoryScope.USER else None,
            project_id=request.project_id if request.scope == MemoryScope.PROJECT else None,
            scope=request.scope.value,
            type=request.type.value,
            title=clean_title,
            content=clean_content,
            normalized_content=normalized_content,
            metadata_json=clean_meta,
            source_type=request.source_type.value,
            source_id=request.source_id,
            importance=request.importance.value,
            confidence=classification.confidence,
            status=MemoryStatus.ACTIVE.value,
            expires_at=expires_at,
        )
        self.session.add(memory)
        await self.session.flush()

        # Generate and persist vector embedding
        try:
            vector = await self.embedding_provider.embed_text(clean_content)
            mem_emb = MemoryEmbedding(
                memory_id=memory.id,
                embedding=vector,
                embedding_model="text-embedding-3-small",
            )
            self.session.add(mem_emb)
        except Exception as exc:
            logger.warning(f"[MemoryService] Embedding generation failed for memory {memory.id}: {exc}")

        # Check for directive conflicts
        await MemoryLifecycleService.detect_and_record_conflict(
            session=self.session,
            workspace_id=workspace_id,
            new_memory=memory,
        )

        await self.session.commit()
        await self.session.refresh(memory)

        logger.info(f"[MemoryService] Persisted memory '{memory.id}' (scope={memory.scope}, type={memory.type})")
        return memory

    async def get_memory(
        self,
        memory_id: UUID,
        workspace_id: UUID,
        user: User,
    ) -> Memory:
        stmt = (
            select(Memory)
            .options(selectinload(Memory.embedding))
            .where(
                and_(
                    Memory.id == memory_id,
                    Memory.workspace_id == workspace_id,
                )
            )
        )
        res = await self.session.execute(stmt)
        mem = res.scalars().first()
        if not mem:
            raise MemoryNotFoundError(str(memory_id))

        # Scope authorization check
        if mem.scope == MemoryScope.USER.value and mem.user_id != user.id:
            raise MemoryPermissionError("Cannot access private memory of another user.")

        return mem

    async def list_memories(
        self,
        workspace_id: UUID,
        user: User,
        scope: Optional[str] = None,
        type_: Optional[str] = None,
        status: Optional[str] = None,
        project_id: Optional[UUID] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Memory], int]:
        filters = [Memory.workspace_id == workspace_id]

        if status:
            filters.append(Memory.status == status)
        else:
            # Default to active and archived (excluding expired unless requested)
            filters.append(Memory.status.in_([MemoryStatus.ACTIVE.value, MemoryStatus.ARCHIVED.value]))

        if type_:
            filters.append(Memory.type == type_)

        if scope:
            filters.append(Memory.scope == scope)
            if scope == MemoryScope.USER.value:
                filters.append(Memory.user_id == user.id)
            elif scope == MemoryScope.PROJECT.value and project_id:
                filters.append(Memory.project_id == project_id)
        else:
            # Multi-tenant scoping rule: user only sees their own user memories + workspace memories + their project memories
            filters.append(
                or_(
                    Memory.scope == MemoryScope.WORKSPACE.value,
                    and_(Memory.scope == MemoryScope.USER.value, Memory.user_id == user.id),
                    and_(Memory.scope == MemoryScope.PROJECT.value, Memory.project_id == project_id) if project_id else Memory.scope == MemoryScope.PROJECT.value,
                )
            )

        if search and search.strip():
            term = f"%{search.strip()}%"
            filters.append(or_(Memory.title.ilike(term), Memory.normalized_content.ilike(term)))

        # Total count
        count_stmt = select(Memory.id).where(and_(*filters))
        count_res = await self.session.execute(count_stmt)
        total = len(count_res.scalars().all())

        stmt = (
            select(Memory)
            .options(selectinload(Memory.embedding))
            .where(and_(*filters))
            .order_by(Memory.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await self.session.execute(stmt)
        items = list(res.scalars().all())
        return items, total

    async def update_memory(
        self,
        memory_id: UUID,
        workspace_id: UUID,
        user: User,
        request: MemoryUpdateRequest,
    ) -> Memory:
        mem = await self.get_memory(memory_id, workspace_id, user)

        if request.title is not None:
            mem.title = request.title.strip()[:255]

        if request.content is not None:
            clean_title, clean_content, norm_content, _ = sanitize_memory(
                title=mem.title,
                content=request.content,
                enforce_no_secrets=True,
            )
            mem.content = clean_content
            mem.normalized_content = norm_content

            # Re-compute embedding
            try:
                vector = await self.embedding_provider.embed_text(clean_content)
                if mem.embedding:
                    mem.embedding.embedding = vector
                else:
                    self.session.add(
                        MemoryEmbedding(
                            memory_id=mem.id,
                            embedding=vector,
                            embedding_model="text-embedding-3-small",
                        )
                    )
            except Exception as exc:
                logger.warning(f"[MemoryService] Re-embedding failed for memory {mem.id}: {exc}")

        if request.importance is not None:
            mem.importance = request.importance.value

        if request.metadata is not None:
            mem.metadata_json = request.metadata

        if request.expires_at is not None:
            mem.expires_at = request.expires_at

        mem.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(mem)
        return mem

    async def delete_memory(
        self,
        memory_id: UUID,
        workspace_id: UUID,
        user: User,
    ) -> bool:
        mem = await self.get_memory(memory_id, workspace_id, user)
        await self.session.delete(mem)
        await self.session.commit()
        return True

    async def archive_memory(
        self,
        memory_id: UUID,
        workspace_id: UUID,
        user: User,
    ) -> Memory:
        mem = await self.get_memory(memory_id, workspace_id, user)
        mem.status = MemoryStatus.ARCHIVED.value
        mem.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(mem)
        return mem

    async def restore_memory(
        self,
        memory_id: UUID,
        workspace_id: UUID,
        user: User,
    ) -> Memory:
        mem = await self.get_memory(memory_id, workspace_id, user)
        mem.status = MemoryStatus.ACTIVE.value
        mem.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(mem)
        return mem

    async def touch_memory_used(
        self,
        memory_id: UUID,
        workspace_id: UUID,
    ) -> None:
        now = datetime.now(timezone.utc)
        await self.session.execute(
            update(Memory)
            .where(and_(Memory.id == memory_id, Memory.workspace_id == workspace_id))
            .values(last_used_at=now)
        )
        await self.session.commit()

    # =========================================================================
    # 2. Memory Suggestions
    # =========================================================================

    async def create_suggestion(
        self,
        workspace_id: UUID,
        candidate: CandidateMemory,
        user_id: Optional[UUID] = None,
    ) -> MemorySuggestion:
        """
        Creates an unconfirmed suggestion record.
        NEVER silently creates permanent memory.
        """
        clean_title, clean_content, _, clean_meta = sanitize_memory(
            title=candidate.title,
            content=candidate.content,
            enforce_no_secrets=True,
        )

        suggestion = MemorySuggestion(
            workspace_id=workspace_id,
            user_id=user_id if candidate.scope == MemoryScope.USER else None,
            project_id=candidate.project_id if candidate.scope == MemoryScope.PROJECT else None,
            type=candidate.type.value,
            scope=candidate.scope.value,
            title=clean_title,
            content=clean_content,
            reason=candidate.reason,
            confidence=candidate.confidence,
            source_type=candidate.source_type.value,
            source_id=candidate.source_id,
            importance=candidate.importance.value,
            status="pending",
            metadata_json=clean_meta,
        )
        self.session.add(suggestion)
        await self.session.commit()
        await self.session.refresh(suggestion)
        return suggestion

    async def list_suggestions(
        self,
        workspace_id: UUID,
        user: User,
        status: str = "pending",
    ) -> List[MemorySuggestion]:
        stmt = (
            select(MemorySuggestion)
            .where(
                and_(
                    MemorySuggestion.workspace_id == workspace_id,
                    MemorySuggestion.status == status,
                    or_(
                        MemorySuggestion.scope != MemoryScope.USER.value,
                        MemorySuggestion.user_id == user.id,
                        MemorySuggestion.user_id.is_(None),
                    ),
                )
            )
            .order_by(MemorySuggestion.created_at.desc())
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def accept_suggestion(
        self,
        suggestion_id: UUID,
        workspace_id: UUID,
        user: User,
    ) -> Memory:
        suggestion = await self.session.get(MemorySuggestion, suggestion_id)
        if not suggestion or suggestion.workspace_id != workspace_id:
            raise MemoryNotFoundError(str(suggestion_id))

        if suggestion.status != "pending":
            raise MemoryValidationError(f"Suggestion has already been {suggestion.status}.")

        create_req = MemoryCreateRequest(
            type=suggestion.type,
            scope=suggestion.scope,
            title=suggestion.title,
            content=suggestion.content,
            importance=suggestion.importance,
            project_id=suggestion.project_id,
            source_type=suggestion.source_type,
            source_id=suggestion.source_id,
            metadata=suggestion.metadata_json or {},
        )
        memory = await self.create_memory(workspace_id=workspace_id, user=user, request=create_req)

        suggestion.status = "accepted"
        suggestion.resolved_at = datetime.now(timezone.utc)
        await self.session.commit()
        return memory

    async def reject_suggestion(
        self,
        suggestion_id: UUID,
        workspace_id: UUID,
        user: User,
    ) -> bool:
        suggestion = await self.session.get(MemorySuggestion, suggestion_id)
        if not suggestion or suggestion.workspace_id != workspace_id:
            raise MemoryNotFoundError(str(suggestion_id))

        suggestion.status = "rejected"
        suggestion.resolved_at = datetime.now(timezone.utc)
        await self.session.commit()
        return True

    # =========================================================================
    # 3. Memory Conflicts
    # =========================================================================

    async def list_conflicts(
        self,
        workspace_id: UUID,
        status: Optional[str] = "unresolved",
    ) -> List[MemoryConflict]:
        filters = [MemoryConflict.workspace_id == workspace_id]
        if status:
            filters.append(MemoryConflict.status == status)

        stmt = (
            select(MemoryConflict)
            .options(
                selectinload(MemoryConflict.memory_a),
                selectinload(MemoryConflict.memory_b),
            )
            .where(and_(*filters))
            .order_by(MemoryConflict.detected_at.desc())
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def resolve_conflict(
        self,
        conflict_id: UUID,
        workspace_id: UUID,
        user: User,
        request: ConflictResolveRequest,
    ) -> MemoryConflict:
        stmt = (
            select(MemoryConflict)
            .options(
                selectinload(MemoryConflict.memory_a),
                selectinload(MemoryConflict.memory_b),
            )
            .where(MemoryConflict.id == conflict_id)
        )
        res = await self.session.execute(stmt)
        conflict = res.scalars().first()
        if not conflict or conflict.workspace_id != workspace_id:
            raise MemoryNotFoundError(str(conflict_id))

        await MemoryLifecycleService.resolve_conflict(
            session=self.session,
            conflict=conflict,
            request=request,
        )
        await self.session.commit()
        # Re-fetch with relationships to avoid DetachedInstanceError during response serialization
        reloaded = await self.session.execute(stmt)
        return reloaded.scalars().first()

    # =========================================================================
    # 4. User Memory Settings
    # =========================================================================

    async def get_or_create_settings(
        self,
        workspace_id: UUID,
        user_id: UUID,
    ) -> UserMemorySettings:
        stmt = select(UserMemorySettings).where(
            and_(
                UserMemorySettings.workspace_id == workspace_id,
                UserMemorySettings.user_id == user_id,
            )
        )
        res = await self.session.execute(stmt)
        settings = res.scalars().first()
        if not settings:
            settings = UserMemorySettings(
                workspace_id=workspace_id,
                user_id=user_id,
                memory_enabled=True,
                suggestions_enabled=True,
                default_retrieval_mode="auto",
                default_scope="user",
                retention_preference="never",
            )
            self.session.add(settings)
            await self.session.commit()
            await self.session.refresh(settings)
        return settings

    async def update_settings(
        self,
        workspace_id: UUID,
        user_id: UUID,
        request: UserMemorySettingsUpdateRequest,
    ) -> UserMemorySettings:
        settings = await self.get_or_create_settings(workspace_id, user_id)
        if request.memory_enabled is not None:
            settings.memory_enabled = request.memory_enabled
        if request.suggestions_enabled is not None:
            settings.suggestions_enabled = request.suggestions_enabled
        if request.default_retrieval_mode is not None:
            settings.default_retrieval_mode = request.default_retrieval_mode
        if request.default_scope is not None:
            settings.default_scope = request.default_scope
        if request.retention_preference is not None:
            settings.retention_preference = request.retention_preference
        settings.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(settings)
        return settings

    # =========================================================================
    # 5. Privacy Bulk Deletion
    # =========================================================================

    async def delete_all_project_memories(
        self,
        workspace_id: UUID,
        project_id: UUID,
        user: User,
    ) -> int:
        """Privacy control: deletes all memories associated with a project."""
        stmt = (
            delete(Memory)
            .where(
                and_(
                    Memory.workspace_id == workspace_id,
                    Memory.project_id == project_id,
                )
            )
        )
        res = await self.session.execute(stmt)
        await self.session.commit()
        count = res.rowcount or 0
        logger.info(f"[MemoryService] Deleted {count} project memories for project '{project_id}'")
        return count

    async def delete_all_workspace_memories(
        self,
        workspace_id: UUID,
        user: User,
    ) -> int:
        """Privacy control: deletes all workspace-scoped memories in this workspace."""
        stmt = (
            delete(Memory)
            .where(
                and_(
                    Memory.workspace_id == workspace_id,
                    Memory.scope == MemoryScope.WORKSPACE.value,
                )
            )
        )
        res = await self.session.execute(stmt)
        await self.session.commit()
        count = res.rowcount or 0
        logger.info(f"[MemoryService] Deleted {count} workspace memories for workspace '{workspace_id}'")
        return count
