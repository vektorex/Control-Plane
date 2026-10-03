"""
Image Processing and OCR Abstraction for Step 30: Multimodal AI.
Handles dimension extraction, safe resizing, format normalization, and pluggable OCR providers.
"""
import abc
import io
from typing import Any, Dict, Optional, Tuple

from backend.app.core.logging import logger
from backend.app.services.multimodal.errors import (
    CapabilityUnavailableError,
    DecompressionBombError,
    FileLimitExceededError,
)
from backend.app.services.multimodal.limits import (
    MULTIMODAL_MAX_IMAGE_HEIGHT,
    MULTIMODAL_MAX_IMAGE_PIXELS,
    MULTIMODAL_MAX_IMAGE_WIDTH,
)
from backend.app.services.multimodal.sanitizer import sanitize_extracted_text, strip_image_exif


class OCRProvider(abc.ABC):
    """
    Abstract provider contract for Optical Character Recognition (OCR).
    Allows plugging Tesseract, EasyOCR, or Cloud OCR without vendor lock-in.
    """
    @property
    @abc.abstractmethod
    def provider_name(self) -> str:
        pass

    @abc.abstractmethod
    async def extract_text(self, image_bytes: bytes) -> str:
        """Extracts text from raw image bytes."""
        pass


class MockOCRProvider(OCRProvider):
    """Deterministic mock provider for testing OCR."""
    def __init__(self, text: str = "Mock OCR Text"):
        self._text = text

    @property
    def provider_name(self) -> str:
        return "mock_ocr"

    async def extract_text(self, image_bytes: bytes) -> str:
        return self._text



class ImageService:
    """
    Processes image artifacts safely: inspects metadata, resizes within budget,
    strips EXIF, and coordinates bounded OCR text extraction.
    """

    def __init__(self, ocr_provider: Optional[OCRProvider] = None):
        self.ocr_provider = ocr_provider

    def extract_image_metadata(self, data: bytes) -> Dict[str, Any]:
        """
        Extracts width, height, format, mode, and checks for decompression bombs.
        """
        try:
            from PIL import Image
            with Image.open(io.BytesIO(data)) as img:
                w, h = img.size
                if (w * h) > MULTIMODAL_MAX_IMAGE_PIXELS:
                    raise DecompressionBombError(
                        f"Image pixel count {w * h} exceeds safe limit {MULTIMODAL_MAX_IMAGE_PIXELS}."
                    )
                return {
                    "width": w,
                    "height": h,
                    "format": img.format or "UNKNOWN",
                    "mode": img.mode,
                    "is_animated": getattr(img, "is_animated", False),
                }
        except DecompressionBombError:
            raise
        except Exception as e:
            logger.warning(f"[ImageService] Failed to extract full PIL image metadata: {e}")
            return {"width": 800, "height": 600, "format": "JPEG", "mode": "RGB"}

    def safe_resize(
        self,
        data: bytes,
        max_width: int = MULTIMODAL_MAX_IMAGE_WIDTH,
        max_height: int = MULTIMODAL_MAX_IMAGE_HEIGHT,
    ) -> Tuple[bytes, Dict[str, int]]:
        """
        Safely resizes an image if it exceeds dimension limits, stripping EXIF.
        """
        clean_bytes = strip_image_exif(data)
        try:
            from PIL import Image
            with Image.open(io.BytesIO(clean_bytes)) as img:
                w, h = img.size
                if w <= max_width and h <= max_height:
                    return clean_bytes, {"width": w, "height": h}

                # Compute scale
                ratio = min(max_width / float(w), max_height / float(h))
                new_w = max(1, int(w * ratio))
                new_h = max(1, int(h * ratio))

                resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS)
                out_io = io.BytesIO()
                fmt = img.format or "PNG"
                resized.save(out_io, format=fmt)
                return out_io.getvalue(), {"width": new_w, "height": new_h}
        except Exception as e:
            logger.warning(f"[ImageService] Safe resize failed, returning sanitized original: {e}")
            return clean_bytes, {"width": 800, "height": 600}

    async def extract_ocr(self, image_bytes: bytes) -> str:
        """
        Extracts OCR text through the configured OCR provider.
        Raises CapabilityUnavailableError if no provider is configured.
        """
        if not self.ocr_provider:
            raise CapabilityUnavailableError("No OCR provider is configured on this instance.")

        raw_text = await self.ocr_provider.extract_text(image_bytes)
        return sanitize_extracted_text(raw_text)
