from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from backend.app.api.deps import get_db, get_current_user
from backend.app.db.models.user import User
from backend.app.services.intent_solution.schemas import (
    IntentRequestCreate,
    IntentRequestResponse,
    ValidationResponse
)
from backend.app.services.intent_solution.service import IntentService
from backend.app.services.events.service import EventBus

router = APIRouter()

def get_intent_service(db: Session = Depends(get_db)):
    event_bus = EventBus()
    return IntentService(db, event_bus)

@router.post("", response_model=IntentRequestResponse)
def create_intent(
    obj_in: IntentRequestCreate,
    current_user: User = Depends(get_current_user),
    service: IntentService = Depends(get_intent_service)
):
    return service.create_intent(obj_in)

@router.get("", response_model=List[IntentRequestResponse])
def list_intents(
    status: str = None,
    current_user: User = Depends(get_current_user),
    service: IntentService = Depends(get_intent_service)
):
    filters = {}
    if status: filters["status"] = status
    return service.list_intents(filters)

@router.get("/{request_id}", response_model=IntentRequestResponse)
def get_intent(
    request_id: str,
    current_user: User = Depends(get_current_user),
    service: IntentService = Depends(get_intent_service)
):
    item = service.get_intent(request_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Intent request not found")
    return item

@router.post("/{request_id}/analyze", response_model=IntentRequestResponse)
def analyze_intent(
    request_id: str,
    current_user: User = Depends(get_current_user),
    service: IntentService = Depends(get_intent_service)
):
    item = service.analyze_intent(request_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Intent request not found")
    return item

@router.post("/{request_id}/candidates/{candidate_id}/validate", response_model=ValidationResponse)
def validate_candidate(
    request_id: str,
    candidate_id: str,
    current_user: User = Depends(get_current_user),
    service: IntentService = Depends(get_intent_service)
):
    return service.validate_candidate(candidate_id)

@router.post("/{request_id}/candidates/{candidate_id}/simulate")
def simulate_candidate(
    request_id: str,
    candidate_id: str,
    current_user: User = Depends(get_current_user),
    service: IntentService = Depends(get_intent_service)
):
    return service.simulate_candidate(candidate_id)

@router.post("/{request_id}/candidates/{candidate_id}/convert")
def convert_candidate(
    request_id: str,
    candidate_id: str,
    current_user: User = Depends(get_current_user),
    service: IntentService = Depends(get_intent_service)
):
    return service.convert_candidate(request_id, candidate_id)
