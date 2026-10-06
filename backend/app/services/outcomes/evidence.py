"""
Evidence Provenance and Collection Manager for Step 43:
AI Outcome Intelligence & Work Impact Layer.
Ensures every evidence item retains strict provenance and validation status.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import hashlib
import json

from backend.app.services.outcomes.models import OutcomeEvidence
from backend.app.services.outcomes.registry import EvidenceStatus, EvidenceType


class EvidenceProvenanceValidator:
    """Validates evidence provenance and tamper resistance."""

    @staticmethod
    def compute_evidence_fingerprint(snapshot: Dict[str, Any]) -> str:
        """Computes a SHA256 digest of the evidence snapshot."""
        serialized = json.dumps(snapshot, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @staticmethod
    def validate_provenance_record(evidence: OutcomeEvidence) -> bool:
        """Ensures source_type and source_id are populated and valid."""
        return bool(evidence.source_type and evidence.source_id and evidence.evidence_type)
