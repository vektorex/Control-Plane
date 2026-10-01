import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.db.models.observability import ExecutionTraceEvent
from backend.app.services.observability.events import TraceEventStatus, TraceEventType
from backend.app.services.observability.sanitizer import sanitize_metadata


class ExecutionTracer:
    """
    Execution tracer managing sequence numbering, in-memory event buffering,
    sanitization, and safe database persistence for a single Run.
    """

    def __init__(self, run_id: uuid.UUID, workspace_id: uuid.UUID) -> None:
        self.run_id = run_id
        self.workspace_id = workspace_id
        self.sequence_number = 0
        self.events: List[Dict[str, Any]] = []

    def record_event(
        self,
        event_type: Union[TraceEventType, str],
        step_type: Optional[str] = None,
        status: Union[TraceEventStatus, str] = TraceEventStatus.COMPLETED.value,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        duration_ms: Optional[int] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Records a sanitized trace event into the local run buffer with auto-incrementing sequence number.
        """
        self.sequence_number += 1
        now = datetime.now(timezone.utc)
        start = started_at or now
        end = completed_at or (now if status != TraceEventStatus.STARTED.value else None)

        if duration_ms is None and end and start:
            duration_ms = max(0, int((end.timestamp() - start.timestamp()) * 1000))

        sanitized_meta = sanitize_metadata(metadata)
        e_type = event_type.value if hasattr(event_type, "value") else str(event_type)
        e_status = status.value if hasattr(status, "value") else str(status)

        event_data = {
            "id": uuid.uuid4(),
            "run_id": self.run_id,
            "workspace_id": self.workspace_id,
            "sequence_number": self.sequence_number,
            "event_type": e_type,
            "step_type": step_type,
            "status": e_status,
            "started_at": start,
            "completed_at": end,
            "duration_ms": duration_ms,
            "model": model,
            "provider": provider,
            "metadata": sanitized_meta,
            "error_code": error_code,
            "created_at": now,
        }
        self.events.append(event_data)
        return event_data

    async def flush_to_db(self, session: AsyncSession) -> int:
        """
        Persists all buffered trace events to the database in a batch.
        Fail-safe: catches any database persistence errors without raising.
        """
        if not self.events:
            return 0

        to_flush = list(self.events)
        self.events.clear()

        try:
            db_objs = [
                ExecutionTraceEvent(
                    id=e["id"],
                    run_id=e["run_id"],
                    workspace_id=e["workspace_id"],
                    sequence_number=e["sequence_number"],
                    event_type=e["event_type"],
                    step_type=e["step_type"],
                    status=e["status"],
                    started_at=e["started_at"],
                    completed_at=e["completed_at"],
                    duration_ms=e["duration_ms"],
                    model=e["model"],
                    provider=e["provider"],
                    metadata_json=e["metadata"],
                    error_code=e["error_code"],
                    created_at=e["created_at"],
                )
                for e in to_flush
            ]
            session.add_all(db_objs)
            await session.flush()
            return len(db_objs)
        except Exception as exc:
            logger.warning(f"[ExecutionTracer] Failed to flush trace events to DB: {exc}")
            return 0
