from typing import List, Optional
from backend.app.core.errors import ExtractionError
from backend.app.services.extraction.base import DocumentExtractor, ExtractedDocument, ExtractedPage


class TextExtractor(DocumentExtractor):
    """
    Extractor for plain text files (.txt).
    """

    @property
    def supported_mime_types(self) -> List[str]:
        return ["text/plain"]

    @property
    def supported_extensions(self) -> List[str]:
        return [".txt"]

    def extract(self, data: bytes, filename: str, mime_type: Optional[str] = None) -> ExtractedDocument:
        # Try UTF-8 with fallback encodings
        text = None
        for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
            try:
                text = data.decode(encoding)
                break
            except UnicodeDecodeError:
                continue

        if text is None:
            raise ExtractionError(f"Failed to decode text file '{filename}' with supported text encodings.")

        cleaned_text = text.strip()
        page = ExtractedPage(page_number=1, text=cleaned_text)

        return ExtractedDocument(
            filename=filename,
            mime_type=mime_type or "text/plain",
            text=cleaned_text,
            pages=[page],
            char_count=len(cleaned_text),
            metadata={"format": "txt"},
        )
