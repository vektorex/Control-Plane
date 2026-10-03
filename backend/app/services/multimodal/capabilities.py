"""
Capability Resolver for Step 30: Multimodal AI and Unified Artifact Intelligence.
Resolves model capability requirements dynamically based on artifacts and task intent.
Feeds explicit requirements into the Model Router.
"""
import re
from typing import List, Optional, Set
from pydantic import BaseModel, Field

from backend.app.services.models.base import ModelRequirements
from backend.app.services.models.capabilities import ModelCapability
from backend.app.services.multimodal.constants import ArtifactType, MediaCapability
from backend.app.services.multimodal.models import Artifact


class CapabilityResolution(BaseModel):
    """Result of multimodal capability resolution."""
    required_capabilities: List[str] = Field(default_factory=list)
    requires_vision: bool = False
    requires_audio: bool = False
    requires_video: bool = False
    requires_table: bool = False
    requires_document: bool = False
    requires_multimodal: bool = False
    model_requirements: ModelRequirements


class CapabilityResolver:
    """
    Derives concrete, testable model capability requirements from input artifacts and task text.
    Prevents models or users from arbitrarily requesting unneeded or unavailable capabilities.
    """

    VISION_PATTERNS = [
        re.compile(r"\b(screenshot|image|photo|diagram|chart|picture|graph|visual|ui|figure|draw)\b", re.IGNORECASE),
    ]

    AUDIO_PATTERNS = [
        re.compile(r"\b(audio|recording|speech|voice|podcast|transcript|listen|sound)\b", re.IGNORECASE),
    ]

    VIDEO_PATTERNS = [
        re.compile(r"\b(video|clip|footage|mp4|webm|frames|recording)\b", re.IGNORECASE),
    ]

    TABLE_PATTERNS = [
        re.compile(r"\b(spreadsheet|csv|xlsx|excel|table|rows|columns|data\s+analysis|sheet)\b", re.IGNORECASE),
    ]

    DOCUMENT_PATTERNS = [
        re.compile(r"\b(pdf|document|docx|contract|report|manual|page)\b", re.IGNORECASE),
    ]

    @classmethod
    def resolve_for_artifacts(cls, artifacts: List[Artifact]) -> Set[str]:
        """Maps artifact types to required technical capabilities."""
        caps: Set[str] = set()
        for art in artifacts:
            t = art.artifact_type.lower()
            if t == ArtifactType.IMAGE.value:
                caps.add(MediaCapability.VISION.value)
                caps.add(MediaCapability.IMAGE_INPUT.value)
            elif t == ArtifactType.AUDIO.value:
                caps.add(MediaCapability.AUDIO_INPUT.value)
                caps.add(MediaCapability.AUDIO_TRANSCRIPTION.value)
            elif t == ArtifactType.VIDEO.value:
                caps.add(MediaCapability.VIDEO.value)
                caps.add(MediaCapability.VISION.value)
            elif t == ArtifactType.SPREADSHEET.value:
                caps.add(MediaCapability.TABLE_EXTRACTION.value)
            elif t == ArtifactType.DOCUMENT.value:
                caps.add("document_processing")
        return caps

    @classmethod
    def resolve_requirements(
        cls,
        task_text: str = "",
        artifacts: Optional[List[Artifact]] = None,
        streaming: bool = True,
        structured_output: bool = False,
    ) -> CapabilityResolution:
        """
        Determines the full capability requirements specification for model selection.
        """
        active_arts = artifacts or []
        art_caps = cls.resolve_for_artifacts(active_arts)

        # Check intent from task text
        has_vision_intent = any(p.search(task_text) for p in cls.VISION_PATTERNS)
        has_audio_intent = any(p.search(task_text) for p in cls.AUDIO_PATTERNS)
        has_video_intent = any(p.search(task_text) for p in cls.VIDEO_PATTERNS)
        has_table_intent = any(p.search(task_text) for p in cls.TABLE_PATTERNS)
        has_doc_intent = any(p.search(task_text) for p in cls.DOCUMENT_PATTERNS)

        # Resolve booleans
        req_vision = (MediaCapability.VISION.value in art_caps) or (has_vision_intent and bool(active_arts))
        req_audio = (MediaCapability.AUDIO_INPUT.value in art_caps) or has_audio_intent
        req_video = (MediaCapability.VIDEO.value in art_caps) or has_video_intent
        req_table = (MediaCapability.TABLE_EXTRACTION.value in art_caps) or has_table_intent
        req_doc = ("document_processing" in art_caps) or has_doc_intent
        req_multimodal = req_vision or req_audio or req_video or len(active_arts) > 0

        # Build list of normalized capability strings
        all_caps: Set[str] = set(art_caps)
        if req_vision:
            all_caps.add(ModelCapability.VISION.value)
        if req_multimodal:
            all_caps.add("multimodal")

        model_reqs = ModelRequirements(
            requires_vision=req_vision,
            requires_tools=False,
            requires_streaming=streaming,
            requires_structured_output=structured_output,
        )

        return CapabilityResolution(
            required_capabilities=sorted(list(all_caps)),
            requires_vision=req_vision,
            requires_audio=req_audio,
            requires_video=req_video,
            requires_table=req_table,
            requires_document=req_doc,
            requires_multimodal=req_multimodal,
            model_requirements=model_reqs,
        )
