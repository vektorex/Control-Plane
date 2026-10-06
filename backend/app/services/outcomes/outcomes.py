"""
Outcome domain manager for Step 43:
AI Outcome Intelligence & Work Impact Layer.
"""
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.outcomes.models import Outcome
from backend.app.services.outcomes.repository import OutcomeRepository


class OutcomeManager:
    """Manages outcomes and links to work executions."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = OutcomeRepository(session)

    async def get_outcome_summary(self, outcome_id: str, workspace_id: str) -> Dict[str, Any]:
        outcome = await self.repo.get_outcome(outcome_id, workspace_id)
        if not outcome:
            return {}
        return {
            "id": outcome.id,
            "name": outcome.name,
            "outcome_type": outcome.outcome_type,
            "status": outcome.status,
            "confidence": outcome.confidence,
            "evidence_count": len(outcome.evidence),
            "work_links_count": len(outcome.work_links),
            "measurements_count": len(outcome.measurements),
            "attributions_count": len(outcome.attributions),
        }
