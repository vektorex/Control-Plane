"""
Work Decision and Provenance Tracking for Step 43:
AI Outcome Intelligence & Work Impact Layer.
Answers 'Why was this decision made?' with transparent provenance without exposing raw chain-of-thought.
"""
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.services.outcomes.models import WorkDecision
from backend.app.services.outcomes.repository import OutcomeRepository
from backend.app.services.outcomes.registry import WorkDecisionType


class DecisionProvenanceTracker:
    """Manages work decision provenance and ensures AI decisions are not masked as human decisions."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = OutcomeRepository(session)

    @staticmethod
    def sanitize_provenance_payload(provenance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts structured provenance keys without leaking private reasoning tokens.
        Allowed keys: agent_id, agent_version_id, run_id, model_provider, prompt_version, evidence_ids, evaluation_id, approval_id.
        """
        ALLOWED_PROVENANCE_KEYS = {
            "agent_id",
            "agent_version_id",
            "run_id",
            "model_provider",
            "prompt_version",
            "evidence_ids",
            "evaluation_id",
            "approval_id",
            "approved_by",
            "approved_at",
            "rejected_by",
            "rejected_at",
            "rejection_reason",
        }
        return {k: v for k, v in provenance.items() if k in ALLOWED_PROVENANCE_KEYS}
