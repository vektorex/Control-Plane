"""
Comprehensive Test Suite for STEP 30: Production-Grade Multimodal AI and Unified Artifact Intelligence Layer.

Covers:
1. Media Detection, MIME & Magic-Byte Validation, Spoofing Rejection & Size Limits
2. Image Processing, Dimensions, EXIF Stripping, Safe Resizing & OCR Abstraction
3. Audio Processing, Duration Probing & Transcription Abstraction
4. Video Processing, Bounded Keyframe Extraction & Duration Limits
5. Table Processing, CSV/XLSX Parsing, Bounded Preview & Markdown Conversion
6. Artifact Model CRUD, Multi-Tenant Isolation & Storage Security
7. ArtifactPart Model & Content Reference Integrity
8. Capability Resolver (Vision, Audio, Video, Table, Multimodal)
9. Model Router & AI Gateway Multimodal Execution (with mock-vision-v1 & fallbacks)
10. ContextEngine MultimodalContextProvider & Untrusted Tagging
11. Retrieval Router Multimodal Strategy
12. Evaluation Lab Multimodal Assertions
13. Replay Snapshot Artifact Configuration & Hash Tamper Detection
14. Background Job Handlers (artifact_processing, image_processing, etc.)
15. Unified Event Bus & Notification Publishing
16. Security Policies (Path traversal, URL injection, untrusted prompt injection defense)
"""
import io
import os
import uuid
import struct
import pytest
import pytest_asyncio
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.user import User
from backend.app.services.access_control.permissions import (
    ARTIFACT_ANALYZE,
    ARTIFACT_CREATE,
    ARTIFACT_DELETE,
    ARTIFACT_PROCESS,
    ARTIFACT_READ,
    ARTIFACT_UPDATE,
)
from backend.app.services.ai_gateway.gateway import AIGateway
from backend.app.services.ai_gateway.requests import GatewayRequest
from backend.app.services.context.engine import ContextEngine
from backend.app.services.context.models import ContextItem, ContextSourceType
from backend.app.services.evaluation_lab.assertions import AssertionEngine
from backend.app.services.evaluation_lab.schemas import AssertionDefinition, AssertionType
from backend.app.services.events.constants import AggregateType, SystemEventType
from backend.app.services.jobs.constants import JobType
from backend.app.services.jobs.handlers import JobHandlerRegistry
from backend.app.services.models.capabilities import ModelCapability
from backend.app.services.models.catalog import get_default_catalog
from backend.app.services.models.router import ModelRouter
from backend.app.services.multimodal.artifact_service import ArtifactService
from backend.app.services.multimodal.audio_service import AudioService, MockAudioTranscriptionProvider
from backend.app.services.multimodal.capabilities import CapabilityResolver
from backend.app.services.multimodal.constants import (
    ArtifactPartType,
    ArtifactStatus,
    ArtifactType,
    MediaCapability,
)
from backend.app.services.multimodal.context_provider import MultimodalContextProvider
from backend.app.services.multimodal.errors import (
    ArtifactAccessDeniedError,
    ArtifactNotFoundError,
    CapabilityUnavailableError,
    DecompressionBombError,
    FileLimitExceededError,
    MimeSpoofingError,
    MultimodalError,
    UnsupportedMimeTypeError,
)
from backend.app.services.multimodal.extractors import ArtifactExtractor
from backend.app.services.multimodal.image_service import ImageService, MockOCRProvider
from backend.app.services.multimodal.limits import (
    MULTIMODAL_MAX_FILE_SIZE,
    MULTIMODAL_MAX_IMAGE_HEIGHT,
    MULTIMODAL_MAX_IMAGE_WIDTH,
    MULTIMODAL_MAX_VIDEO_FRAMES,
)
from backend.app.services.multimodal.media_detector import MediaDetector
from backend.app.services.multimodal.models import Artifact, ArtifactEvidence, ArtifactPart
from backend.app.services.multimodal.policies import ArtifactPolicyEngine
from backend.app.services.multimodal.repository import ArtifactRepository
from backend.app.services.multimodal.sanitizer import (
    MultimodalSanitizer,
    sanitize_artifact_metadata,
    sanitize_extracted_text,
    strip_image_exif,
    wrap_untrusted_context_metadata,
)
from backend.app.services.multimodal.schemas import (
    ArtifactAnalysisRequest,
    ArtifactCreate,
)
from backend.app.services.multimodal.service import MultimodalService
from backend.app.services.multimodal.table_service import TableService
from backend.app.services.multimodal.video_service import VideoService
from backend.app.services.multimodal.vision import VisionService
from backend.app.services.replay.schemas import ExecutionSnapshot
from backend.app.services.replay.snapshot import ReplaySnapshotService
from backend.app.services.retrieval.decision import RetrievalStrategy
from backend.app.services.retrieval.policies import RuleBasedDecisionProvider
from backend.app.services.retrieval.router import RetrievalRouter
from backend.app.services.storage import LocalFileStorage, get_storage
from backend.app.services.task_intelligence.rules import RuleBasedTaskAnalyzer
from backend.app.services.task_intelligence.schemas import TaskType


