"""
EventSanitizer for Step 26: Unified Event Bus.
Enforces rigorous stripping of sensitive credentials, keys, chain-of-thought,
and internal security tokens, as well as byte budget truncation.
"""
import json
from typing import Any, Dict, List, Union
from backend.app.config import settings
from backend.app.services.events.constants import SENSITIVE_KEYS
from backend.app.services.events.errors import EventPayloadTooLargeError
from backend.app.services.events.schemas import ActorSchema, AggregateSchema, EventContract


class EventSanitizer:
    """
    Centralized sanitization barrier ensuring no secrets, credentials, or internal thoughts
    ever leak into the durable event store, SSE stream, or API responses.
    """

    MAX_FIELD_STRING_LEN = 8192  # 8 KB per individual string field

    @classmethod
    def sanitize_dict(cls, data: Any, depth: int = 0) -> Any:
        if depth > 10:
            return "[NESTING_LIMIT_REACHED]"

        if isinstance(data, dict):
            clean = {}
            for k, v in data.items():
                lower_key = str(k).lower()
                # Check for sensitive key patterns
                if any(secret_term in lower_key for secret_term in SENSITIVE_KEYS):
                    clean[k] = "[REDACTED]"
                elif isinstance(v, (dict, list)):
                    clean[k] = cls.sanitize_dict(v, depth + 1)
                elif isinstance(v, str):
                    if len(v) > cls.MAX_FIELD_STRING_LEN:
                        clean[k] = v[:cls.MAX_FIELD_STRING_LEN] + "... [TRUNCATED]"
                    else:
                        clean[k] = v
                else:
                    clean[k] = v
            return clean

        elif isinstance(data, list):
            return [cls.sanitize_dict(item, depth + 1) for item in data[:100]]

        elif isinstance(data, str):
            if len(data) > cls.MAX_FIELD_STRING_LEN:
                return data[:cls.MAX_FIELD_STRING_LEN] + "... [TRUNCATED]"
            return data

        return data

    @classmethod
    def validate_and_sanitize_payload(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitizes dictionary and asserts that serialized size does not exceed EVENT_MAX_PAYLOAD_BYTES.
        """
        max_bytes = getattr(settings, "EVENT_MAX_PAYLOAD_BYTES", 65536)

        # Check raw input size
        try:
            raw_serialized = json.dumps(payload or {})
            if len(raw_serialized.encode("utf-8")) > max_bytes:
                raise EventPayloadTooLargeError(len(raw_serialized.encode("utf-8")), max_bytes)
        except EventPayloadTooLargeError:
            raise
        except Exception:
            pass

        clean = cls.sanitize_dict(payload or {})
        try:
            serialized = json.dumps(clean)
        except Exception:
            clean = {"error": "Invalid un-serializable payload content"}
            serialized = json.dumps(clean)

        if len(serialized.encode("utf-8")) > max_bytes:
            raise EventPayloadTooLargeError(len(serialized.encode("utf-8")), max_bytes)

        return clean

    @classmethod
    def validate_and_sanitize_metadata(cls, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitizes metadata and enforces EVENT_MAX_METADATA_BYTES.
        """
        clean = cls.sanitize_dict(metadata or {})
        try:
            serialized = json.dumps(clean)
        except Exception:
            clean = {"error": "Invalid un-serializable metadata content"}
            serialized = json.dumps(clean)

        max_bytes = getattr(settings, "EVENT_MAX_METADATA_BYTES", 16384)
        if len(serialized.encode("utf-8")) > max_bytes:
            clean = {"truncated": True, "notice": "Metadata exceeded byte budget"}

        return clean

    @classmethod
    def to_contract(cls, event: Any) -> EventContract:
        """
        Converts a database Event entity to a safe, standardized EventContract.
        """
        actor = ActorSchema(
            type=str(getattr(event, "actor_type", "system")),
            id=str(getattr(event, "actor_id", "")) if getattr(event, "actor_id", None) else None,
        )
        aggregate = AggregateSchema(
            type=str(getattr(event, "aggregate_type", "system")),
            id=str(getattr(event, "aggregate_id", "")),
        )

        clean_payload = cls.sanitize_dict(getattr(event, "payload", {}) or {})
        clean_metadata = cls.sanitize_dict(getattr(event, "metadata_json", {}) or {})

        created_at_dt = getattr(event, "created_at", None)
        timestamp_str = created_at_dt.isoformat() if created_at_dt else ""

        return EventContract(
            id=str(getattr(event, "id")),
            type=str(getattr(event, "event_type")),
            timestamp=timestamp_str,
            workspace_id=str(getattr(event, "workspace_id")),
            project_id=str(getattr(event, "project_id")) if getattr(event, "project_id", None) else None,
            actor=actor,
            aggregate=aggregate,
            parent_event_id=str(getattr(event, "parent_event_id")) if getattr(event, "parent_event_id", None) else None,
            correlation_id=str(getattr(event, "correlation_id")) if getattr(event, "correlation_id", None) else None,
            causation_id=str(getattr(event, "causation_id")) if getattr(event, "causation_id", None) else None,
            sequence_number=getattr(event, "sequence_number", None),
            data=clean_payload,
            metadata=clean_metadata,
        )
