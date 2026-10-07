from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from backend.app.api.deps import get_db, get_current_user
from backend.app.db.models.user import User
from backend.app.services.decision_intelligence.schemas import (
    DecisionRequestCreate,
    DecisionRequestResponse,
)
from backend.app.services.decision_intelligence.service import DecisionService
from backend.app.services.events.service import EventBus

router = APIRouter()

def get_decision_service(db: Session = Depends(get_db)):
    event_bus = EventBus()
    return DecisionService(db, event_bus)

@router.post("", response_model=DecisionRequestResponse)
def create_decision(
    obj_in: DecisionRequestCreate,
    current_user: User = Depends(get_current_user),
    service: DecisionService = Depends(get_decision_service)
):
    return service.create_request(obj_in)

@router.get("", response_model=List[DecisionRequestResponse])
def list_decisions(
    status: str = None,
    current_user: User = Depends(get_current_user),
    service: DecisionService = Depends(get_decision_service)
):
    filters = {}
    if status: filters["status"] = status
    return service.list_requests(filters)

@router.get("/{decision_id}", response_model=DecisionRequestResponse)
def get_decision(
    decision_id: str,
    current_user: User = Depends(get_current_user),
    service: DecisionService = Depends(get_decision_service)
):
    item = service.get_request(decision_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision not found")
    return item

@router.post("/{decision_id}/evaluate", response_model=DecisionRequestResponse)
def evaluate_decision(
    decision_id: str,
    current_user: User = Depends(get_current_user),
    service: DecisionService = Depends(get_decision_service)
):
    item = service.evaluate(decision_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision not found")
    return item

@router.post("/execution-readiness")
def execution_readiness(
    subject_type: str,
    subject_id: str,
    current_user: User = Depends(get_current_user),
    service: DecisionService = Depends(get_decision_service)
):
    return service.assess_execution_readiness(subject_type, subject_id)
