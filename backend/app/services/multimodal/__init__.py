"""
Step 30: Multimodal AI & Unified Artifact Intelligence layer.
"""
from backend.app.services.multimodal.constants import (
    ArtifactPartType,
    ArtifactStatus,
    ArtifactType,
    MediaCapability,
)
from backend.app.services.multimodal.models import (
    Artifact,
    ArtifactEvidence,
    ArtifactPart,
)
from backend.app.services.multimodal.schemas import (
    ArtifactAnalysisRequest,
    ArtifactAnalysisResponse,
    ArtifactCreate,
    ArtifactEvidenceItem,
    ArtifactEvidenceResponse,
    ArtifactInspection,
    ArtifactPartResponse,
    ArtifactResponse,
    TableArtifact,
)
from backend.app.services.multimodal.artifact_service import ArtifactService
from backend.app.services.multimodal.service import MultimodalService
from backend.app.services.multimodal.context_provider import MultimodalContextProvider
from backend.app.services.multimodal.media_detector import MediaDetector
from backend.app.services.multimodal.image_service import ImageService, OCRProvider
from backend.app.services.multimodal.audio_service import AudioService, AudioTranscriptionProvider
from backend.app.services.multimodal.video_service import VideoService
from backend.app.services.multimodal.table_service import TableService
from backend.app.services.multimodal.vision import VisionService
from backend.app.services.multimodal.capabilities import CapabilityResolver

__all__ = [
    "ArtifactType",
    "ArtifactStatus",
    "ArtifactPartType",
    "MediaCapability",
    "Artifact",
    "ArtifactPart",
    "ArtifactEvidence",
    "ArtifactCreate",
    "ArtifactResponse",
    "ArtifactPartResponse",
    "ArtifactEvidenceResponse",
    "ArtifactEvidenceItem",
    "ArtifactInspection",
    "TableArtifact",
    "ArtifactAnalysisRequest",
    "ArtifactAnalysisResponse",
    "ArtifactService",
    "MultimodalService",
    "MultimodalContextProvider",
    "MediaDetector",
    "ImageService",
    "OCRProvider",
    "AudioService",
    "AudioTranscriptionProvider",
    "VideoService",
    "TableService",
    "VisionService",
    "CapabilityResolver",
]
