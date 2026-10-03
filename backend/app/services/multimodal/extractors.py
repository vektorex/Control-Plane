"""
Multimodal Part Extraction Coordinator for Step 30: Multimodal AI.
Extracts normalized ArtifactParts (text, image, table, audio segment, video frame)
from raw media bytes and stores them via ArtifactRepository.
"""
import hashlib
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.services.multimodal.audio_service import AudioService
from backend.app.services.multimodal.constants import ArtifactPartType, ArtifactType
from backend.app.services.multimodal.image_service import ImageService
from backend.app.services.multimodal.limits import MULTIMODAL_MAX_PART_TOKENS
from backend.app.services.multimodal.models import Artifact, ArtifactPart
from backend.app.services.multimodal.repository import ArtifactRepository
from backend.app.services.multimodal.sanitizer import wrap_untrusted_context_metadata
from backend.app.services.multimodal.schemas import ArtifactInspection
from backend.app.services.multimodal.table_service import TableService
from backend.app.services.multimodal.video_service import VideoService
from backend.app.services.storage.factory import get_storage


class MultimodalExtractionCoordinator:
    """
    Coordinates media extraction into discrete, normalized ArtifactParts.
    Enforces tenant boundaries, storage references, and token estimation.
    """

    def __init__(
        self,
        session: AsyncSession,
        image_service: Optional[ImageService] = None,
        audio_service: Optional[AudioService] = None,
    ):
        self.session = session
        self.repo = ArtifactRepository(session)
        self.image_service = image_service or ImageService()
        self.audio_service = audio_service or AudioService()
        self.storage = get_storage()

    async def extract_parts(
        self,
        artifact: Artifact,
        data: bytes,
        inspection: ArtifactInspection,
    ) -> List[ArtifactPart]:
        """
        Dispatches media data to the appropriate specialized extractor.
        """
        t = artifact.artifact_type.lower()
        parts: List[ArtifactPart] = []

        if t == ArtifactType.IMAGE.value:
            parts = await self._extract_image_parts(artifact, data, inspection)
        elif t == ArtifactType.SPREADSHEET.value:
            parts = await self._extract_table_parts(artifact, data, inspection)
        elif t == ArtifactType.AUDIO.value:
            parts = await self._extract_audio_parts(artifact, data, inspection)
        elif t == ArtifactType.VIDEO.value:
            parts = await self._extract_video_parts(artifact, data, inspection)
        elif t in (ArtifactType.DOCUMENT.value, ArtifactType.TEXT.value):
            parts = await self._extract_document_parts(artifact, data, inspection)
        else:
            # Fallback unknown or binary
            part = await self.repo.create_part(
                artifact_id=artifact.id,
                part_type=ArtifactPartType.STRUCTURED_DATA.value,
                sequence_number=0,
                content_reference=artifact.storage_reference,
                text_content=f"Artifact {artifact.filename} ({artifact.mime_type})",
                metadata=wrap_untrusted_context_metadata(artifact.metadata_, str(artifact.id)),
                content_hash=artifact.content_hash,
                token_estimate=10,
            )
            parts.append(part)

        await self._link_vectors_and_graph(artifact, parts)
        return parts

    async def _link_vectors_and_graph(self, artifact: Artifact, parts: List[ArtifactPart]) -> None:
        """
        Embeds textual parts and produces graph entities/relationships
        with source attribution without storing raw binary data in the graph.
        """
        try:
            from backend.app.services.embeddings.factory import get_embedding_provider
            emb_provider = get_embedding_provider()
            for part in parts:
                if part.text_content and len(part.text_content.strip()) > 20:
                    try:
                        vector = await emb_provider.embed_text(part.text_content[:1000])
                        if vector and part.metadata_json is not None:
                            part.metadata_json["has_embedding"] = True
                            part.metadata_json["embedding_dim"] = len(vector)
                    except Exception as e:
                        logger.debug(f"[MultimodalExtractor] Vector embedding skipped for part {part.id}: {e}")

            from backend.app.services.knowledge_graph.repository import GraphRepository
            graph_repo = GraphRepository(self.session)
            source_ref = {
                "artifact_id": str(artifact.id),
                "filename": artifact.filename,
                "mime_type": artifact.mime_type,
            }
            art_entity = await graph_repo.create_entity(
                organization_id=artifact.organization_id,
                workspace_id=artifact.workspace_id,
                project_id=artifact.project_id,
                entity_type="artifact",
                canonical_name=artifact.filename,
                description=f"Multimodal {artifact.artifact_type.value} artifact ({artifact.mime_type})",
                properties={"artifact_id": str(artifact.id), "artifact_type": artifact.artifact_type.value},
                source_references=[source_ref],
            )

            for part in parts:
                if part.part_type == ArtifactPartType.TABLE:
                    tbl_ent = await graph_repo.create_entity(
                        organization_id=artifact.organization_id,
                        workspace_id=artifact.workspace_id,
                        project_id=artifact.project_id,
                        entity_type="table",
                        canonical_name=f"Table in {artifact.filename}",
                        description=part.text_content[:200] if part.text_content else "Structured table",
                        source_references=[source_ref],
                    )
                    await graph_repo.create_relationship(
                        organization_id=artifact.organization_id,
                        workspace_id=artifact.workspace_id,
                        project_id=artifact.project_id,
                        source_entity_id=art_entity.id,
                        target_entity_id=tbl_ent.id,
                        relationship_type="contains",
                        source_references=[source_ref],
                    )
                elif part.part_type == ArtifactPartType.AUDIO_SEGMENT and part.text_content:
                    spk = part.metadata_json.get("speaker") if part.metadata_json else None
                    if spk:
                        spk_ent = await graph_repo.create_entity(
                            organization_id=artifact.organization_id,
                            workspace_id=artifact.workspace_id,
                            project_id=artifact.project_id,
                            entity_type="person",
                            canonical_name=str(spk),
                            source_references=[source_ref],
                        )
                        await graph_repo.create_relationship(
                            organization_id=artifact.organization_id,
                            workspace_id=artifact.workspace_id,
                            project_id=artifact.project_id,
                            source_entity_id=art_entity.id,
                            target_entity_id=spk_ent.id,
                            relationship_type="references",
                            source_references=[source_ref],
                        )
        except Exception as e:
            logger.debug(f"[MultimodalExtractor] Knowledge graph linking skipped: {e}")

    async def _extract_image_parts(
        self,
        artifact: Artifact,
        data: bytes,
        inspection: ArtifactInspection,
    ) -> List[ArtifactPart]:
        """Extracts image representation and bounded OCR text if available."""
        parts: List[ArtifactPart] = []
        meta = wrap_untrusted_context_metadata(
            {
                "width": inspection.dimensions.get("width") if inspection.dimensions else 800,
                "height": inspection.dimensions.get("height") if inspection.dimensions else 600,
                "mime_type": artifact.mime_type,
            },
            str(artifact.id),
            media_type="image",
        )

        # 1. Image part
        p1 = await self.repo.create_part(
            artifact_id=artifact.id,
            part_type=ArtifactPartType.IMAGE.value,
            sequence_number=0,
            content_reference=artifact.storage_reference,
            text_content=None,
            metadata=meta,
            content_hash=artifact.content_hash,
            token_estimate=300,  # Standard token estimate for image vision tile
        )
        parts.append(p1)

        # 2. Optional OCR part if provider available
        try:
            ocr_text = await self.image_service.extract_ocr(data)
            if ocr_text:
                ocr_meta = wrap_untrusted_context_metadata(
                    {"source": "ocr_extraction"},
                    str(artifact.id),
                    str(p1.id),
                    media_type="text",
                )
                p2 = await self.repo.create_part(
                    artifact_id=artifact.id,
                    part_type=ArtifactPartType.TEXT.value,
                    sequence_number=1,
                    text_content=ocr_text,
                    metadata=ocr_meta,
                    content_hash=hashlib.sha256(ocr_text.encode("utf-8")).hexdigest(),
                    token_estimate=min(len(ocr_text) // 4, MULTIMODAL_MAX_PART_TOKENS),
                )
                parts.append(p2)
        except Exception as e:
            logger.info(f"[MultimodalExtractor] OCR extraction skipped for {artifact.filename}: {e}")

        return parts

    async def _extract_table_parts(
        self,
        artifact: Artifact,
        data: bytes,
        inspection: ArtifactInspection,
    ) -> List[ArtifactPart]:
        """Extracts structured table artifact, schema summary, and bounded rows."""
        parts: List[ArtifactPart] = []

        if artifact.mime_type == "text/csv":
            table = TableService.extract_from_csv(data, source_reference=artifact.storage_reference)
        else:
            table = TableService.extract_from_xlsx(data, source_reference=artifact.storage_reference)

        # 1. Summary part
        schema_summary = TableService.generate_schema_summary(table)
        meta_summary = wrap_untrusted_context_metadata(
            {
                "row_count": table.row_count,
                "column_count": table.column_count,
                "columns": table.columns,
                "sheet": table.sheet_name,
            },
            str(artifact.id),
            media_type="table_schema",
        )
        p1 = await self.repo.create_part(
            artifact_id=artifact.id,
            part_type=ArtifactPartType.STRUCTURED_DATA.value,
            sequence_number=0,
            text_content=schema_summary,
            metadata=meta_summary,
            token_estimate=len(schema_summary) // 4,
        )
        parts.append(p1)

        # 2. Bounded Markdown table part
        rendered_md = TableService.format_markdown_table(table, max_display_rows=30)
        meta_table = wrap_untrusted_context_metadata(
            {"display_rows": min(30, table.row_count)},
            str(artifact.id),
            str(p1.id),
            media_type="table",
        )
        p2 = await self.repo.create_part(
            artifact_id=artifact.id,
            part_type=ArtifactPartType.TABLE.value,
            sequence_number=1,
            text_content=rendered_md,
            metadata=meta_table,
            token_estimate=min(len(rendered_md) // 4, MULTIMODAL_MAX_PART_TOKENS),
        )
        parts.append(p2)

        return parts

    async def _extract_audio_parts(
        self,
        artifact: Artifact,
        data: bytes,
        inspection: ArtifactInspection,
    ) -> List[ArtifactPart]:
        """Extracts audio metadata and transcript segments."""
        parts: List[ArtifactPart] = []

        meta = self.audio_service.extract_audio_metadata(data, artifact.mime_type)
        safe_meta = wrap_untrusted_context_metadata(meta, str(artifact.id), media_type="audio")

        # 1. Audio reference part
        p1 = await self.repo.create_part(
            artifact_id=artifact.id,
            part_type=ArtifactPartType.AUDIO_SEGMENT.value,
            sequence_number=0,
            content_reference=artifact.storage_reference,
            text_content=f"Audio Recording ({meta.get('duration_seconds', 0.0)}s)",
            metadata=safe_meta,
            content_hash=artifact.content_hash,
            token_estimate=50,
        )
        parts.append(p1)

        # 2. Optional transcription part
        try:
            segments = await self.audio_service.transcribe_audio(data, artifact.mime_type)
            if segments:
                formatted_transcript = AudioService.format_transcript_context(segments)
                t_meta = wrap_untrusted_context_metadata(
                    {"segment_count": len(segments)},
                    str(artifact.id),
                    str(p1.id),
                    media_type="transcript",
                )
                p2 = await self.repo.create_part(
                    artifact_id=artifact.id,
                    part_type=ArtifactPartType.TEXT.value,
                    sequence_number=1,
                    text_content=formatted_transcript,
                    metadata=t_meta,
                    token_estimate=min(len(formatted_transcript) // 4, MULTIMODAL_MAX_PART_TOKENS),
                )
                parts.append(p2)
        except Exception as e:
            logger.info(f"[MultimodalExtractor] Transcription skipped for {artifact.filename}: {e}")

        return parts

    async def _extract_video_parts(
        self,
        artifact: Artifact,
        data: bytes,
        inspection: ArtifactInspection,
    ) -> List[ArtifactPart]:
        """Extracts bounded keyframes from video."""
        parts: List[ArtifactPart] = []
        meta = VideoService.extract_video_metadata(data, artifact.mime_type)
        safe_meta = wrap_untrusted_context_metadata(meta, str(artifact.id), media_type="video")

        # 1. Video root part
        p_root = await self.repo.create_part(
            artifact_id=artifact.id,
            part_type=ArtifactPartType.STRUCTURED_DATA.value,
            sequence_number=0,
            content_reference=artifact.storage_reference,
            text_content=f"Video Asset: {artifact.filename} ({meta.get('duration_seconds', 0.0)}s)",
            metadata=safe_meta,
            content_hash=artifact.content_hash,
            token_estimate=50,
        )
        parts.append(p_root)

        # 2. Extract and persist sampled keyframes
        frames = VideoService.extract_keyframes(data, duration_seconds=meta.get("duration_seconds"))
        for idx, f in enumerate(frames):
            frame_key = f"artifacts/{artifact.id}/frames/frame_{idx:03d}.jpg"
            await self.storage.upload(frame_key, f.image_bytes, "image/jpeg")

            f_meta = wrap_untrusted_context_metadata(
                {"timestamp": f.timestamp, "frame_index": f.frame_index},
                str(artifact.id),
                str(p_root.id),
                media_type="video_frame",
            )
            part_frame = await self.repo.create_part(
                artifact_id=artifact.id,
                part_type=ArtifactPartType.VIDEO_FRAME.value,
                sequence_number=idx + 1,
                content_reference=frame_key,
                text_content=f"Frame at {f.timestamp:.1f}s",
                metadata=f_meta,
                token_estimate=300,
            )
            parts.append(part_frame)

        return parts

    async def _extract_document_parts(
        self,
        artifact: Artifact,
        data: bytes,
        inspection: ArtifactInspection,
    ) -> List[ArtifactPart]:
        """Extracts raw text representation from documents or markdown."""
        parts: List[ArtifactPart] = []
        text = ""
        try:
            text = data.decode("utf-8", errors="replace")
        except Exception:
            text = f"Document content ({len(data)} bytes)"

        doc_meta = wrap_untrusted_context_metadata(
            {"page_count": inspection.page_count or 1, "mime_type": artifact.mime_type},
            str(artifact.id),
            media_type="document",
        )
        part = await self.repo.create_part(
            artifact_id=artifact.id,
            part_type=ArtifactPartType.TEXT.value,
            sequence_number=0,
            content_reference=artifact.storage_reference,
            text_content=text,
            metadata=doc_meta,
            content_hash=artifact.content_hash,
            token_estimate=min(len(text) // 4, MULTIMODAL_MAX_PART_TOKENS),
        )
        parts.append(part)
        return parts


ArtifactExtractor = MultimodalExtractionCoordinator

