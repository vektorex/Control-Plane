from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from .repository import CatalogRepository
from .schemas import (
    ServiceCatalogItemCreate, 
    ServiceCatalogItemUpdate,
    CompatibilityRequest,
    CompatibilityResponse,
    EligibilityRequest,
    EligibilityResponse
)
from backend.app.db.models.service_catalog import ServiceCatalogItem
from backend.app.services.events.service import EventBus

class CatalogService:
    def __init__(self, session: Session, event_bus: EventBus):
        self.session = session
        self.repository = CatalogRepository(session)
        self.event_bus = event_bus

    def register_item(self, item_in: ServiceCatalogItemCreate) -> ServiceCatalogItem:
        item = self.repository.register_item(item_in)
        self.event_bus.publish(
            "catalog.item_registered",
            {
                "item_id": item.id,
                "resource_type": item.resource_type,
                "resource_id": item.resource_id
            }
        )
        return item

    def get_item(self, item_id: str) -> Optional[ServiceCatalogItem]:
        return self.repository.get_item(item_id)

    def list_items(self, filters: Dict[str, Any] = None) -> List[ServiceCatalogItem]:
        return self.repository.list_items(filters)

    def search_items(self, query: str, filters: Dict[str, Any] = None) -> List[ServiceCatalogItem]:
        # Basic mock implementation of search. Would typically use pg_trgm or pgvector
        all_items = self.repository.list_items(filters)
        if not query:
            return all_items
        
        query = query.lower()
        results = []
        for item in all_items:
            if query in item.name.lower() or (item.description and query in item.description.lower()) or query in item.category.lower():
                results.append(item)
        return results

    def check_compatibility(self, item_id: str, request: CompatibilityRequest) -> CompatibilityResponse:
        item = self.get_item(item_id)
        if not item:
            return CompatibilityResponse(
                status="unknown", 
                reasons=["Item not found"], 
                missing_requirements=[], 
                incompatible_requirements=[]
            )
        
        missing = []
        incompatible = []
        
        # Example validation logic
        if request.required_tools:
            for tool in request.required_tools:
                if tool not in item.required_tools:
                    missing.append(f"Tool {tool} is not supported by this capability.")
                    
        if missing or incompatible:
            return CompatibilityResponse(
                status="conditionally_compatible" if len(incompatible) == 0 else "incompatible",
                reasons=["Requirements not fully met"],
                missing_requirements=missing,
                incompatible_requirements=incompatible
            )
            
        return CompatibilityResponse(
            status="compatible",
            reasons=["All requested requirements are met by this capability."],
            missing_requirements=[],
            incompatible_requirements=[]
        )

    def check_eligibility(self, item_id: str, request: EligibilityRequest) -> EligibilityResponse:
        item = self.get_item(item_id)
        if not item:
            return EligibilityResponse(status="unknown", reasons=["Item not found"])
            
        # Example RBAC/Governance check stub
        if item.visibility == "private" and item.workspace_id != request.workspace_id:
            return EligibilityResponse(
                status="ineligible", 
                reasons=["This capability is private to another workspace and cannot be executed here."]
            )
            
        return EligibilityResponse(
            status="eligible", 
            reasons=["User and workspace meet all governance requirements to utilize this capability."]
        )
