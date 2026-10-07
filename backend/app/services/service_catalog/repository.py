from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_
from backend.app.db.models.service_catalog import ServiceCatalogItem
from .schemas import ServiceCatalogItemCreate, ServiceCatalogItemUpdate

class CatalogRepository:
    def __init__(self, session: Session):
        self.session = session

    def register_item(self, item_in: ServiceCatalogItemCreate) -> ServiceCatalogItem:
        import uuid
        existing = self.get_by_resource(item_in.resource_type, item_in.resource_id)
        if existing:
            return existing # Avoid duplication, could throw error instead based on policy

        item = ServiceCatalogItem(
            id=str(uuid.uuid4()),
            **item_in.model_dump()
        )
        self.session.add(item)
        self.session.flush()
        return item

    def get_item(self, item_id: str) -> Optional[ServiceCatalogItem]:
        return self.session.execute(
            select(ServiceCatalogItem).where(ServiceCatalogItem.id == item_id)
        ).scalar_one_or_none()
        
    def get_by_resource(self, resource_type: str, resource_id: str) -> Optional[ServiceCatalogItem]:
        return self.session.execute(
            select(ServiceCatalogItem).where(
                and_(
                    ServiceCatalogItem.resource_type == resource_type,
                    ServiceCatalogItem.resource_id == resource_id
                )
            )
        ).scalar_one_or_none()

    def list_items(self, filters: Dict[str, Any] = None) -> List[ServiceCatalogItem]:
        query = select(ServiceCatalogItem)
        if filters:
            conditions = []
            if "category" in filters:
                conditions.append(ServiceCatalogItem.category == filters["category"])
            if "status" in filters:
                conditions.append(ServiceCatalogItem.status == filters["status"])
            if "visibility" in filters:
                conditions.append(ServiceCatalogItem.visibility == filters["visibility"])
            if conditions:
                query = query.where(and_(*conditions))
        
        return list(self.session.execute(query).scalars().all())

    def update_item(self, item_id: str, updates: ServiceCatalogItemUpdate) -> Optional[ServiceCatalogItem]:
        item = self.get_item(item_id)
        if not item:
            return None
        update_data = updates.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(item, key, value)
        self.session.flush()
        return item

    def update_sync_status(self, item_id: str, freshness: str, synced_at: Any) -> None:
        item = self.get_item(item_id)
        if item:
            item.freshness_status = freshness
            item.last_synced_at = synced_at
            self.session.flush()
