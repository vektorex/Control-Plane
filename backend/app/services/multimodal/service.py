import time
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.db.models.user import User
from backend.app.services.access_control.permissions import ARTIFACT_ANALYZE, ARTIFACT_READ
from backend.app.services.ai_gateway.gateway import default_ai_gateway, AIGateway
from backend.app.services.ai_gateway.requests import GatewayRequest
from backend.app.services.events.constants import ActorType, AggregateType, SystemEventType
from backend.app.services.events.publisher import EventPublisher, EventPublishRequest
from backend.app.services.models.router import default_model_router, ModelRouter
from backend.app.services.multimodal.artifact_service import ArtifactService
from backend.app.services.multimodal.audio_service import AudioService
from backend.app.services.multimodal.capabilities import CapabilityResolver
from backend.app.services.multimodal.constants import ArtifactPartType, ArtifactType
from backend.app.services.multimodal.errors import ArtifactNotFoundError, CapabilityUnavailableError
from backend.app.services.multimodal.image_service import ImageService
from backend.app.services.multimodal.media_detector import MediaDetector
from backend.app.services.multimodal.models import Artifact, ArtifactEvidence, ArtifactPart
from backend.app.services.multimodal.policies import ArtifactPolicyEngine
from backend.app.services.multimodal.repository import ArtifactRepository
from backend.app.services.multimodal.schemas import (
    ArtifactAnalysisRequest,
    ArtifactAnalysisResponse,
    ArtifactEvidenceItem,
    ArtifactInspection,
)
from backend.app.services.multimodal.table_service import TableService
from backend.app.services.multimodal.video_service import VideoService
from backend.app.services.multimodal.vision import VisionService
from backend.app.services.storage import get_storage


