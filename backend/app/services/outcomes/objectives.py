"""
Objective planning and lifecycle domain manager for Step 43:
AI Outcome Intelligence & Work Impact Layer.
"""
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.outcomes.models import Objective
from backend.app.services.outcomes.repository import OutcomeRepository
from backend.app.services.outcomes.schemas import ObjectiveCreate, ObjectiveUpdate


class ObjectiveManager:
    """Manages strategic objectives and their planning structures."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = OutcomeRepository(session)

    async def get_objective_summary(self, objective_id: str, workspace_id: str) -> Dict[str, Any]:
        obj = await self.repo.get_objective(objective_id, workspace_id)
        if not obj:
            return {}
        return {
            "id": obj.id,
            "name": obj.name,
            "type": obj.objective_type,
            "status": obj.status,
            "priority": obj.priority,
            "target_count": len(obj.targets),
            "milestone_count": len(obj.milestones),
            "outcome_count": len(obj.outcomes),
        }
