from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class RetrievalCandidate(BaseModel):
    """
    Candidate chunk retrieved from either vector or keyword search.
    """
    chunk_id: UUID
    document_id: UUID
    workspace_id: UUID
    project_id: Optional[UUID] = None
    filename: str = "document"
    content: str
    page_number: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    vector_score: Optional[float] = None
    keyword_score: Optional[float] = None
    fusion_score: float = 0.0
    rerank_score: float = 0.0


class RetrievalResult(BaseModel):
    """
    Final ranked retrieval result produced by the Hybrid Search and Reranker pipeline.
    """
    candidates: List[RetrievalCandidate] = Field(default_factory=list)
    query: str
    total_found: int = 0
    vector_count: int = 0
    keyword_count: int = 0
    retrieval_latency_ms: int = 0
