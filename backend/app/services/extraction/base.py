from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExtractedPage(BaseModel):
    """
    Extracted page text and metadata within a document.
    """
    page_number: int
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExtractedDocument(BaseModel):
    """
    Normalized document representation resulting from the extraction stage.
    """
    filename: str
    mime_type: str
    text: str
    pages: List[ExtractedPage] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    char_count: int = 0


class DocumentExtractor(ABC):
    """
    Abstract Base Class for format-specific document extractors.
    """

    @property
    @abstractmethod
    def supported_mime_types(self) -> List[str]:
        """List of MIME content types supported by this extractor."""
        pass

    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """List of file extensions supported by this extractor (e.g. ['.pdf', '.txt'])."""
        pass

    def can_handle(self, mime_type: str, filename: str) -> bool:
        """
        Returns True if this extractor can process the given MIME type or file extension.
        """
        mime_match = any(mime_type.lower().startswith(m.lower()) for m in self.supported_mime_types)
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        ext_match = ext in [e.lower() for e in self.supported_extensions]
        return mime_match or ext_match

    @abstractmethod
    def extract(self, data: bytes, filename: str, mime_type: Optional[str] = None) -> ExtractedDocument:
        """
        Extracts structured text and page information from raw binary document data.
        """
        pass
