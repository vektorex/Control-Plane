"""
Recovery evidence bridge reusing Step 33 ComplianceEvidence.
"""
import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.app.services.data_governance.models import ComplianceEvidence


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RecoveryEvidenceBridge:
    """
    Records immutable recovery lifecycle evidence (backup created, verified, restore approved/executed)
    directly into Step 33 ComplianceEvidence with cryptographic hash chaining.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def record_evidence(
        self,
        organization_id: str,
        evidence_type: str,  # backup_created, backup_verified, restore_executed, recovery_exercise_completed
        subject_type: str,   # backup_run, restore_plan, recovery_exercise
        subject_id: str,
        action: str,
        result: str,
        actor_id: str = "system",
        workspace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ComplianceEvidence:
        """
        Record a tamper-evident compliance evidence entry chained to previous hash.
        """
        # Fetch previous evidence hash for org
        res = await self.session.execute(
            select(ComplianceEvidence)
            .where(ComplianceEvidence.organization_id == organization_id)
            .order_by(desc(ComplianceEvidence.timestamp))
            .limit(1)
        )
        prev_entry = res.scalar_one_or_none()
        previous_hash = prev_entry.evidence_hash if prev_entry else "0" * 64

        now = _utc_now()
        clean_metadata = metadata or {}

        # Compute deterministic evidence hash
        hash_payload = {
            "organization_id": organization_id,
            "evidence_type": evidence_type,
            "subject_type": subject_type,
            "subject_id": subject_id,
            "action": action,
            "result": result,
            "actor_id": actor_id,
            "timestamp": now.isoformat(),
            "previous_hash": previous_hash,
            "metadata": clean_metadata,
        }
        evidence_hash = hashlib.sha256(
            json.dumps(hash_payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()

        evidence = ComplianceEvidence(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            workspace_id=workspace_id,
            evidence_type=evidence_type,
            subject_type=subject_type,
            subject_id=subject_id,
            action=action,
            result=result,
            actor_type="user" if actor_id != "system" else "system",
            actor_id=actor_id,
            timestamp=now,
            evidence_hash=evidence_hash,
            previous_evidence_hash=previous_hash,
            evidence_metadata=clean_metadata,
        )
        self.session.add(evidence)
        await self.session.commit()
        return evidence
