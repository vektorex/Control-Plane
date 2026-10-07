from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from backend.app.api.deps import get_db, get_current_user
from backend.app.db.models.user import User
from backend.app.services.service_catalog.schemas import (
    ServiceCatalogItemCreate,
    ServiceCatalogItemResponse,
    CompatibilityRequest,
    CompatibilityResponse,
    EligibilityRequest,
    EligibilityResponse
)
from backend.app.services.service_catalog.service import CatalogService
from backend.app.services.events.service import EventBus

router = APIRouter()

def get_catalog_service(db: Session = Depends(get_db)):
    event_bus = EventBus()
    return CatalogService(db, event_bus)

@router.post("", response_model=ServiceCatalogItemResponse)
def register_item(
    item_in: ServiceCatalogItemCreate,
    current_user: User = Depends(get_current_user),
    service: CatalogService = Depends(get_catalog_service)
):
    return service.register_item(item_in)

@router.get("", response_model=List[ServiceCatalogItemResponse])
def list_items(
    category: str = None,
    status: str = None,
    visibility: str = None,
    current_user: User = Depends(get_current_user),
    service: CatalogService = Depends(get_catalog_service)
):
    filters = {}
    if category: filters["category"] = category
    if status: filters["status"] = status
    if visibility: filters["visibility"] = visibility
    return service.list_items(filters)
    
@router.post("/search", response_model=List[ServiceCatalogItemResponse])
def search_items(
    query: str,
    filters: Dict[str, Any] = None,
    current_user: User = Depends(get_current_user),
    service: CatalogService = Depends(get_catalog_service)
):
    return service.search_items(query, filters)

@router.get("/{item_id}", response_model=ServiceCatalogItemResponse)
def get_item(
    item_id: str,
    current_user: User = Depends(get_current_user),
    service: CatalogService = Depends(get_catalog_service)
):
    item = service.get_item(item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Catalog item not found")
    return item

@router.post("/{item_id}/compatibility", response_model=CompatibilityResponse)
def check_compatibility(
    item_id: str,
    request: CompatibilityRequest,
    current_user: User = Depends(get_current_user),
    service: CatalogService = Depends(get_catalog_service)
):
    return service.check_compatibility(item_id, request)
    
@router.post("/{item_id}/eligibility", response_model=EligibilityResponse)
def check_eligibility(
    item_id: str,
    request: EligibilityRequest,
    current_user: User = Depends(get_current_user),
    service: CatalogService = Depends(get_catalog_service)
):
    return service.check_eligibility(item_id, request)
