"""
Constants and Enums for Step 30: Multimodal AI and Unified Artifact Intelligence.
"""
from enum import Enum
from typing import Set


class ArtifactType(str, Enum):
    TEXT = "text"
    DOCUMENT = "document"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    SPREADSHEET = "spreadsheet"
    ARCHIVE = "archive"
    UNKNOWN = "unknown"


class ArtifactStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    ARCHIVED = "archived"


class ArtifactPartType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    TABLE = "table"
    AUDIO_SEGMENT = "audio_segment"
    VIDEO_FRAME = "video_frame"
    STRUCTURED_DATA = "structured_data"


class MediaCapability(str, Enum):
    VISION = "vision"
    IMAGE_INPUT = "image_input"
    MULTIMODAL_INPUT = "multimodal_input"
    AUDIO_INPUT = "audio_input"
    AUDIO_TRANSCRIPTION = "audio_transcription"
    VIDEO = "video"
    TABLE_EXTRACTION = "table_extraction"
    OCR = "ocr"


ALLOWED_IMAGE_MIMES: Set[str] = {
    "image/png",
    "image/jpeg",
    "image/webp",
}

ALLOWED_DOCUMENT_MIMES: Set[str] = {
    "application/pdf",
    "text/plain",
    "text/markdown",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

ALLOWED_AUDIO_MIMES: Set[str] = {
    "audio/mpeg",
    "audio/wav",
    "audio/x-m4a",
    "audio/mp4",
}

ALLOWED_VIDEO_MIMES: Set[str] = {
    "video/mp4",
    "video/webm",
}

ALLOWED_TABLE_MIMES: Set[str] = {
    "text/csv",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}

ALL_ALLOWED_MIMES: Set[str] = (
    ALLOWED_IMAGE_MIMES
    | ALLOWED_DOCUMENT_MIMES
    | ALLOWED_AUDIO_MIMES
    | ALLOWED_VIDEO_MIMES
    | ALLOWED_TABLE_MIMES
)

MAGIC_BYTE_SIGNATURES = {
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
    b"RIFF": "image/webp_or_wav",  # Need secondary check for WEBP or WAV
    b"%PDF-": "application/pdf",
    b"PK\x03\x04": "zip_based",  # docx or xlsx
    b"ID3": "audio/mpeg",
    b"\xff\xfb": "audio/mpeg",
    b"\xff\xf3": "audio/mpeg",
    b"\xff\xf2": "audio/mpeg",
    b"\x00\x00\x00\x18ftyp": "video/mp4_or_audio",
    b"\x00\x00\x00\x1cftyp": "video/mp4_or_audio",
    b"\x00\x00\x00\x20ftyp": "video/mp4_or_audio",
    b"\x1a\x45\xdf\xa3": "video/webm",
}
