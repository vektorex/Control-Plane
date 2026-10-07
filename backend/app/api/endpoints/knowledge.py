from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db, get_current_user
from backend.app.db.models.user import User
from backend.app.services.organizational_knowledge.schemas import (
    OrganizationalKnowledgeItemCreate,
    OrganizationalKnowledgeItemUpdate,
    OrganizationalKnowledgeItemResponse,
)
from backend.app.services.organizational_knowledge.service import OrganizationalKnowledgeService
from backend.app.services.events.service import EventBus

router = APIRouter()

def get_knowledge_service(db: Session = Depends(get_db)):
    event_bus = EventBus()
    return OrganizationalKnowledgeService(db, event_bus)

@router.post("", response_model=OrganizationalKnowledgeItemResponse)
def create_knowledge_item(
    item_in: OrganizationalKnowledgeItemCreate,
    current_user: User = Depends(get_current_user),
    service: OrganizationalKnowledgeService = Depends(get_knowledge_service)
):
    return service.create_knowledge_item(item_in, str(current_user.id))

@router.get("/{knowledge_id}", response_model=OrganizationalKnowledgeItemResponse)
def get_knowledge_item(
    knowledge_id: str,
    current_user: User = Depends(get_current_user),
    service: OrganizationalKnowledgeService = Depends(get_knowledge_service)
):
    item = service.get_knowledge_item(knowledge_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge item not found")
    return item

@router.post("/{knowledge_id}/verify", response_model=OrganizationalKnowledgeItemResponse)
def verify_knowledge_item(
    knowledge_id: str,
    current_user: User = Depends(get_current_user),
    service: OrganizationalKnowledgeService = Depends(get_knowledge_service)
):
    item = service.verify_knowledge_item(knowledge_id, str(current_user.id))
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge item not found")
    return item