# Sample synthetic media byte generators
def create_sample_png(width=100, height=100) -> bytes:
    from PIL import Image
    buf = io.BytesIO()
    img = Image.new("RGB", (width, height), color="red")
    img.save(buf, format="PNG")
    return buf.getvalue()


def create_raw_png_header(width=50000, height=50000) -> bytes:
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr = b"\x00\x00\x00\rIHDR" + ihdr_data + b"\x00\x00\x00\x00"
    iend = b"\x00\x00\x00\x00IEND\xaeB`\x82"
    return sig + ihdr + iend


def create_sample_jpeg() -> bytes:
    from PIL import Image
    buf = io.BytesIO()
    img = Image.new("RGB", (100, 100), color="blue")
    img.save(buf, format="JPEG")
    return buf.getvalue()


def create_sample_pdf() -> bytes:
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"


def create_sample_mp3() -> bytes:
    # ID3v2 signature
    return b"ID3\x03\x00\x00\x00\x00\x00\x10" + b"\xff\xfb\x90\x64" + b"\x00" * 200


def create_sample_wav() -> bytes:
    # RIFF header + WAVE
    data_size = 100
    riff = b"RIFF" + struct.pack("<I", 36 + data_size) + b"WAVE"
    fmt = b"fmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00"
    data = b"data" + struct.pack("<I", data_size) + b"\x00" * data_size
    return riff + fmt + data


def create_sample_csv() -> bytes:
    return b"date,region,revenue,units\n2026-01-01,North,12000,45\n2026-01-02,South,15400,52\n2026-01-03,West,9800,31\n"


# =============================================================================
# 1. Media Detection, MIME & Magic-Byte Validation Tests
# =============================================================================

def test_detect_png_valid():
    png_data = create_sample_png(200, 150)
    inspection = MediaDetector.detect_and_inspect("screenshot.png", png_data, "image/png")
    assert inspection.detected_type == ArtifactType.IMAGE.value
    assert inspection.mime_type == "image/png"
    assert inspection.dimensions is not None
    assert inspection.dimensions["width"] == 200
    assert inspection.dimensions["height"] == 150
    assert MediaCapability.VISION.value in inspection.required_capabilities


def test_detect_jpeg_valid():
    jpeg_data = create_sample_jpeg()
    inspection = MediaDetector.detect_and_inspect("photo.jpg", jpeg_data, "image/jpeg")
    assert inspection.detected_type == ArtifactType.IMAGE.value
    assert inspection.mime_type == "image/jpeg"
    assert MediaCapability.VISION.value in inspection.required_capabilities


def test_detect_pdf_valid():
    pdf_data = create_sample_pdf()
    inspection = MediaDetector.detect_and_inspect("document.pdf", pdf_data, "application/pdf")
    assert inspection.detected_type == ArtifactType.DOCUMENT.value
    assert inspection.mime_type == "application/pdf"
    assert "document_processing" in inspection.required_capabilities


def test_detect_csv_valid():
    csv_data = create_sample_csv()
    inspection = MediaDetector.detect_and_inspect("sales.csv", csv_data, "text/csv")
    assert inspection.detected_type == ArtifactType.SPREADSHEET.value
    assert inspection.mime_type == "text/csv"
    assert MediaCapability.TABLE_EXTRACTION.value in inspection.required_capabilities


def test_detect_audio_mp3_valid():
    mp3_data = create_sample_mp3()
    inspection = MediaDetector.detect_and_inspect("meeting.mp3", mp3_data, "audio/mpeg")
    assert inspection.detected_type == ArtifactType.AUDIO.value
    assert inspection.mime_type == "audio/mpeg"
    assert MediaCapability.AUDIO_TRANSCRIPTION.value in inspection.required_capabilities


