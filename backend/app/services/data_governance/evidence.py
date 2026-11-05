"""
Tamper-evident, hash-chained compliance evidence engine for Step 33.
"""
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.data_governance.models import ComplianceEvidence
from backend.app.services.data_governance.redaction import sanitize_payload


def canonical_json(data: Any) -> str:
    """
    Serializes a data structure into deterministic, canonical JSON for hashing.
    """
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def compute_evidence_hash(previous_hash: Optional[str], canonical_data: str) -> str:
    """
    Computes cryptographic SHA-256 hash linking this evidence to the previous record.
    """
    chain_input = f"{previous_hash or 'GENESIS'}:{canonical_data}"
    return hashlib.sha256(chain_input.encode("utf-8")).hexdigest()


class ComplianceEvidenceService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_latest_hash(self, organization_id: str, workspace_id: Optional[str] = None) -> Optional[str]:
        """
        Retrieves the most recent evidence_hash in the chain for an organization or workspace.
        """
        query = select(ComplianceEvidence.evidence_hash).where(
            ComplianceEvidence.organization_id == str(organization_id)
        )
        if workspace_id:
            query = query.where(ComplianceEvidence.workspace_id == str(workspace_id))
        query = query.order_by(desc(ComplianceEvidence.timestamp), desc(ComplianceEvidence.id)).limit(1)

        result = await self.session.execute(query)
        row = result.first()
        return row[0] if row else None

    async def record_evidence(
        self,
        organization_id: str,
        evidence_type: str,
        subject_type: str,
        subject_id: str,
        action: str,
        result: str,
        actor_type: str = "system",
        actor_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        policy_version_id: Optional[str] = None,
        governance_decision_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> ComplianceEvidence:
        """
        Creates an immutable, cryptographically chained compliance evidence record.
        Sanitizes metadata to prevent secret leakage in evidence logs.
        """
        org_id_str = str(organization_id)
        ws_id_str = str(workspace_id) if workspace_id is not None else None
        subj_id_str = str(subject_id)
        act_id_str = str(actor_id) if actor_id is not None else None
        pol_ver_str = str(policy_version_id) if policy_version_id is not None else None
        gov_dec_str = str(governance_decision_id) if governance_decision_id is not None else None

        ts = timestamp or datetime.now(timezone.utc)
        sanitized_meta = sanitize_payload(metadata or {})

        prev_hash = await self.get_latest_hash(org_id_str, ws_id_str)

        canonical_content = canonical_json({
            "organization_id": org_id_str,
            "workspace_id": ws_id_str,
            "evidence_type": evidence_type,
            "subject_type": subject_type,
            "subject_id": subj_id_str,
            "action": action,
            "result": result,
            "actor_type": actor_type,
            "actor_id": act_id_str,
            "policy_version_id": pol_ver_str,
            "governance_decision_id": gov_dec_str,
            "timestamp": ts.isoformat(),
            "metadata": sanitized_meta,
        })

        record_hash = compute_evidence_hash(prev_hash, canonical_content)

        record = ComplianceEvidence(
            organization_id=org_id_str,
            workspace_id=ws_id_str,
            evidence_type=evidence_type,
            subject_type=subject_type,
            subject_id=subj_id_str,
            action=action,
            result=result,
            policy_version_id=pol_ver_str,
            governance_decision_id=gov_dec_str,
            actor_type=actor_type,
            actor_id=act_id_str,
            timestamp=ts,
            evidence_hash=record_hash,
            previous_evidence_hash=prev_hash,
            evidence_metadata=sanitized_meta,
        )

        self.session.add(record)
        await self.session.flush()
        await self.session.refresh(record)
        return record

    async def verify_chain(
        self,
        organization_id: str,
        workspace_id: Optional[str] = None,
    ) -> Tuple[bool, int, List[str]]:
        """
        Validates the hash chain integrity across all records in chronological order.
        Returns (is_valid, total_checked, broken_record_ids).
        """
        query = select(ComplianceEvidence).where(
            ComplianceEvidence.organization_id == str(organization_id)
        )
        if workspace_id:
            query = query.where(ComplianceEvidence.workspace_id == str(workspace_id))
        query = query.order_by(ComplianceEvidence.timestamp.asc(), ComplianceEvidence.id.asc())

        res = await self.session.execute(query)
        records = res.scalars().all()

        if not records:
            return True, 0, []

        broken = []
        expected_prev_hash: Optional[str] = None

        for rec in records:
            if rec.previous_evidence_hash != expected_prev_hash:
                broken.append(rec.id)

            canonical_content = canonical_json({
                "organization_id": rec.organization_id,
                "workspace_id": rec.workspace_id,
                "evidence_type": rec.evidence_type,
                "subject_type": rec.subject_type,
                "subject_id": rec.subject_id,
                "action": rec.action,
                "result": rec.result,
                "actor_type": rec.actor_type,
                "actor_id": rec.actor_id,
                "policy_version_id": rec.policy_version_id,
                "governance_decision_id": rec.governance_decision_id,
                "timestamp": rec.timestamp.isoformat(),
                "metadata": rec.evidence_metadata or {},
            })

            computed_hash = compute_evidence_hash(rec.previous_evidence_hash, canonical_content)
            if rec.evidence_hash != computed_hash:
                if rec.id not in broken:
                    broken.append(rec.id)

            expected_prev_hash = rec.evidence_hash

        return len(broken) == 0, len(records), broken
