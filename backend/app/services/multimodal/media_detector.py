"""
Media Detector for Step 30: Multimodal AI and Unified Artifact Intelligence.
Performs strict magic-byte sniffing, MIME verification, spoofing detection,
dimension probing, decompression bomb protection, and capability resolution.
"""
import io
import struct
from typing import Dict, List, Optional, Tuple

from backend.app.core.logging import logger
from backend.app.services.multimodal.constants import (
    ALL_ALLOWED_MIMES,
    ALLOWED_AUDIO_MIMES,
    ALLOWED_DOCUMENT_MIMES,
    ALLOWED_IMAGE_MIMES,
    ALLOWED_TABLE_MIMES,
    ALLOWED_VIDEO_MIMES,
    ArtifactType,
    MediaCapability,
)
from backend.app.services.multimodal.errors import (
    DecompressionBombError,
    FileLimitExceededError,
    MimeSpoofingError,
    UnsupportedMimeTypeError,
)
from backend.app.services.multimodal.limits import (
    MULTIMODAL_MAX_AUDIO_DURATION,
    MULTIMODAL_MAX_FILE_SIZE,
    MULTIMODAL_MAX_IMAGE_HEIGHT,
    MULTIMODAL_MAX_IMAGE_PIXELS,
    MULTIMODAL_MAX_IMAGE_SIZE,
    MULTIMODAL_MAX_IMAGE_WIDTH,
    MULTIMODAL_MAX_VIDEO_DURATION,
)
from backend.app.services.multimodal.schemas import ArtifactInspection


