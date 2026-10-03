import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.app.core.logging import logger
from backend.app.db.models.task import Task
from backend.app.services.context.base import ContextProvider
from backend.app.services.context.models import ContextItem, ContextSourceType
from backend.app.services.context.token_estimator import estimate_context_item_tokens
from backend.app.services.multimodal.constants import ArtifactPartType, ArtifactType
from backend.app.services.multimodal.models import Artifact, ArtifactPart
from backend.app.services.multimodal.sanitizer import MultimodalSanitizer


class MultimodalContextProvider(ContextProvider):
    """
    ContextProvider that gathers normalized artifact context (text, documents,
    images, tables, audio transcripts, video frames) and packages them as
    ContextItems into the unified ContextEngine.
    
    Adheres strictly to tenant isolation and prompt injection defenses:
    all artifact-derived text is tagged as external_untrusted.
    """

    def __init__(self) -> None:
        self.sanitizer = MultimodalSanitizer()

    @property
    def provider_id(self) -> str:
        return "multimodal_context"

    @property
    def source_type(self) -> str:
        return ContextSourceType.MULTIMODAL.value

    async def can_handle(self, task: Task, **kwargs: Any) -> bool:
        """
        Determines whether multimodal context should be collected.
        Returns True if artifact_ids are provided in kwargs or task metadata.
        """
        if not task:
            return False

        # Explicit artifact IDs passed via kwargs
        if kwargs.get("artifact_ids") or kwargs.get("artifacts"):
            return True

        # Task metadata may contain referenced artifact IDs
        meta = getattr(task, "metadata_json", None) or {}
        if meta.get("artifact_ids") or meta.get("artifacts") or meta.get("input_artifacts"):
            return True

        return False

    async def collect(
        self,
        task: Task,
        session: Optional[AsyncSession] = None,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """
        Queries authorized artifacts and their parts for the given task.
        """
        if session is None:
            return []

        # Gather target artifact IDs
        raw_ids = kwargs.get("artifact_ids") or []
        if not raw_ids and kwargs.get("artifacts"):
            raw_ids = [a.id if hasattr(a, "id") else a.get("id") for a in kwargs["artifacts"]]

        if not raw_ids:
            meta = getattr(task, "metadata_json", None) or {}
            raw_ids = meta.get("artifact_ids") or meta.get("input_artifacts") or []

        if not raw_ids:
            return []

        clean_ids = []
        for rid in raw_ids:
            try:
                clean_ids.append(uuid.UUID(str(rid)))
            except (ValueError, TypeError):
                continue

        if not clean_ids:
            return []

        # Query artifacts ensuring workspace/organization boundary
        conditions = [Artifact.id.in_(clean_ids)]
        task_org_id = getattr(task, "organization_id", None)
        if task_org_id:
            conditions.append(Artifact.organization_id == task_org_id)

        stmt = (
            select(Artifact)
            .options(selectinload(Artifact.parts))
            .where(*conditions)
        )

        res = await session.execute(stmt)
        artifacts = res.scalars().all()

        collected: List[Dict[str, Any]] = []
        for art in artifacts:
            # Respect project restriction if task is project-scoped and artifact is project-scoped
            if art.project_id and task.project_id and art.project_id != task.project_id:
                logger.warning(
                    f"[MultimodalContextProvider] Artifact {art.id} project {art.project_id} "
                    f"mismatches task project {task.project_id}. Skipping."
                )
                continue

            collected.append({
                "artifact": art,
                "parts": art.parts or [],
            })

        return collected

    def normalize(self, raw_items: List[Dict[str, Any]], **kwargs: Any) -> List[ContextItem]:
        """
        Transforms collected artifacts and their parts into normalized ContextItems.
        """
        items: List[ContextItem] = []

        for entry in raw_items:
            art: Artifact = entry["artifact"]
            parts: List[ArtifactPart] = entry.get("parts", [])

            # If artifact has parts, normalize individual parts
            if parts:
                for part in parts:
                    item = self._normalize_part(art, part)
                    if item:
                        items.append(item)
            else:
                # Top-level fallback context item for artifact without extracted parts
                art_type_str = art.artifact_type.value if hasattr(art.artifact_type, "value") else str(art.artifact_type)
                art_status_str = art.status.value if hasattr(art.status, "value") else str(art.status)
                summary = f"Multimodal Artifact: {art.filename} ({art_type_str}, {art.mime_type})"
                content = f"[Artifact {art.filename}] Type: {art_type_str} Status: {art_status_str}"
                metadata = {
                    "artifact_id": str(art.id),
                    "artifact_type": art_type_str,
                    "mime_type": art.mime_type,
                    "filename": art.filename,
                    "size_bytes": art.size_bytes,
                    "storage_reference": art.storage_reference,
                    "data_trust_level": "external_untrusted",
                    "is_untrusted_input": True,
                }
                c_item = ContextItem(
                    id=f"artifact-{art.id}",
                    source_type=self.source_type,
                    title=summary,
                    content=content,
                    metadata=metadata,
                    priority=65,
                    trust_level="external_untrusted",
                )
                c_item.token_estimate = estimate_context_item_tokens(c_item)
                items.append(c_item)

        return items

    def _normalize_part(self, art: Artifact, part: ArtifactPart) -> Optional[ContextItem]:
        """
        Normalizes a single ArtifactPart into a ContextItem according to its part_type.
        """
        pt_val = part.part_type.value if hasattr(part.part_type, "value") else str(part.part_type)
        meta = dict(part.metadata_json or {})
        meta["artifact_id"] = str(art.id)
        meta["part_id"] = str(part.id)
        meta["part_type"] = pt_val
        meta["filename"] = art.filename
        meta["data_trust_level"] = "external_untrusted"
        meta["is_untrusted_input"] = True

        raw_text = part.text_content or ""
        sanitized_text = self.sanitizer.sanitize_text(raw_text) if raw_text else ""

        if pt_val == ArtifactPartType.IMAGE.value:
            meta["media_type"] = "image"
            meta["width"] = meta.get("width")
            meta["height"] = meta.get("height")
            meta["storage_reference"] = part.content_reference
            
            title = f"Image: {art.filename} (Part #{part.sequence_number})"
            content = (
                f"[Image Reference: {art.filename}] "
                f"Dimensions: {meta.get('width')}x{meta.get('height')}. "
                + (f"Description/OCR: {sanitized_text}" if sanitized_text else "Visual artifact reference.")
            )

        elif pt_val == ArtifactPartType.TABLE.value:
            meta["media_type"] = "table"
            meta["row_count"] = meta.get("row_count", 0)
            meta["column_count"] = meta.get("column_count", 0)
            meta["columns"] = meta.get("columns", [])
            meta["source_artifact"] = str(art.id)
            meta["sheet"] = meta.get("sheet", "default")

            title = f"Table: {art.filename} ({meta['row_count']} rows x {meta['column_count']} cols)"
            content = sanitized_text or f"[Structured Table Artifact: {art.filename}]"

        elif pt_val == ArtifactPartType.AUDIO_SEGMENT.value:
            meta["media_type"] = "audio_transcript"
            meta["timestamp"] = meta.get("timestamp_label", "00:00:00")
            meta["speaker"] = meta.get("speaker")
            meta["segment_id"] = str(part.id)

            speaker_tag = f"{meta['speaker']}: " if meta.get("speaker") else ""
            title = f"Audio Transcript: {art.filename} [{meta['timestamp']}]"
            content = f"[{meta['timestamp']}] {speaker_tag}{sanitized_text}"

        elif pt_val == ArtifactPartType.VIDEO_FRAME.value:
            meta["media_type"] = "video_frame"
            meta["timestamp"] = meta.get("timestamp_label", "00:00:00")
            meta["frame_reference"] = part.content_reference

            title = f"Video Keyframe: {art.filename} at {meta['timestamp']}"
            content = (
                f"[Video Keyframe: {art.filename} @ {meta['timestamp']}] "
                + (f"Frame OCR/Analysis: {sanitized_text}" if sanitized_text else "")
            )

        elif pt_val == ArtifactPartType.TEXT.value:
            title = f"Document Section: {art.filename} (#{part.sequence_number})"
            content = sanitized_text or f"[Document Part: {art.filename}]"

        else:
            title = f"Artifact Part: {art.filename} ({pt_val})"
            content = sanitized_text or f"[{pt_val} content: {art.filename}]"

        c_item = ContextItem(
            id=f"part-{part.id}",
            source_type=self.source_type,
            title=title,
            content=content,
            metadata=meta,
            priority=75,
            trust_level="external_untrusted",
        )
        c_item.token_estimate = part.token_estimate or estimate_context_item_tokens(c_item)
        return c_item