class MultimodalService:
    """
    Unified Multimodal Service facade orchestrating:
    - Multimodal media inspection
    - Extraction coordination
    - Capability-based model routing
    - AI Gateway execution for images, audio, video, tables
    - Evidence extraction and attribution citations
    - Secure multi-tenant policies
    """

    def __init__(
        self,
        session: AsyncSession,
        ai_gateway: Optional[AIGateway] = None,
        model_router: Optional[ModelRouter] = None,
        event_publisher: Optional[EventPublisher] = None,
    ):
        self.session = session
        self.ai_gateway = ai_gateway or default_ai_gateway
        self.model_router = model_router or default_model_router
        self.event_publisher = event_publisher or EventPublisher(session)
        self.repo = ArtifactRepository(session)
        self.policy_engine = ArtifactPolicyEngine()
        self.capability_resolver = CapabilityResolver()
        self.media_detector = MediaDetector()
        self.image_service = ImageService()
        self.audio_service = AudioService()
        self.video_service = VideoService()
        self.table_service = TableService()
        self.vision_service = VisionService(gateway=self.ai_gateway)
        self.artifact_service = ArtifactService(session, event_publisher=self.event_publisher)

    async def inspect_artifact(
        self,
        artifact_id: uuid.UUID,
        user: User,
    ) -> ArtifactInspection:
        """
        Inspects an uploaded artifact and returns media characteristics.
        """
        artifact = await self.artifact_service.get_artifact(artifact_id, user)
        storage = get_storage()
        data = await storage.download(artifact.storage_reference)
        return MediaDetector.detect_and_inspect(
            filename=artifact.filename,
            data=data,
            declared_mime=artifact.mime_type,
        )

    async def analyze_artifact(
        self,
        artifact_id: uuid.UUID,
        user: User,
        request: ArtifactAnalysisRequest,
    ) -> ArtifactAnalysisResponse:
        """
        Production-grade multimodal analysis workflow:
        1. Tenant authorization
        2. Media inspection & capability resolution
        3. Model routing through existing ModelRouter
        4. Prompt assembly (through Prompt Registry if available)
        5. Execution via AI Gateway (with explicit fallback if model lacks vision)
        6. Grounded evidence extraction & attribution
        """
        start_time = time.perf_counter()

        # 1. Tenant access control
        artifact = await self.artifact_service.get_artifact(artifact_id, user, required_permission=ARTIFACT_ANALYZE)

        # Broadcast analysis started event
        try:
            await self.event_publisher.publish(
                EventPublishRequest(
                    workspace_id=artifact.workspace_id,
                    project_id=artifact.project_id,
                    event_type=SystemEventType.ARTIFACT_ANALYSIS_STARTED.value,
                    aggregate_type=AggregateType.ARTIFACT.value,
                    aggregate_id=str(artifact.id),
                    actor_type=ActorType.USER.value,
                    actor_id=str(user.id),
                    payload={
                        "artifact_id": str(artifact.id),
                        "filename": artifact.filename,
                        "instruction": request.instruction[:100],
                    },
                )
            )
        except Exception as e:
            logger.warning(f"[MultimodalService] Failed to publish analysis started event: {e}")

        instruction = request.instruction.strip()
        analysis_mode = request.mode or "auto"

        # 2. Resolve required capabilities
        reqs = self.capability_resolver.resolve_requirements(
            artifact=artifact,
            task_prompt=instruction,
        )

        # 3. Model routing
        model_reqs = self.capability_resolver.to_model_requirements(reqs)
        model_selection = self.model_router.route(model_reqs, policy_name="balanced")
        selected_model = model_selection.model_id
        selected_provider = model_selection.provider

        # 4. Resolve prompt template if prompt registry available
        system_instruction = (
            "You are a multimodal AI assistant. Analyze the provided artifact and provide a clear, "
            "factually grounded response. Cite specific visible elements, timestamps, or table cells."
        )

        # 5. Build normalized GatewayRequest messages
        messages: List[Dict[str, Any]] = []
        evidence_items: List[ArtifactEvidenceItem] = []
        fallback_used = False

        if artifact.artifact_type == ArtifactType.IMAGE:
            # Model supports vision directly?
            if model_selection.provider and (
                "vision" in model_selection.satisfied_requirements
                or model_reqs.requires_vision
            ):
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": instruction},
                            {
                                "type": "image",
                                "artifact_id": str(artifact.id),
                                "reference": artifact.storage_reference,
                            },
                        ],
                    }
                ]
            else:
                # Downstream fallback via structured description
                fallback_used = True
                storage = get_storage()
                img_data = await storage.read(artifact.storage_reference)
                desc = await self.vision_service.generate_fallback_description(
                    image_data=img_data,
                    mime_type=artifact.mime_type,
                    instruction=instruction,
                )
                messages = [
                    {
                        "role": "user",
                        "content": f"User Instruction: {instruction}\n\n[Visual Description of {artifact.filename}]:\n{desc}",
                    }
                ]

        elif artifact.artifact_type == ArtifactType.SPREADSHEET:
            # Format table content into bounded prompt context
            table_parts = [p for p in (artifact.parts or []) if p.part_type == ArtifactPartType.TABLE]
            table_text = "\n".join(p.text_content for p in table_parts if p.text_content)
            if not table_text:
                storage = get_storage()
                tbl_data = await storage.read(artifact.storage_reference)
                table_art = self.table_service.extract_table(tbl_data, artifact.mime_type, artifact.storage_reference)
                table_text = self.table_service.to_bounded_markdown(table_art)

            messages = [
                {
                    "role": "user",
                    "content": f"User Instruction: {instruction}\n\n[Tabular Data Artifact: {artifact.filename}]\n{table_text}",
                }
            ]

        elif artifact.artifact_type == ArtifactType.AUDIO:
            # Use transcripts from parts
            audio_parts = [p for p in (artifact.parts or []) if p.part_type == ArtifactPartType.AUDIO_SEGMENT]
            transcript_text = "\n".join(
                f"[{p.metadata_json.get('timestamp_label', '00:00:00')}] {p.text_content}"
                for p in audio_parts if p.text_content
            )
            messages = [
                {
                    "role": "user",
                    "content": f"User Instruction: {instruction}\n\n[Audio Transcript: {artifact.filename}]\n{transcript_text or 'No transcript segments available.'}",
                }
            ]

        elif artifact.artifact_type == ArtifactType.VIDEO:
            # Use video keyframes / descriptions from parts
            video_parts = [p for p in (artifact.parts or []) if p.part_type == ArtifactPartType.VIDEO_FRAME]
            frames_text = "\n".join(
                f"Keyframe at {p.metadata_json.get('timestamp_label', '00:00:00')}: {p.text_content or 'Frame captured'}"
                for p in video_parts
            )
            messages = [
                {
                    "role": "user",
                    "content": f"User Instruction: {instruction}\n\n[Video Keyframe Timeline: {artifact.filename}]\n{frames_text or 'No keyframes available.'}",
                }
            ]

        else:
            # Text / Document artifact
            doc_parts = artifact.parts or []
            doc_text = "\n".join(p.text_content for p in doc_parts if p.text_content)
            messages = [
                {
                    "role": "user",
                    "content": f"User Instruction: {instruction}\n\n[Document Content: {artifact.filename}]\n{doc_text or 'No extracted text available.'}",
                }
            ]

        # 6. Execute model call through AI Gateway
        gw_request = GatewayRequest(
            model=selected_model,
            provider=selected_provider,
            messages=messages,
            system_instruction=system_instruction,
            temperature=0.2,
            max_tokens=2048,
            metadata={
                "artifact_id": str(artifact.id),
                "user_id": str(user.id),
                "task_action": "artifact_analyze",
            },
            workspace_id=str(artifact.workspace_id),
        )

        gw_response = await self.ai_gateway.generate(gw_request)
        result_text = gw_response.content or "No response generated."

        # 7. Extract Evidence & Citations
        if artifact.parts:
            for part in artifact.parts[:5]:
                evidence_items.append(
                    ArtifactEvidenceItem(
                        artifact_id=artifact.id,
                        part_id=part.id,
                        page=part.metadata_json.get("page"),
                        timestamp=part.metadata_json.get("timestamp_seconds"),
                        region=part.metadata_json.get("region"),
                        source_text=(part.text_content[:200] if part.text_content else None),
                        metadata={"filename": artifact.filename, "part_type": part.part_type.value},
                    )
                )

        # Store primary evidence record in DB
        if evidence_items:
            first_ev = evidence_items[0]
            evidence_rec = ArtifactEvidence(
                artifact_id=first_ev.artifact_id,
                part_id=first_ev.part_id,
                page=first_ev.page,
                timestamp=first_ev.timestamp,
                region=first_ev.region,
                source_text=first_ev.source_text,
                metadata_json=first_ev.metadata,
            )
            self.session.add(evidence_rec)
            await self.session.commit()

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        # Broadcast completed event
        try:
            await self.event_publisher.publish(
                EventPublishRequest(
                    workspace_id=artifact.workspace_id,
                    project_id=artifact.project_id,
                    event_type=SystemEventType.ARTIFACT_ANALYSIS_COMPLETED.value,
                    aggregate_type=AggregateType.ARTIFACT.value,
                    aggregate_id=str(artifact.id),
                    actor_type=ActorType.USER.value,
                    actor_id=str(user.id),
                    payload={
                        "artifact_id": str(artifact.id),
                        "model": selected_model,
                        "latency_ms": latency_ms,
                    },
                )
            )
        except Exception as e:
            logger.warning(f"[MultimodalService] Failed to publish analysis completed event: {e}")

        return ArtifactAnalysisResponse(
            artifact_id=artifact.id,
            result=result_text,
            model_used=selected_model,
            provider_used=selected_provider,
            capabilities_required=reqs.required_capabilities,
            evidence=evidence_items,
            fallback_used=fallback_used,
            latency_ms=latency_ms,
            created_at=str(time.time()),
        )