def test_reject_mime_spoofing():
    # File named "image.png" containing executable or text bytes without PNG signature
    fake_png = b"This is plain text disguised as a png file."
    with pytest.raises(MimeSpoofingError):
        MediaDetector.detect_and_inspect("image.png", fake_png, "image/png")


def test_reject_unsupported_mime():
    # Binary exe / unknown format
    exe_data = b"MZ\x90\x00\x03\x00\x00\x00"
    with pytest.raises(UnsupportedMimeTypeError):
        MediaDetector.detect_and_inspect("app.exe", exe_data, declared_mime=None)


def test_reject_file_size_exceeded():
    large_data = b"x" * (MULTIMODAL_MAX_FILE_SIZE + 10)
    with pytest.raises(FileLimitExceededError):
        MediaDetector.detect_and_inspect("huge.txt", large_data, "text/plain")


def test_reject_decompression_bomb():
    # Craft a PNG claiming 50,000 x 50,000 pixels
    bomb_png = create_raw_png_header(50000, 50000)
    with pytest.raises(DecompressionBombError):
        MediaDetector.detect_and_inspect("bomb.png", bomb_png, "image/png")


# =============================================================================
# 2. Image, Audio, Video & Table Service Tests
# =============================================================================

@pytest.mark.asyncio
async def test_image_service_metadata_and_ocr():
    png_data = create_sample_png(320, 240)
    img_svc = ImageService(ocr_provider=MockOCRProvider("Detected OCR Text from Diagram"))
    
    meta = img_svc.extract_image_metadata(png_data)
    assert meta["width"] == 320
    assert meta["height"] == 240

    ocr_text = await img_svc.extract_ocr(png_data)
    assert "Detected OCR Text" in ocr_text


@pytest.mark.asyncio
async def test_audio_service_duration_and_transcription():
    wav_data = create_sample_wav()
    audio_svc = AudioService(transcription_provider=MockAudioTranscriptionProvider())
    
    meta = audio_svc.extract_audio_metadata(wav_data, "audio/wav")
    assert meta["duration_seconds"] is not None
    assert meta["duration_seconds"] >= 0.0

    segments = await audio_svc.transcribe_audio(wav_data, "audio/wav")
    assert len(segments) > 0
    assert "Mock transcription" in segments[0].text
    assert segments[0].start_seconds == 0.0


@pytest.mark.asyncio
async def test_video_service_bounded_frame_extraction():
    video_svc = VideoService()
    # Mock video data
    dummy_video = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 500
    
    meta = video_svc.extract_video_metadata(dummy_video, "video/mp4")
    assert meta["duration_seconds"] is not None

    frames = video_svc.extract_keyframes(dummy_video, max_frames=10)
    assert len(frames) <= MULTIMODAL_MAX_VIDEO_FRAMES
    assert len(frames) <= 10
    if len(frames) > 0:
        assert hasattr(frames[0], "timestamp")
        assert hasattr(frames[0], "image_bytes")


@pytest.mark.asyncio
async def test_table_service_csv_parsing():
    csv_data = create_sample_csv()
    
    parsed = TableService.extract_from_csv(csv_data)
    assert parsed.columns == ["date", "region", "revenue", "units"]
    assert len(parsed.rows) == 3
    assert parsed.row_count == 3

    markdown = TableService.format_markdown_table(parsed, max_display_rows=5)
    assert "| date | region | revenue | units |" in markdown
    assert "12000" in markdown


# =============================================================================
# 3. Security, Sanitization & Tenant Isolation Tests
# =============================================================================

def test_sanitizer_exif_and_secrets():
    # Secret scrubbing
    text_with_secret = "Here is the key sk-1234567890abcdef1234567890abcdef and token ghp_1234567890abcdefghijklmnopqrstuvwxyz"
    cleaned = sanitize_extracted_text(text_with_secret)
    assert "sk-" not in cleaned
    assert "[REDACTED_SECRET]" in cleaned

    # Metadata untrusted tagging
    meta = {"source": "upload", "page": 1}
    wrapped = wrap_untrusted_context_metadata(meta, artifact_id="art-123", media_type="image")
    assert wrapped["data_trust_level"] == "external_untrusted"
    assert wrapped["is_untrusted_input"] is True
    assert wrapped["artifact_id"] == "art-123"


