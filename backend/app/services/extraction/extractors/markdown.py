from typing import List, Optional
from backend.app.core.errors import ExtractionError
from backend.app.services.extraction.base import DocumentExtractor, ExtractedDocument, ExtractedPage


class MarkdownExtractor(DocumentExtractor):
    """
    Extractor for Markdown documentation files (.md, .markdown).
    """

    @property
    def supported_mime_types(self) -> List[str]:
        return ["text/markdown", "text/x-markdown", "text/plain"]

    @property
    def supported_extensions(self) -> List[str]:
        return [".md", ".markdown"]

    def extract(self, data: bytes, filename: str, mime_type: Optional[str] = None) -> ExtractedDocument:
        text = None
        for encoding in ["utf-8", "utf-8-sig", "latin-1"]:
            try:
                text = data.decode(encoding)
                break
            except UnicodeDecodeError:
                continue

        if text is None:
            raise ExtractionError(f"Failed to decode markdown file '{filename}'.")

        cleaned_text = text.strip()
        headings_count = sum(1 for line in cleaned_text.splitlines() if line.strip().startswith('#'))
        page = ExtractedPage(page_number=1, text=cleaned_text)

        return ExtractedDocument(
            filename=filename,
            mime_type=mime_type or "text/markdown",
            text=cleaned_text,
            pages=[page],
            char_count=len(cleaned_text),
            metadata={"format": "markdown", "headings_count": headings_count},
        )
