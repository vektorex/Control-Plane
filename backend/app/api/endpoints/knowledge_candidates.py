from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db, get_current_user
from backend.app.db.models.user import User
from backend.app.services.organizational_knowledge.schemas import (
    KnowledgeCandidateCreate,
    KnowledgeCandidateResponse,
    OrganizationalKnowledgeItemResponse,
)
from backend.app.services.organizational_knowledge.service import OrganizationalKnowledgeService
from backend.app.services.events.service import EventBus

router = APIRouter()

def get_knowledge_service(db: Session = Depends(get_db)):
    event_bus = EventBus()
    return OrganizationalKnowledgeService(db, event_bus)

@router.post("", response_model=KnowledgeCandidateResponse)
def propose_candidate(
    candidate_in: KnowledgeCandidateCreate,
    current_user: User = Depends(get_current_user),
    service: OrganizationalKnowledgeService = Depends(get_knowledge_service)
):
    return service.propose_candidate(candidate_in)

@router.post("/{candidate_id}/accept", response_model=OrganizationalKnowledgeItemResponse)
def accept_candidate(
    candidate_id: str,
    current_user: User = Depends(get_current_user),
    service: OrganizationalKnowledgeService = Depends(get_knowledge_service)
):
    item = service.accept_candidate(candidate_id, str(current_user.id))
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    return item