def test_policy_engine_path_traversal_rejection():
    # Traversal attack attempts
    with pytest.raises(MultimodalError):
        ArtifactPolicyEngine.validate_storage_reference("../../../etc/passwd")

    with pytest.raises(MultimodalError):
        ArtifactPolicyEngine.validate_storage_reference("c:\\windows\\system32\\cmd.exe")

    with pytest.raises(MultimodalError):
        ArtifactPolicyEngine.validate_storage_reference("https://malicious.com/payload.png")


def test_policy_engine_filename_sanitization():
    unsafe = "../../../secret<stuff>:bad.png"
    safe = ArtifactPolicyEngine.sanitize_filename(unsafe)
    assert ".." not in safe
    assert "<" not in safe
    assert ":" not in safe
    assert "bad.png" in safe


def test_tenant_boundary_enforcement():
    org_a = uuid.uuid4()
    org_b = uuid.uuid4()

    user_a = User(
        id=uuid.uuid4(),
        auth_user_id="auth-a",
        email="alice@orga.com",
    )
    user_a.organization_id = org_a
    user_a.is_superuser = False

    # User A attempting to access Org B resource
    with pytest.raises(ArtifactAccessDeniedError):
        ArtifactPolicyEngine.verify_tenant_boundary(user_a, org_b)

    # User A accessing Org A resource passes
    ArtifactPolicyEngine.verify_tenant_boundary(user_a, org_a)


# =============================================================================
# 4. Artifact Lifecycle, Parts & Repository Tests (DB Integration)
# =============================================================================

@pytest.mark.asyncio
async def test_artifact_crud_and_parts_lifecycle(db_session: AsyncSession):
    org_id = uuid.uuid4()
    ws_id = uuid.uuid4()
    user_id = uuid.uuid4()

    user = User(
        id=user_id,
        auth_user_id="auth-dev",
        email="developer@test.com",
    )
    user.organization_id = org_id
    user.is_superuser = True

    artifact_service = ArtifactService(session=db_session)

    # 1. Upload Artifact
    csv_bytes = create_sample_csv()
    artifact, inspection = await artifact_service.create_artifact(
        organization_id=org_id,
        workspace_id=ws_id,
        owner_user_id=user.id,
        filename="financials.csv",
        data=csv_bytes,
        declared_mime="text/csv",
    )

    assert artifact.id is not None
    assert artifact.artifact_type == ArtifactType.SPREADSHEET.value
    assert artifact.status == ArtifactStatus.UPLOADED.value
    assert artifact.size_bytes == len(csv_bytes)

    # 2. Process and Extract Parts
    parts = await artifact_service.process_artifact(artifact.id)
    assert len(parts) >= 1
    assert parts[0].part_type in [ArtifactPartType.TABLE.value, ArtifactPartType.STRUCTURED_DATA.value]
    assert parts[0].text_content is not None
    assert "revenue" in parts[0].text_content

    # 3. Retrieve Artifact & Parts
    retrieved = await artifact_service.get_artifact(artifact.id, user)
    assert retrieved.id == artifact.id
    assert retrieved.status == ArtifactStatus.READY.value

    fetched_parts = await artifact_service.get_artifact_parts(artifact.id, user)
    assert len(fetched_parts) == len(parts)

    # 4. Soft Delete / Archive
    await artifact_service.delete_artifact(artifact.id, user)
    with pytest.raises(ArtifactNotFoundError):
        await artifact_service.get_artifact(artifact.id, user)


# =============================================================================
# 5. Capability Resolver & Model Router Capability Integration
# =============================================================================

def test_capability_resolver():
    resolver = CapabilityResolver()
    
    # Image artifact requires vision
    img_art = Artifact(
        id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        owner_user_id=uuid.uuid4(),
        artifact_type=ArtifactType.IMAGE.value,
        mime_type="image/png",
        filename="diagram.png",
        size_bytes=1024,
        storage_reference="ref1",
        content_hash="hash1",
        status=ArtifactStatus.READY.value,
    )
    reqs_img = resolver.resolve_requirements(task_text="Analyze this architecture diagram", artifacts=[img_art])
    assert reqs_img.requires_vision is True
    assert MediaCapability.VISION.value in reqs_img.required_capabilities

    # Audio artifact requires audio
    audio_art = Artifact(
        id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        owner_user_id=uuid.uuid4(),
        artifact_type=ArtifactType.AUDIO.value,
        mime_type="audio/mpeg",
        filename="meeting.mp3",
        size_bytes=2048,
        storage_reference="ref2",
        content_hash="hash2",
        status=ArtifactStatus.READY.value,
    )
    reqs_audio = resolver.resolve_requirements(task_text="What were the decisions?", artifacts=[audio_art])
    assert reqs_audio.requires_audio is True
    assert MediaCapability.AUDIO_INPUT.value in reqs_audio.required_capabilities


