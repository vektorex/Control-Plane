from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.app.api.deps import get_db, get_current_user
from backend.app.db.models.user import User
from backend.app.services.contracts.schemas import (
    WorkContractCreate,
    WorkContractResponse,
)
from backend.app.services.contracts.service import ContractService
from backend.app.services.events.service import EventBus

router = APIRouter()

def get_contract_service(db: Session = Depends(get_db)):
    event_bus = EventBus()
    return ContractService(db, event_bus)

@router.post("", response_model=WorkContractResponse)
def create_contract(
    contract_in: WorkContractCreate,
    current_user: User = Depends(get_current_user),
    service: ContractService = Depends(get_contract_service)
):
    return service.create_draft(contract_in, str(current_user.id))

@router.get("/{contract_id}", response_model=WorkContractResponse)
def get_contract(
    contract_id: str,
    current_user: User = Depends(get_current_user),
    service: ContractService = Depends(get_contract_service)
):
    contract = service.get_contract(contract_id)
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    return contract

@router.post("/{contract_id}/propose", response_model=WorkContractResponse)
def propose_contract(
    contract_id: str,
    current_user: User = Depends(get_current_user),
    service: ContractService = Depends(get_contract_service)
):
    contract = service.propose_contract(contract_id, str(current_user.id))
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    return contract

@router.post("/{contract_id}/approve", response_model=WorkContractResponse)
def approve_contract(
    contract_id: str,
    current_user: User = Depends(get_current_user),
    service: ContractService = Depends(get_contract_service)
):
    contract = service.approve_contract(contract_id, str(current_user.id))
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    return contract

@router.post("/{contract_id}/activate", response_model=WorkContractResponse)
def activate_contract(
    contract_id: str,
    current_user: User = Depends(get_current_user),
    service: ContractService = Depends(get_contract_service)
):
    contract = service.activate_contract(contract_id, str(current_user.id))
    if not contract:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Contract cannot be activated")
    return contract
