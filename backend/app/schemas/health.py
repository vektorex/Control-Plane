from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="healthy", description="Backend service status")
    version: str = Field(description="Backend semantic version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="UTC timestamp")
    environment: str = Field(description="Runtime environment")
    providers_configured: List[str] = Field(default_factory=list, description="List of configured LLM providers")