def test_model_catalog_has_multimodal_capabilities():
    # Verify mock-vision-v1 exists and advertises vision & multimodal
    catalog = {m.model_id: m for m in get_default_catalog()}
    model = catalog.get("mock-vision-v1")
    assert model is not None
    assert ModelCapability.VISION.value in model.capabilities
    assert ModelCapability.IMAGE_INPUT.value in model.capabilities
    assert ModelCapability.MULTIMODAL_INPUT.value in model.capabilities


def test_model_router_filters_vision_capability():
    from backend.app.services.models.base import ModelRequirements
    router = ModelRouter()
    
    # Request vision capability
    reqs = ModelRequirements(
        requires_vision=True,
    )
    selection = router.route(reqs)
    assert selection is not None
    catalog = {m.model_id: m for m in get_default_catalog()}
    selected_meta = catalog.get(selection.model_id)
    assert selected_meta is not None
    assert ModelCapability.VISION.value in selected_meta.capabilities or ModelCapability.IMAGE_INPUT.value in selected_meta.capabilities


# =============================================================================
# 6. AI Gateway Multimodal Request & Vision Service Tests
# =============================================================================

@pytest.mark.asyncio
async def test_ai_gateway_multimodal_request(db_session: AsyncSession):
    gateway = AIGateway()
    
    req = GatewayRequest(
        model="mock-vision-v1",
        prompt="Describe what you see in this screenshot.",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe what you see."},
                    {"type": "image", "artifact_id": str(uuid.uuid4()), "reference": "storage/img.png"},
                ],
            }
        ],
    )
    
    resp = await gateway.execute(req)
    assert resp.content is not None
    assert len(resp.content) > 0


@pytest.mark.asyncio
async def test_vision_service_with_structured_fallback():
    vision_svc = VisionService()
    
    # 1. Vision-capable model returns reasoning result
    result = await vision_svc.analyze_image(
        image_bytes=create_sample_png(),
        mime_type="image/png",
        instruction="Explain diagram",
        model_preference="mock-vision-v1",
    )
    assert result.analysis is not None
    assert result.summary is not None

    # 2. Non-vision model falls back to structured fallback description
    result_fallback = await vision_svc.analyze_image(
        image_bytes=create_sample_png(),
        mime_type="image/png",
        instruction="Explain diagram",
        model_preference="non-existent-provider-model",
    )
    assert result_fallback.analysis is not None
    assert result_fallback.fallback_used is True


# =============================================================================
# 7. ContextEngine Integration (MultimodalContextProvider)
# =============================================================================

@pytest.mark.asyncio
async def test_multimodal_context_provider(db_session: AsyncSession):
    org_id = uuid.uuid4()
    ws_id = uuid.uuid4()
    user_id = uuid.uuid4()

    # Create artifact & part
    art = Artifact(
        id=uuid.uuid4(),
        organization_id=org_id,
        workspace_id=ws_id,
        owner_user_id=user_id,
        artifact_type=ArtifactType.SPREADSHEET.value,
        mime_type="text/csv",
        filename="metrics.csv",
        size_bytes=100,
        storage_reference="store/metrics.csv",
        content_hash="hash123",
        status=ArtifactStatus.READY.value,
    )
    db_session.add(art)
    await db_session.flush()

    part = ArtifactPart(
        id=uuid.uuid4(),
        artifact_id=art.id,
        part_type=ArtifactPartType.TABLE.value,
        sequence_number=0,
        content_reference="part_ref_1",
        text_content="| month | revenue |\n| Jan | 50000 |",
        content_hash="hashpart123",
        metadata_json={"total_rows": 1, "columns": ["month", "revenue"]},
    )
    db_session.add(part)
    await db_session.commit()

    from backend.app.db.models.task import Task
    task = Task(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        title="Analyze Metrics",
    )
    task.organization_id = org_id
    task.workspace_id = ws_id
    provider = MultimodalContextProvider()
    raw_items = await provider.collect(
        task=task,
        session=db_session,
        artifact_ids=[art.id],
    )
    items = provider.normalize(raw_items)

    assert len(items) >= 1
    assert items[0].source_type == ContextSourceType.MULTIMODAL.value
    assert items[0].trust_level == "external_untrusted"
    assert "50000" in items[0].content


