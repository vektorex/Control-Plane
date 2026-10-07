from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.api.deps import get_db, get_current_user
from backend.app.db.models.user import User
from backend.app.services.organizational_knowledge.schemas import (
    KnowledgeConflictCreate,
    KnowledgeConflictResponse,
)
from backend.app.services.organizational_knowledge.service import OrganizationalKnowledgeService
from backend.app.services.events.service import EventBus

router = APIRouter()

def get_knowledge_service(db: Session = Depends(get_db)):
    event_bus = EventBus()
    return OrganizationalKnowledgeService(db, event_bus)

class ConflictResolution(BaseModel):
    resolution: str

@router.post("", response_model=KnowledgeConflictResponse)
def report_conflict(
    conflict_in: KnowledgeConflictCreate,
    current_user: User = Depends(get_current_user),
    service: OrganizationalKnowledgeService = Depends(get_knowledge_service)
):
    return service.report_conflict(conflict_in, str(current_user.id))

@router.post("/{conflict_id}/resolve", response_model=KnowledgeConflictResponse)
def resolve_conflict(
    conflict_id: str,
    resolution: ConflictResolution,
    current_user: User = Depends(get_current_user),
    service: OrganizationalKnowledgeService = Depends(get_knowledge_service)
):
    conflict = service.resolve_conflict(conflict_id, resolution.resolution, str(current_user.id))
    if not conflict:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conflict not found")
    return conflict
