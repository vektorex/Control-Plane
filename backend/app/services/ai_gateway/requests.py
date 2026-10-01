import hashlib
import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GatewayRequest(BaseModel):
    """
    Normalized, provider-independent model execution request contract.
    No provider-specific vendor types are accepted here.
    """
    model: str = Field(..., description="Target model identifier or alias")
    provider: Optional[str] = Field(default=None, description="Optional target provider identifier")
    messages: List[Dict[str, Any]] = Field(..., description="Normalized chat messages with 'role' and 'content'")
    system_instruction: Optional[str] = Field(default=None, description="Optional system-level instruction")
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(default=None, gt=0, description="Max completion tokens to generate")
    stream: bool = Field(default=False, description="Whether to stream token deltas")
    tools: Optional[List[Dict[str, Any]]] = Field(default=None, description="Optional function/tool specifications")
    response_format: Optional[Dict[str, Any]] = Field(default=None, description="Optional response format (e.g. {'type': 'json_object'})")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Execution metadata (task_id, run_id, etc.)")
    timeout_ms: Optional[int] = Field(default=None, description="Optional per-request timeout in milliseconds")
    workspace_id: Optional[str] = Field(default=None, description="Workspace ID for policy and tenant isolation")

    def get_fingerprint(self) -> str:
        """
        Generate a safe deterministic fingerprint of the request metadata and structure
        for optional deduplication and architectural caching.
        Does NOT store or expose raw prompt contents.
        """
        data = {
            "model": self.model,
            "provider": self.provider,
            "system": bool(self.system_instruction),
            "msg_count": len(self.messages),
            "msg_roles": [m.get("role") for m in self.messages],
            "msg_lens": [len(str(m.get("content", ""))) for m in self.messages],
            "temp": self.temperature,
            "max_tokens": self.max_tokens,
            "tools": len(self.tools or []),
            "format": self.response_format,
        }
        encoded = json.dumps(data, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()
