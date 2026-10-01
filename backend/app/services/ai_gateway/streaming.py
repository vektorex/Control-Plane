import json
from typing import Any, AsyncIterator, Dict, Optional


class NormalizedStreamEvent:
    """Helper constructors for standard AI Gateway streaming events."""

    @staticmethod
    def delta(content: str, full_content: Optional[str] = None) -> Dict[str, Any]:
        evt = {"type": "delta", "content": content}
        if full_content is not None:
            evt["full_content"] = full_content
        return evt

    @staticmethod
    def usage(usage_dict: Dict[str, Any], estimated_cost: Optional[float] = None) -> Dict[str, Any]:
        data = dict(usage_dict)
        if estimated_cost is not None:
            data["estimated_cost"] = estimated_cost
        return {"type": "usage", "usage": data}

    @staticmethod
    def fallback(from_model: str, to_model: str, provider: str, attempt: int, reason: str = "") -> Dict[str, Any]:
        return {
            "type": "model_fallback",
            "from_model": from_model,
            "to_model": to_model,
            "provider": provider,
            "attempt": attempt,
            "reason": reason,
        }

    @staticmethod
    def completed(finish_reason: str = "stop") -> Dict[str, Any]:
        return {"type": "completed", "finish_reason": finish_reason}

    @staticmethod
    def error(message: str, code: str = "STREAM_ERROR") -> Dict[str, Any]:
        return {"type": "error", "error": {"code": code, "message": message}}


def format_sse(data: Dict[str, Any]) -> str:
    """Encode an event payload into a Server-Sent Events (SSE) data line."""
    return f"data: {json.dumps(data)}\n\n"
