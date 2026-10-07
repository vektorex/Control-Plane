from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, desc

from backend.app.db.models.organizational_knowledge import (
    OrganizationalKnowledgeItem,
    KnowledgeProvenance,
    KnowledgeEvidence,
    KnowledgeVersion,
    KnowledgeCandidate,
    KnowledgeConflict,
)
from backend.app.services.organizational_knowledge.schemas import (
    OrganizationalKnowledgeItemCreate,
    OrganizationalKnowledgeItemUpdate,
    KnowledgeCandidateCreate,
    KnowledgeConflictCreate,
)

class OrganizationalKnowledgeRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_item(self, item_in: OrganizationalKnowledgeItemCreate, created_by: str) -> OrganizationalKnowledgeItem:
        import uuid
        item_id = str(uuid.uuid4())
        item = OrganizationalKnowledgeItem(
            id=item_id,
            **item_in.model_dump(),
            created_by=created_by
        )
        self.session.add(item)
        self.session.flush()
        return item

    def get_item(self, item_id: str) -> Optional[OrganizationalKnowledgeItem]:
        return self.session.execute(
            select(OrganizationalKnowledgeItem).where(OrganizationalKnowledgeItem.id == item_id)
        ).scalar_one_or_none()
        
    def list_items(self, workspace_id: str, project_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[OrganizationalKnowledgeItem]:
        query = select(OrganizationalKnowledgeItem).where(OrganizationalKnowledgeItem.workspace_id == workspace_id)
        if project_id:
            query = query.where(OrganizationalKnowledgeItem.project_id == project_id)
        query = query.order_by(desc(OrganizationalKnowledgeItem.created_at)).offset(skip).limit(limit)
        return list(self.session.execute(query).scalars().all())

    def update_item(self, item_id: str, update_data: Dict[str, Any]) -> Optional[OrganizationalKnowledgeItem]:
        item = self.get_item(item_id)
        if not item:
            return None
        for key, value in update_data.items():
            setattr(item, key, value)
        self.session.flush()
        return item
        
    def create_version(self, item_id: str, version_number: int, content: str, summary: str, classification: str, scope: str, provenance_snapshot: Dict[str, Any], created_by: str) -> KnowledgeVersion:
        import uuid
        version = KnowledgeVersion(
            id=str(uuid.uuid4()),
            knowledge_item_id=item_id,
            version=version_number,
            content=content,
            summary=summary,
            classification=classification,
            scope=scope,
            provenance_snapshot=provenance_snapshot,
            created_by=created_by
        )
        self.session.add(version)
        self.session.flush()
        return version

    def create_candidate(self, candidate_in: KnowledgeCandidateCreate) -> KnowledgeCandidate:
        import uuid
        candidate = KnowledgeCandidate(
            id=str(uuid.uuid4()),
            **candidate_in.model_dump()
        )
        self.session.add(candidate)
        self.session.flush()
        return candidate
        
    def get_candidate(self, candidate_id: str) -> Optional[KnowledgeCandidate]:
        return self.session.execute(
            select(KnowledgeCandidate).where(KnowledgeCandidate.id == candidate_id)
        ).scalar_one_or_none()

    def list_candidates(self, workspace_id: str, status: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[KnowledgeCandidate]:
        query = select(KnowledgeCandidate).where(KnowledgeCandidate.workspace_id == workspace_id)
        if status:
            query = query.where(KnowledgeCandidate.status == status)
        query = query.order_by(desc(KnowledgeCandidate.created_at)).offset(skip).limit(limit)
        return list(self.session.execute(query).scalars().all())

    def update_candidate_status(self, candidate_id: str, status: str) -> Optional[KnowledgeCandidate]:
        candidate = self.get_candidate(candidate_id)
        if candidate:
            candidate.status = status
            self.session.flush()
        return candidate

    def create_conflict(self, conflict_in: KnowledgeConflictCreate) -> KnowledgeConflict:
        import uuid
        conflict = KnowledgeConflict(
            id=str(uuid.uuid4()),
            **conflict_in.model_dump()
        )
        self.session.add(conflict)
        self.session.flush()
        return conflict

    def get_conflict(self, conflict_id: str) -> Optional[KnowledgeConflict]:
        return self.session.execute(
            select(KnowledgeConflict).where(KnowledgeConflict.id == conflict_id)
        ).scalar_one_or_none()
        
    def resolve_conflict(self, conflict_id: str, resolution: str, resolved_by: str) -> Optional[KnowledgeConflict]:
        conflict = self.get_conflict(conflict_id)
        if conflict:
            from datetime import datetime
            from datetime import timezone
            conflict.status = "resolved"
            conflict.resolution = resolution
            conflict.resolved_by = resolved_by
            conflict.resolved_at = datetime.now(timezone.utc)
            self.session.flush()
        return conflict
