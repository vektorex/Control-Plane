from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class RawChunk(BaseModel):
    """
    In-memory representation of a chunked text segment.
    """
    chunk_index: int
    content: str
    token_count: int = 0
    page_number: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
