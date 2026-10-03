"""
Idempotency Management for Public API Mutations.
Step 37: Public API, Developer Platform & SDK Layer.
"""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from typing import Any, Dict, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.developer_platform.errors import IdempotencyConflictError
from backend.app.services.developer_platform.models import APIIdempotencyRecord


class IdempotencyService:
    """Manages request idempotency to guarantee at-most-once execution for mutations."""

    DEFAULT_TTL_HOURS = 24

    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def compute_fingerprint(method: str, endpoint: str, body: Any) -> str:
        """Computes deterministic SHA-256 fingerprint of the request payload and target."""
        raw = f"{method.upper()}:{endpoint}:"
        if isinstance(body, (dict, list)):
            raw += json.dumps(body, sort_keys=True, separators=(",", ":"))
        elif body:
            raw += str(body)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    async def check_idempotency(
        self,
        application_id: str,
        idempotency_key: str,
        fingerprint: str,
    ) -> Optional[Tuple[int, Dict[str, Any]]]:
        """
        Checks if an idempotency key was previously processed.
        Returns (status_code, response_data) if already completed with identical payload.
        Raises IdempotencyConflictError if key reused with differing payload.
        """
        now = datetime.now(timezone.utc)
        query = select(APIIdempotencyRecord).where(
            APIIdempotencyRecord.application_id == application_id,
            APIIdempotencyRecord.idempotency_key == idempotency_key,
            APIIdempotencyRecord.expires_at > now,
        )
        result = await self.session.execute(query)
        record: Optional[APIIdempotencyRecord] = result.scalars().first()

        if not record:
            return None

        # Check payload fingerprint match
        if record.request_fingerprint != fingerprint:
            raise IdempotencyConflictError(
                f"Idempotency key '{idempotency_key}' was previously used with a different request payload."
            )

        # Replay cached response
        cached_response = {}
        if record.response_reference:
            try:
                cached_response = json.loads(record.response_reference)
            except Exception:
                cached_response = {"data": record.response_reference}

        return record.status_code, cached_response

    async def record_response(
        self,
        organization_id: str,
        application_id: str,
        credential_id: str,
        endpoint: str,
        idempotency_key: str,
        fingerprint: str,
        status_code: int,
        response_data: Any,
        ttl_hours: Optional[int] = None,
    ) -> APIIdempotencyRecord:
        """Stores the response of an executed mutation under the idempotency key."""
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=ttl_hours or self.DEFAULT_TTL_HOURS)

        serialized = ""
        if isinstance(response_data, (dict, list)):
            serialized = json.dumps(response_data)
        elif response_data is not None:
            serialized = str(response_data)

        record = APIIdempotencyRecord(
            organization_id=organization_id,
            application_id=application_id,
            credential_id=credential_id,
            endpoint=endpoint,
            idempotency_key=idempotency_key,
            request_fingerprint=fingerprint,
            response_reference=serialized,
            status_code=status_code,
            created_at=now,
            expires_at=expires_at,
        )
        self.session.add(record)
        await self.session.commit()
        return record

IdempotencyManager = IdempotencyService
