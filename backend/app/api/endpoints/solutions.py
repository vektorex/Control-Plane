from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from backend.app.api.deps import get_db, get_current_user
from backend.app.db.models.user import User
from backend.app.services.solutions.schemas import (
    SolutionCreate,
    SolutionUpdate,
    SolutionResponse,
    SolutionVersionResponse,
    ValidationResponse
)
from backend.app.services.solutions.service import SolutionService
from backend.app.services.events.service import EventBus

router = APIRouter()

def get_solution_service(db: Session = Depends(get_db)):
    event_bus = EventBus()
    return SolutionService(db, event_bus)

@router.post("", response_model=SolutionResponse)
def create_solution(
    obj_in: SolutionCreate,
    current_user: User = Depends(get_current_user),
    service: SolutionService = Depends(get_solution_service)
):
    return service.create_solution(obj_in)

@router.get("", response_model=List[SolutionResponse])
def list_solutions(
    status: str = None,
    visibility: str = None,
    current_user: User = Depends(get_current_user),
    service: SolutionService = Depends(get_solution_service)
):
    filters = {}
    if status: filters["status"] = status
    if visibility: filters["visibility"] = visibility
    return service.list_solutions(filters)

@router.get("/{solution_id}", response_model=SolutionResponse)
def get_solution(
    solution_id: str,
    current_user: User = Depends(get_current_user),
    service: SolutionService = Depends(get_solution_service)
):
    item = service.get_solution(solution_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solution not found")
    return item

@router.patch("/{solution_id}", response_model=SolutionResponse)
def update_solution(
    solution_id: str,
    updates: SolutionUpdate,
    current_user: User = Depends(get_current_user),
    service: SolutionService = Depends(get_solution_service)
):
    item = service.update_solution(solution_id, updates)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solution not found")
    return item

@router.get("/{solution_id}/versions", response_model=List[SolutionVersionResponse])
def list_versions(
    solution_id: str,
    current_user: User = Depends(get_current_user),
    service: SolutionService = Depends(get_solution_service)
):
    return service.get_versions(solution_id)

@router.post("/{solution_id}/validate", response_model=ValidationResponse)
def validate_solution(
    solution_id: str,
    current_user: User = Depends(get_current_user),
    service: SolutionService = Depends(get_solution_service)
):
    return service.validate_solution(solution_id)

@router.post("/{solution_id}/simulate")
def simulate_solution(
    solution_id: str,
    current_user: User = Depends(get_current_user),
    service: SolutionService = Depends(get_solution_service)
):
    return service.simulate_solution(solution_id)
