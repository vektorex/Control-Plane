from typing import List, Optional
from backend.app.core.errors import UnsupportedMediaTypeError
from backend.app.services.extraction.base import DocumentExtractor
from backend.app.services.extraction.extractors.docx import DOCXExtractor
from backend.app.services.extraction.extractors.markdown import MarkdownExtractor
from backend.app.services.extraction.extractors.pdf import PDFExtractor
from backend.app.services.extraction.extractors.text import TextExtractor


class ExtractorFactory:
    """
    Factory that selects the appropriate DocumentExtractor based on MIME type and file extension.
    """

    def __init__(self) -> None:
        self.extractors: List[DocumentExtractor] = [
            TextExtractor(),
            MarkdownExtractor(),
            PDFExtractor(),
            DOCXExtractor(),
        ]

    def register_extractor(self, extractor: DocumentExtractor) -> None:
        """Register custom or specialized extractor."""
        self.extractors.insert(0, extractor)

    def get_extractor(self, mime_type: str, filename: str) -> DocumentExtractor:
        """
        Finds the first extractor capable of handling the specified MIME type or filename.
        """
        for extractor in self.extractors:
            if extractor.can_handle(mime_type=mime_type, filename=filename):
                return extractor

        raise UnsupportedMediaTypeError(
            f"Unsupported file format for '{filename}' (MIME: '{mime_type}'). "
            "Supported formats: PDF (.pdf), Plain Text (.txt), Markdown (.md), and Word (.docx)."
        )


_global_factory: Optional[ExtractorFactory] = None


def get_extractor_factory() -> ExtractorFactory:
    """Dependency injector / factory function for ExtractorFactory."""
    global _global_factory
    if _global_factory is None:
        _global_factory = ExtractorFactory()
    return _global_factory
