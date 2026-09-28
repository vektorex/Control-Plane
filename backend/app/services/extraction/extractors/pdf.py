import io
from typing import List, Optional
from backend.app.core.errors import ExtractionError
from backend.app.services.extraction.base import DocumentExtractor, ExtractedDocument, ExtractedPage


class PDFExtractor(DocumentExtractor):
    """
    Extractor for Portable Document Format files (.pdf).
    Extracts structured page-by-page text preserving page numbers.
    """

    @property
    def supported_mime_types(self) -> List[str]:
        return ["application/pdf", "application/x-pdf"]

    @property
    def supported_extensions(self) -> List[str]:
        return [".pdf"]

    def extract(self, data: bytes, filename: str, mime_type: Optional[str] = None) -> ExtractedDocument:
        if not data:
            raise ExtractionError(f"PDF file '{filename}' is empty.")

        pages: List[ExtractedPage] = []
        all_text_segments: List[str] = []

        # Strategy 1: Use pypdf if available
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(data))
            total_pages = len(reader.pages)

            for idx, page in enumerate(reader.pages, 1):
                page_text = page.extract_text() or ""
                cleaned = page_text.strip()
                if cleaned:
                    pages.append(ExtractedPage(page_number=idx, text=cleaned))
                    all_text_segments.append(cleaned)
                else:
                    # Record empty page placeholder to preserve page numbering
                    pages.append(ExtractedPage(page_number=idx, text=""))

            full_text = "\n\n".join(t for t in all_text_segments if t)
            return ExtractedDocument(
                filename=filename,
                mime_type=mime_type or "application/pdf",
                text=full_text,
                pages=pages,
                char_count=len(full_text),
                metadata={"total_pages": total_pages, "format": "pdf", "engine": "pypdf"},
            )
        except Exception as e:
            # Strategy 2: Fallback to PyMuPDF (fitz) if pypdf encountered an issue
            try:
                import fitz
                doc = fitz.open(stream=data, filetype="pdf")
                total_pages = len(doc)
                pages = []
                all_text_segments = []

                for idx in range(total_pages):
                    page = doc[idx]
                    page_text = page.get_text() or ""
                    cleaned = page_text.strip()
                    pages.append(ExtractedPage(page_number=idx + 1, text=cleaned))
                    if cleaned:
                        all_text_segments.append(cleaned)

                full_text = "\n\n".join(t for t in all_text_segments if t)
                return ExtractedDocument(
                    filename=filename,
                    mime_type=mime_type or "application/pdf",
                    text=full_text,
                    pages=pages,
                    char_count=len(full_text),
                    metadata={"total_pages": total_pages, "format": "pdf", "engine": "pymupdf"},
                )
            except Exception as fitz_err:
                raise ExtractionError(f"Failed to parse PDF document '{filename}': {str(e)} / {str(fitz_err)}")
