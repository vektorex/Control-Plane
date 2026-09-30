from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RetrievalMode(str, Enum):
    """User routing mode preference."""
    AUTO = "auto"
    ALWAYS = "always"
    NEVER = "never"


class RetrievalStrategy(str, Enum):
    """
    Supported retrieval strategies for knowledge grounding.
    Extensible for future sources (web, graph, database, api, github).
    """
    NONE = "none"
    KEYWORD = "keyword"
    VECTOR = "vector"
    HYBRID = "hybrid"
    MULTI_QUERY = "multi_query"

    # Extensibility hooks for sources
    MEMORY = "memory"
    DOCUMENT = "document"
    WEB = "web"
    GRAPH = "graph"
    DATABASE = "database"
    API = "api"
    GITHUB = "github"
    CONNECTOR = "connector"



class RetrievalScope(str, Enum):
    """Scope of document search."""
    PROJECT = "project"
    WORKSPACE = "workspace"


class RetrievalDecision(BaseModel):
    """
    Structured routing decision emitted by the Retrieval Router.
    Determines whether retrieval is required, which strategy and scope to use,
    and documents why the decision was made with a confidence score.
    """
    retrieval_required: bool = Field(..., description="Whether external document knowledge retrieval is required")
    strategy: RetrievalStrategy = Field(default=RetrievalStrategy.NONE, description="Selected retrieval strategy")
    scope: RetrievalScope = Field(default=RetrievalScope.PROJECT, description="Scoping boundary: project or workspace")
    top_k: int = Field(default=8, ge=1, le=50, description="Target number of candidate chunks to retrieve")
    query: str = Field(default="", description="Search query string extracted or constructed for retrieval")
    reason: str = Field(default="", description="Human-interpretable explanation of why this routing decision was chosen")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score of the routing decision")
    generated_queries: List[str] = Field(default_factory=list, description="Alternative queries generated for multi-query retrieval")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional contextual routing metadata")
