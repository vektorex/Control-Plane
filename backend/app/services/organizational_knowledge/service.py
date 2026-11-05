from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from .repository import OrganizationalKnowledgeRepository
from .schemas import (
    OrganizationalKnowledgeItemCreate,
    OrganizationalKnowledgeItemUpdate,
    KnowledgeCandidateCreate,
    KnowledgeConflictCreate,
)
from backend.app.db.models.organizational_knowledge import (
    OrganizationalKnowledgeItem,
    KnowledgeCandidate,
    KnowledgeConflict,
)
from backend.app.services.events.service import EventBus
from backend.app.core.auth import get_current_user

class OrganizationalKnowledgeService:
    def __init__(self, session: Session, event_bus: EventBus):
        self.session = session
        self.repository = OrganizationalKnowledgeRepository(session)
        self.event_bus = event_bus

    def create_knowledge_item(self, item_in: OrganizationalKnowledgeItemCreate, current_user_id: str) -> OrganizationalKnowledgeItem:
        item = self.repository.create_item(item_in, current_user_id)
        
        # Publish event
        self.event_bus.publish(
            "knowledge.created",
            {
                "item_id": item.id,
                "workspace_id": item.workspace_id,
                "created_by": current_user_id
            }
        )
        return item

    def get_knowledge_item(self, item_id: str) -> Optional[OrganizationalKnowledgeItem]:
        return self.repository.get_item(item_id)
        
    def verify_knowledge_item(self, item_id: str, verifier_id: str) -> Optional[OrganizationalKnowledgeItem]:
        item = self.repository.get_item(item_id)
        if not item:
            return None
            
        update_data = {
            "status": "verified",
            "confidence_state": "verified",
            "last_verified_at": datetime.now(timezone.utc)
        }
        item = self.repository.update_item(item_id, update_data)
        
        # Create a new version on verification
        self.repository.create_version(
            item_id=item.id,
            version_number=len(item.versions) + 1,
            content=item.content,
            summary=item.summary,
            classification=item.sensitivity,
            scope="project" if item.project_id else "workspace",
            provenance_snapshot={"verified_by": verifier_id, "timestamp": datetime.now(timezone.utc).isoformat()},
            created_by=verifier_id
        )
        
        self.event_bus.publish(
            "knowledge.verified",
            {
                "item_id": item.id,
                "workspace_id": item.workspace_id,
                "verifier_id": verifier_id
            }
        )
        return item

    def propose_candidate(self, candidate_in: KnowledgeCandidateCreate) -> KnowledgeCandidate:
        candidate = self.repository.create_candidate(candidate_in)
        self.event_bus.publish(
            "knowledge.candidate_created",
            {
                "candidate_id": candidate.id,
                "workspace_id": candidate.workspace_id,
                "source_type": candidate.source_type
            }
        )
        return candidate
        
    def accept_candidate(self, candidate_id: str, reviewer_id: str) -> Optional[OrganizationalKnowledgeItem]:
        candidate = self.repository.get_candidate(candidate_id)
        if not candidate:
            return None
            
        candidate = self.repository.update_candidate_status(candidate_id, "accepted")
        
        # Promote to knowledge item
        item_in = OrganizationalKnowledgeItemCreate(
            workspace_id=candidate.workspace_id,
            project_id=candidate.project_id,
            knowledge_type=candidate.candidate_type,
            title=candidate.title,
            summary=candidate.title, # Simple default
            content=candidate.content,
            status="under_review",
            confidence_state="supported"
        )
        
        item = self.create_knowledge_item(item_in, reviewer_id)
        
        self.event_bus.publish(
            "knowledge.accepted",
            {
                "candidate_id": candidate.id,
                "item_id": item.id,
                "reviewer_id": reviewer_id
            }
        )
        
        return item

    def report_conflict(self, conflict_in: KnowledgeConflictCreate, reporter_id: str) -> KnowledgeConflict:
        conflict = self.repository.create_conflict(conflict_in)
        
        # Mark items as disputed
        self.repository.update_item(conflict.knowledge_item_a_id, {"status": "disputed", "confidence_state": "disputed"})
        self.repository.update_item(conflict.knowledge_item_b_id, {"status": "disputed", "confidence_state": "disputed"})
        
        self.event_bus.publish(
            "knowledge.conflict_detected",
            {
                "conflict_id": conflict.id,
                "workspace_id": conflict.workspace_id,
                "item_a_id": conflict.knowledge_item_a_id,
                "item_b_id": conflict.knowledge_item_b_id,
                "reporter_id": reporter_id
            }
        )
        return conflict
        
    def resolve_conflict(self, conflict_id: str, resolution: str, resolved_by: str) -> Optional[KnowledgeConflict]:
        conflict = self.repository.resolve_conflict(conflict_id, resolution, resolved_by)
        if conflict:
            self.event_bus.publish(
                "knowledge.conflict_resolved",
                {
                    "conflict_id": conflict.id,
                    "workspace_id": conflict.workspace_id,
                    "resolved_by": resolved_by
                }
            )
        return conflict
