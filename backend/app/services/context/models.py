import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ContextSourceType(str, Enum):
    """
    Extensible enumeration of context item source types.
    Allows adding document, vector, web, github, database, api, tool in future steps
    without modifying the core ContextEngine architecture.
    """
    TASK = "task"
    MANUAL = "manual"
    SYSTEM = "system"
    DOCUMENT = "document"
    VECTOR = "vector"
    WEB = "web"
    GITHUB = "github"
    DATABASE = "database"
    API = "api"
    TOOL = "tool"
    CONNECTOR = "connector"
    MEMORY = "memory"


class ContextItem(BaseModel):
    """
    Normalized internal context representation across all heterogeneous sources.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_type: str = Field(default=ContextSourceType.MANUAL.value)
    title: str = Field(..., description="Human-readable title or label for this context item")
    content: str = Field(..., description="The textual content or payload of the context")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary metadata attributes")
    relevance_score: Optional[float] = Field(default=None, description="Optional relevance metric [0.0 - 1.0]")
    priority: int = Field(default=1, description="Priority weight (higher values denote higher priority)")
    token_estimate: int = Field(default=0, description="Estimated token count for this item")
    trust_level: Optional[str] = Field(default="trusted_user_context", description="Security and provenance trust classification")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<ContextItem id={self.id} source={self.source_type} title='{self.title}' priority={self.priority} tokens={self.token_estimate}>"


class ContextBudget(BaseModel):
    """
    Configuration for context token limits and budget allocation.
    """
    max_context_tokens: int = Field(default=8000, ge=1, le=128000, description="Max tokens allocated for context")
    reserved_output_tokens: int = Field(default=1000, ge=0, description="Reserved token buffer for model response generation")


class ContextPackage(BaseModel):
    """
    Structured, provider-independent output produced by the ContextEngine.
    """
    items: List[ContextItem] = Field(default_factory=list, description="Assembled, prioritized context items")
    total_items: int = Field(default=0, description="Count of accepted context items")
    estimated_tokens: int = Field(default=0, description="Total estimated token count across all included items")
    truncated: bool = Field(default=False, description="True if any items were excluded or truncated to respect budget")
    sources: List[str] = Field(default_factory=list, description="Unique source types represented in the package")
    dropped_items_count: int = Field(default=0, description="Number of items dropped due to budget constraints or deduplication")