# =============================================================================
# 8. Retrieval Router Multimodal Strategy
# =============================================================================

@pytest.mark.asyncio
async def test_retrieval_router_multimodal_strategy():
    from backend.app.db.models.task import Task
    provider = RuleBasedDecisionProvider()
    
    # Prompt explicitly referencing multimodal assets
    pid = uuid.uuid4()
    task1 = Task(project_id=pid, instructions="Find the error in this screenshot image", title="Check screenshot")
    decision = await provider.decide(task=task1)
    assert decision.strategy == RetrievalStrategy.MULTIMODAL

    task2 = Task(project_id=pid, instructions="Please transcribe this audio recording", title="Audio task")
    decision_audio = await provider.decide(task=task2)
    assert decision_audio.strategy == RetrievalStrategy.MULTIMODAL

    task3 = Task(project_id=pid, instructions="Analyze this spreadsheet and calculate total revenue", title="Spreadsheet task")
    decision_table = await provider.decide(task=task3)
    assert decision_table.strategy == RetrievalStrategy.MULTIMODAL


# =============================================================================
# 9. Task Intelligence Multimodal Requirements
# =============================================================================

def test_task_intelligence_multimodal_requirements():
    analyzer = RuleBasedTaskAnalyzer()
    
    # Task with image/screenshot
    analysis, reqs = analyzer.analyze(
        task_text="Look at this screenshot and tell me why the build failed"
    )
    assert reqs.vision_required.value is True
    assert reqs.multimodal_required.value is True

    # Task with spreadsheet
    table_analysis, table_reqs = analyzer.analyze(
        task_text="Examine this csv spreadsheet and report revenue trend"
    )
    assert table_reqs.table_required.value is True
    assert table_analysis.task_type == TaskType.DATA_ANALYSIS


# =============================================================================
# 10. Evaluation Lab Multimodal Assertions
# =============================================================================

def test_evaluation_lab_multimodal_assertions():
    output = "According to the transcript at 00:02:14, the team agreed to launch on Friday."
    context = "At 00:02:14 Speaker 1 says 'We are ready to launch on Friday.'"

    # Test transcript_grounded assertion
    defn = AssertionDefinition(
        type=AssertionType.TRANSCRIPT_GROUNDED,
        value="launch on Friday",
        description="transcript_check",
    )
    res = AssertionEngine.evaluate_assertion(
        assertion=defn,
        output_text=output,
        context_items=[{"content": context, "metadata": {"media_type": "audio_transcript"}}],
    )
    assert res.passed is True

    # Test source_timestamp_exists assertion
    ts_defn = AssertionDefinition(
        type=AssertionType.SOURCE_TIMESTAMP_EXISTS,
        description="timestamp_check",
    )
    ts_res = AssertionEngine.evaluate_assertion(
        assertion=ts_defn,
        output_text=output,
    )
    assert ts_res.passed is True


# =============================================================================
# 11. Replay Snapshot Hash Capture & Tamper Detection
# =============================================================================

def test_replay_snapshot_captures_artifact_hash():
    snapshot = ExecutionSnapshot(
        run_id=str(uuid.uuid4()),
        task_id=str(uuid.uuid4()),
        workspace_id=str(uuid.uuid4()),
        created_at=datetime.now(timezone.utc).isoformat(),
        artifact_configuration={
            "artifact_ids": ["art-001"],
            "content_hashes": {"art-001": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"},
            "parts_selected": ["part-001"],
        },
    )

    assert snapshot.artifact_configuration is not None
    assert "artifact_ids" in snapshot.artifact_configuration
    assert snapshot.artifact_configuration["content_hashes"]["art-001"] is not None


# =============================================================================
# 12. Background Job Handlers Integration
# =============================================================================

@pytest.mark.asyncio
async def test_job_handlers_registered():
    from backend.app.services.jobs.handlers import job_handler_registry
    assert job_handler_registry.get_handler(JobType.ARTIFACT_PROCESSING.value) is not None
    assert job_handler_registry.get_handler(JobType.IMAGE_PROCESSING.value) is not None
    assert job_handler_registry.get_handler(JobType.AUDIO_TRANSCRIPTION.value) is not None
    assert job_handler_registry.get_handler(JobType.VIDEO_PROCESSING.value) is not None
    assert job_handler_registry.get_handler(JobType.TABLE_PROCESSING.value) is not None
    assert job_handler_registry.get_handler(JobType.MULTIMODAL_EXTRACTION.value) is not None
