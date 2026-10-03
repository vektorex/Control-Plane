"""
Sanitized, bounded execution checkpoint manager for Step 35: AI Reliability, Resilience & Chaos Engineering Layer.
Integrates with Step 33 Data Governance to respect retention lifecycle and sensitive data masking.
Never persists unredacted secrets or credentials.
"""
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.data_governance.redaction import detect_findings, sanitize_text
from backend.app.services.reliability.exceptions import CheckpointNotFoundError
from backend.app.services.reliability.models import ExecutionCheckpoint
from backend.app.services.reliability.schemas import ExecutionCheckpointCreate
from backend.app.services.reliability.validators import (
    compute_state_fingerprint,
    validate_checkpoint_integrity,
)


def _sanitize_snapshot(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively scans and redacts secrets from the state snapshot before saving.
    """
    if not isinstance(snapshot, dict):
        return {}

    sanitized = {}
    for k, v in snapshot.items():
        if isinstance(v, str):
            sanitized[k] = sanitize_text(v)
        elif isinstance(v, dict):
            sanitized[k] = _sanitize_snapshot(v)
        elif isinstance(v, list):
            sanitized[k] = [
                sanitize_text(item) if isinstance(item, str) else item for item in v
            ]
        else:
            sanitized[k] = v
    return sanitized


class CheckpointService:
    """Manages creation, query, and pruning of execution checkpoints."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_checkpoint(self, data: ExecutionCheckpointCreate) -> ExecutionCheckpoint:
        # Sanitize snapshot to prevent secret leakage
        clean_snapshot = _sanitize_snapshot(data.state_snapshot)

        # Validate integrity
        validate_checkpoint_integrity(
            state_snapshot=clean_snapshot,
            input_fingerprint=data.input_fingerprint,
            context_fingerprint=data.context_fingerprint,
        )

        cp = ExecutionCheckpoint(
            organization_id=data.organization_id,
            workspace_id=data.workspace_id,
            project_id=data.project_id,
            run_id=data.run_id,
            workflow_run_id=data.workflow_run_id,
            job_id=data.job_id,
            step_id=data.step_id,
            sequence_number=data.sequence_number,
            checkpoint_type=data.checkpoint_type,
            state_snapshot=clean_snapshot,
            input_fingerprint=data.input_fingerprint,
            context_fingerprint=data.context_fingerprint,
            expires_at=data.expires_at,
        )
        self.session.add(cp)
        await self.session.commit()
        await self.session.refresh(cp)
        return cp

    async def get_checkpoint(self, checkpoint_id: str, organization_id: Optional[str] = None) -> ExecutionCheckpoint:
        stmt = select(ExecutionCheckpoint).where(ExecutionCheckpoint.id == checkpoint_id)
        if organization_id:
            stmt = stmt.where(ExecutionCheckpoint.organization_id == organization_id)

        res = await self.session.execute(stmt)
        cp = res.scalars().first()
        if not cp:
            raise CheckpointNotFoundError(f"Execution checkpoint '{checkpoint_id}' not found.")
        return cp

    async def get_latest_checkpoint_for_run(
        self,
        run_id: str,
        organization_id: Optional[str] = None,
    ) -> Optional[ExecutionCheckpoint]:
        stmt = select(ExecutionCheckpoint).where(ExecutionCheckpoint.run_id == run_id)
        if organization_id:
            stmt = stmt.where(ExecutionCheckpoint.organization_id == organization_id)
        stmt = stmt.order_by(ExecutionCheckpoint.sequence_number.desc())

        res = await self.session.execute(stmt)
        return res.scalars().first()

    async def list_checkpoints(
        self,
        organization_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        run_id: Optional[str] = None,
        workflow_run_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ExecutionCheckpoint]:
        stmt = select(ExecutionCheckpoint)
        if organization_id:
            stmt = stmt.where(ExecutionCheckpoint.organization_id == organization_id)
        if workspace_id:
            stmt = stmt.where(ExecutionCheckpoint.workspace_id == workspace_id)
        if run_id:
            stmt = stmt.where(ExecutionCheckpoint.run_id == run_id)
        if workflow_run_id:
            stmt = stmt.where(ExecutionCheckpoint.workflow_run_id == workflow_run_id)

        stmt = stmt.order_by(ExecutionCheckpoint.created_at.desc()).offset(offset).limit(limit)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def invalidate_checkpoint(self, checkpoint_id: str, organization_id: Optional[str] = None) -> None:
        cp = await self.get_checkpoint(checkpoint_id, organization_id)
        await self.session.delete(cp)
        await self.session.commit()
