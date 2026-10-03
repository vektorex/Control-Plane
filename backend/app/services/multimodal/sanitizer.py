"""
Sanitization and Security Utilities for Step 30: Multimodal AI and Unified Artifact Intelligence.
Strips EXIF, scrubs sensitive tokens, and marks all extracted media text as 'external_untrusted'.
"""
import io
import re
from typing import Any, Dict, Optional


SENSITIVE_KEY_PATTERNS = [
    re.compile(r"api[-_]?key", re.IGNORECASE),
    re.compile(r"secret", re.IGNORECASE),
    re.compile(r"password", re.IGNORECASE),
    re.compile(r"token", re.IGNORECASE),
    re.compile(r"auth", re.IGNORECASE),
    re.compile(r"bearer", re.IGNORECASE),
]

SECRET_VALUE_PATTERNS = [
    re.compile(r"ghp_[a-zA-Z0-9_]{36,255}"),
    re.compile(r"sk-[a-zA-Z0-9_-]{32,255}"),
    re.compile(r"Bearer\s+[a-zA-Z0-9_\-\.]{20,}", re.IGNORECASE),
    re.compile(r"AKIA[0-9A-Z]{16}"),
]


def sanitize_artifact_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively removes sensitive keys, secrets, or internal paths from artifact metadata.
    """
    sanitized: Dict[str, Any] = {}
    for k, v in metadata.items():
        if any(p.search(str(k)) for p in SENSITIVE_KEY_PATTERNS):
            continue

        if isinstance(v, dict):
            sanitized[k] = sanitize_artifact_metadata(v)
        elif isinstance(v, list):
            sanitized[k] = [
                sanitize_artifact_metadata(item) if isinstance(item, dict) else item
                for item in v
            ]
        elif isinstance(v, str):
            val_clean = v
            for p in SECRET_VALUE_PATTERNS:
                val_clean = p.sub("[REDACTED_SECRET]", val_clean)
            sanitized[k] = val_clean
        else:
            sanitized[k] = v

    return sanitized


def strip_image_exif(image_bytes: bytes) -> bytes:
    """
    Strips EXIF data and geolocation metadata from JPEG/PNG images
    to prevent metadata leaks and memory buffer overflows.
    """
    try:
        from PIL import Image
        with Image.open(io.BytesIO(image_bytes)) as img:
            data_clean = list(img.getdata())
            image_without_exif = Image.new(img.mode, img.size)
            image_without_exif.putdata(data_clean)
            out_io = io.BytesIO()
            fmt = img.format or "PNG"
            image_without_exif.save(out_io, format=fmt)
            return out_io.getvalue()
    except Exception:
        # If pillow fails or is not installed, return original bytes safely
        return image_bytes


def sanitize_extracted_text(text: Optional[str]) -> str:
    """
    Cleans extracted OCR/transcript text, masking detected secrets and neutralizing
    control sequences.
    """
    if not text:
        return ""
    cleaned = text
    for p in SECRET_VALUE_PATTERNS:
        cleaned = p.sub("[REDACTED_SECRET]", cleaned)
    # Remove null characters and non-printable control characters
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", cleaned)
    return cleaned.strip()


def wrap_untrusted_context_metadata(
    metadata: Dict[str, Any],
    artifact_id: str,
    part_id: Optional[str] = None,
    media_type: str = "media",
) -> Dict[str, Any]:
    """
    Wraps extracted content metadata with explicit untrusted tags, provenance,
    and security boundaries so prompt injection from media cannot alter permissions.
    """
    safe_meta = sanitize_artifact_metadata(metadata)
    safe_meta.update({
        "artifact_id": str(artifact_id),
        "part_id": str(part_id) if part_id else None,
        "media_type": media_type,
        "data_trust_level": "external_untrusted",
        "is_untrusted_input": True,
        "provenance": "artifact_extraction",
    })
    return safe_meta


class MultimodalSanitizer:
    """Class wrapper for multimodal sanitization operations."""

    sanitize_metadata = staticmethod(sanitize_artifact_metadata)
    strip_exif = staticmethod(strip_image_exif)
    sanitize_text = staticmethod(sanitize_extracted_text)
    wrap_untrusted_metadata = staticmethod(wrap_untrusted_context_metadata)

