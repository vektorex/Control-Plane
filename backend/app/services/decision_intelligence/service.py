from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from .repository import DecisionRepository
from .schemas import (
    DecisionRequestCreate,
    DecisionEvidenceSchema,
)
from backend.app.db.models.decision import DecisionRequest
from backend.app.services.events.service import EventBus

class DecisionService:
    def __init__(self, session: Session, event_bus: EventBus):
        self.session = session
        self.repository = DecisionRepository(session)
        self.event_bus = event_bus

    def create_request(self, obj_in: DecisionRequestCreate) -> DecisionRequest:
        req = self.repository.create_request(obj_in)
        self.event_bus.publish("decision.requested", {"decision_id": req.id})
        return req

    def get_request(self, decision_id: str) -> Optional[DecisionRequest]:
        return self.repository.get_request(decision_id)

    def list_requests(self, filters: Dict[str, Any] = None) -> List[DecisionRequest]:
        return self.repository.list_requests(filters)

    def evaluate(self, decision_id: str) -> DecisionRequest:
        req = self.get_request(decision_id)
        if not req:
            return None
            
        self.repository.update_status(decision_id, "collecting_evidence")
        self.event_bus.publish("decision.evidence_collected", {"decision_id": req.id})
        
        # Mock evidence collection
        evidence = [
            DecisionEvidenceSchema(
                source_type="governance",
                source_id="gov-1",
                evidence_type="governance_decision",
                claim="Allowed",
                value={"policy": "default"},
                status="verified"
            )
        ]
        self.repository.add_evidence(decision_id, evidence)
        
        self.repository.update_status(decision_id, "analyzing")
        
        # Mock decision engine execution
        decision_val = "allow"
        state = "ready"
        
        self.repository.add_record(decision_id, {
            "decision": decision_val,
            "state": state,
            "decision_version": "v1",
            "conditions": [{"type": "governance", "satisfied": True}],
            "blockers": [],
            "explanation": "All requirements satisfied."
        })
        
        self.repository.update_status(decision_id, state)
        self.event_bus.publish(f"decision.{state}", {"decision_id": req.id})
        
        return self.get_request(decision_id)

    def assess_execution_readiness(self, subject_type: str, subject_id: str) -> Dict[str, Any]:
        """ Specialized execution readiness endpoint used by external components """
        return {
            "overall_state": "ready",
            "conditions": [],
            "blockers": [],
            "evidence": [],
            "required_actions": []
        }
