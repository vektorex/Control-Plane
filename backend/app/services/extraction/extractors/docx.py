import io
from typing import List, Optional
from backend.app.core.errors import ExtractionError
from backend.app.services.extraction.base import DocumentExtractor, ExtractedDocument, ExtractedPage


class DOCXExtractor(DocumentExtractor):
    """
    Extractor for Microsoft Word documents (.docx).
    Parses paragraphs, headings, and table cells.
    """

    @property
    def supported_mime_types(self) -> List[str]:
        return [
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/docx",
            "application/msword",
        ]

    @property
    def supported_extensions(self) -> List[str]:
        return [".docx"]

    def extract(self, data: bytes, filename: str, mime_type: Optional[str] = None) -> ExtractedDocument:
        if not data:
            raise ExtractionError(f"DOCX file '{filename}' is empty.")

        try:
            import docx
            doc = docx.Document(io.BytesIO(data))

            text_chunks: List[str] = []

            # 1. Paragraphs and Headings
            for p in doc.paragraphs:
                cleaned = p.text.strip()
                if cleaned:
                    text_chunks.append(cleaned)

            # 2. Tables
            for table in doc.tables:
                for row in table.rows:
                    row_texts = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_texts:
                        text_chunks.append(" | ".join(row_texts))

            full_text = "\n\n".join(text_chunks)
            page = ExtractedPage(page_number=1, text=full_text)

            return ExtractedDocument(
                filename=filename,
                mime_type=mime_type or "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                text=full_text,
                pages=[page],
                char_count=len(full_text),
                metadata={"format": "docx", "paragraph_count": len(doc.paragraphs)},
            )
        except Exception as e:
            raise ExtractionError(f"Failed to parse DOCX document '{filename}': {str(e)}")