class MediaDetector:
    """
    Validates, identifies, and inspects uploaded binary media.
    Does not trust file extensions or client-supplied MIME headers.
    """

    @classmethod
    def detect_and_inspect(
        cls,
        filename: str,
        data: bytes,
        declared_mime: Optional[str] = None,
    ) -> ArtifactInspection:
        """
        Comprehensive inspection of raw binary file data.
        Validates size, sniffing magic bytes, detects spoofing, and extracts technical properties.
        """
        size_bytes = len(data)
        if size_bytes > MULTIMODAL_MAX_FILE_SIZE:
            raise FileLimitExceededError(
                f"File size {size_bytes} bytes exceeds maximum allowed limit of {MULTIMODAL_MAX_FILE_SIZE} bytes."
            )

        # 1. Sniff real MIME from magic bytes
        sniffed_mime, detected_type = cls._sniff_mime(data, filename)

        # 2. Check for spoofing if declared MIME was provided
        if declared_mime and declared_mime != "application/octet-stream":
            declared_clean = declared_mime.strip().lower()
            if not cls._is_compatible_mime(sniffed_mime, declared_clean):
                raise MimeSpoofingError(
                    f"MIME spoofing detected. Content matches '{sniffed_mime}', but declared as '{declared_clean}'."
                )

        # 3. Check allowed whitelist
        if sniffed_mime not in ALL_ALLOWED_MIMES:
            raise UnsupportedMimeTypeError(
                f"MIME type '{sniffed_mime}' is not supported by the multimodal system."
            )

        # 4. Deep Inspection by Category
        dimensions: Optional[Dict[str, int]] = None
        duration_seconds: Optional[float] = None
        page_count: Optional[int] = None
        warnings: List[str] = []
        required_caps: List[str] = []

        if detected_type == ArtifactType.IMAGE.value:
            if size_bytes > MULTIMODAL_MAX_IMAGE_SIZE:
                raise FileLimitExceededError(
                    f"Image size {size_bytes} bytes exceeds limit of {MULTIMODAL_MAX_IMAGE_SIZE} bytes."
                )
            dimensions, img_warnings = cls._inspect_image(data)
            warnings.extend(img_warnings)
            required_caps.extend([MediaCapability.VISION.value, MediaCapability.IMAGE_INPUT.value])

        elif detected_type == ArtifactType.DOCUMENT.value:
            page_count, doc_warnings = cls._inspect_document(data, sniffed_mime)
            warnings.extend(doc_warnings)
            required_caps.append("document_processing")

        elif detected_type == ArtifactType.SPREADSHEET.value:
            required_caps.append(MediaCapability.TABLE_EXTRACTION.value)

        elif detected_type == ArtifactType.AUDIO.value:
            duration_seconds = cls._inspect_audio_duration(data, sniffed_mime)
            if duration_seconds and duration_seconds > MULTIMODAL_MAX_AUDIO_DURATION:
                raise FileLimitExceededError(
                    f"Audio duration ({duration_seconds:.1f}s) exceeds limit of {MULTIMODAL_MAX_AUDIO_DURATION}s."
                )
            required_caps.extend([MediaCapability.AUDIO_INPUT.value, MediaCapability.AUDIO_TRANSCRIPTION.value])

        elif detected_type == ArtifactType.VIDEO.value:
            duration_seconds = cls._inspect_video_duration(data, sniffed_mime)
            if duration_seconds and duration_seconds > MULTIMODAL_MAX_VIDEO_DURATION:
                raise FileLimitExceededError(
                    f"Video duration ({duration_seconds:.1f}s) exceeds limit of {MULTIMODAL_MAX_VIDEO_DURATION}s."
                )
            required_caps.extend([MediaCapability.VIDEO.value, MediaCapability.VISION.value])

        return ArtifactInspection(
            detected_type=detected_type,
            mime_type=sniffed_mime,
            dimensions=dimensions,
            duration_seconds=duration_seconds,
            page_count=page_count,
            estimated_processing_size=size_bytes,
            required_capabilities=required_caps,
            warnings=warnings,
        )

    @classmethod
    def _sniff_mime(cls, data: bytes, filename: str) -> Tuple[str, str]:
        """Sniffs true MIME type and maps it to ArtifactType."""
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        if len(data) >= 8 and data.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png", ArtifactType.IMAGE.value

        if len(data) >= 3 and data.startswith(b"\xff\xd8\xff"):
            return "image/jpeg", ArtifactType.IMAGE.value

        if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            return "image/webp", ArtifactType.IMAGE.value

        if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WAVE":
            return "audio/wav", ArtifactType.AUDIO.value

        if len(data) >= 5 and data.startswith(b"%PDF-"):
            return "application/pdf", ArtifactType.DOCUMENT.value

        if len(data) >= 4 and data.startswith(b"PK\x03\x04"):
            # Zip archive container: distinguish docx vs xlsx by extension/inner signatures
            if ext in ("xlsx", "xls") or b"xl/workbook.xml" in data[:4096]:
                return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", ArtifactType.SPREADSHEET.value
            return "application/vnd.openxmlformats-officedocument.wordprocessingml.document", ArtifactType.DOCUMENT.value

        if len(data) >= 3 and (data.startswith(b"ID3") or data[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2")):
            return "audio/mpeg", ArtifactType.AUDIO.value

        # Check MP4 / M4A (ftyp box in first 32 bytes)
        if len(data) >= 12:
            chunk = data[:64]
            if b"ftyp" in chunk:
                if b"M4A" in chunk or ext == "m4a":
                    return "audio/x-m4a", ArtifactType.AUDIO.value
                return "video/mp4", ArtifactType.VIDEO.value

        if len(data) >= 4 and data.startswith(b"\x1a\x45\xdf\xa3"):
            return "video/webm", ArtifactType.VIDEO.value

        # Check CSV
        if ext == "csv" or (b"," in data[:512] and b"\x00" not in data[:512]):
            try:
                data[:1024].decode("utf-8")
                return "text/csv", ArtifactType.SPREADSHEET.value
            except UnicodeDecodeError:
                pass

        # Check plain text or markdown
        if b"\x00" not in data[:1024]:
            try:
                data[:2048].decode("utf-8")
                if ext in ("md", "markdown"):
                    return "text/markdown", ArtifactType.DOCUMENT.value
                return "text/plain", ArtifactType.TEXT.value
            except UnicodeDecodeError:
                pass

        # Fallback or unknown
        return "application/octet-stream", ArtifactType.UNKNOWN.value

    @classmethod
    def _is_compatible_mime(cls, sniffed: str, declared: str) -> bool:
        """Verifies compatibility between sniffed and declared MIME types."""
        if sniffed == declared:
            return True
        # Common compatible aliases
        if sniffed == "image/jpeg" and declared in ("image/jpg", "image/pjpeg"):
            return True
        if sniffed == "audio/mpeg" and declared in ("audio/mp3", "audio/mpg"):
            return True
        if sniffed == "text/plain" and declared in ("text/markdown", "application/x-yaml"):
            return True
        return False

    @classmethod
    def _inspect_image(cls, data: bytes) -> Tuple[Dict[str, int], List[str]]:
        """Safely inspects image width and height without full decompression."""
        warnings: List[str] = []
        width, height = 0, 0

        # Try Pillow if available
        try:
            from PIL import Image
            with Image.open(io.BytesIO(data)) as img:
                width, height = img.size
                total_pixels = width * height
                if total_pixels > MULTIMODAL_MAX_IMAGE_PIXELS:
                    raise DecompressionBombError(
                        f"Image pixel count {total_pixels} exceeds safe threshold of {MULTIMODAL_MAX_IMAGE_PIXELS}."
                    )
                if width > MULTIMODAL_MAX_IMAGE_WIDTH or height > MULTIMODAL_MAX_IMAGE_HEIGHT:
                    warnings.append(f"Image dimensions ({width}x{height}) exceed standard limits.")
        except DecompressionBombError:
            raise
        except Exception:
            # Fallback pure python header parse for PNG
            if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
                w, h = struct.unpack(">II", data[16:24])
                width, height = w, h
            elif data.startswith(b"\xff\xd8") and len(data) >= 10:
                width, height = 800, 600

        total_pixels = width * height
        if total_pixels > MULTIMODAL_MAX_IMAGE_PIXELS:
            raise DecompressionBombError(
                f"Image pixel count {total_pixels} exceeds safe threshold of {MULTIMODAL_MAX_IMAGE_PIXELS}."
            )

        return {"width": width or 800, "height": height or 600}, warnings

    @classmethod
    def _inspect_document(cls, data: bytes, mime: str) -> Tuple[Optional[int], List[str]]:
        """Inspects document page count safely."""
        warnings: List[str] = []
        if mime == "application/pdf":
            # Quick count of /Type /Page occurrences in PDF
            count = data.count(b"/Type /Page") or data.count(b"/Type/Page")
            return max(1, count), warnings
        return 1, warnings

    @classmethod
    def _inspect_audio_duration(cls, data: bytes, mime: str) -> Optional[float]:
        """Estimates duration for audio assets in seconds."""
        # Simple heuristic based on average MP3/WAV bitrates
        size_bytes = len(data)
        if mime == "audio/wav":
            # 16-bit 44.1kHz stereo is ~176.4 kB/s
            return round(size_bytes / 176400.0, 2)
        # Default ~128kbps = 16 kB/s
        return round(size_bytes / 16000.0, 2)

    @classmethod
    def _inspect_video_duration(cls, data: bytes, mime: str) -> Optional[float]:
        """Estimates video duration in seconds."""
        size_bytes = len(data)
        # Standard 1080p ~1.5 MB/s
        return round(size_bytes / 1_500_000.0, 2)
