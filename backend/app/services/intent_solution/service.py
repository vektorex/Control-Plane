from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from .repository import IntentRepository
from .schemas import (
    IntentRequestCreate,
    IntentRequirementSchema,
    CandidateSolutionSchema,
    ValidationResponse
)
from backend.app.db.models.intent import IntentRequest, CandidateSolution
from backend.app.services.events.service import EventBus

class IntentService:
    def __init__(self, session: Session, event_bus: EventBus):
        self.session = session
        self.repository = IntentRepository(session)
        self.event_bus = event_bus

    def create_intent(self, obj_in: IntentRequestCreate) -> IntentRequest:
        intent = self.repository.create_intent_request(obj_in)
        self.event_bus.publish("intent.created", {"request_id": intent.id})
        
        # In a real implementation, we would dispatch an async job here to process the intent
        return intent

    def get_intent(self, request_id: str) -> Optional[IntentRequest]:
        return self.repository.get_intent_request(request_id)

    def list_intents(self, filters: Dict[str, Any] = None) -> List[IntentRequest]:
        return self.repository.list_intent_requests(filters)

    def analyze_intent(self, request_id: str) -> IntentRequest:
        intent = self.get_intent(request_id)
        if not intent:
            return None
            
        self.event_bus.publish("intent.analysis_started", {"request_id": intent.id})
        self.repository.update_intent_status(request_id, "analyzing")
        
        # Mocking structured LLM extraction
        intent.normalized_intent = intent.raw_intent
        intent.analysis = {
            "objective": "Process the user intent",
            "inputs": ["Unstructured Text"],
            "outputs": ["Structured Action Plan"]
        }
        
        # Mock requirements
        reqs = [
            IntentRequirementSchema(
                req_type="capability",
                description="Needs to process text",
                source="inferred",
                mandatory=True
            )
        ]
        self.repository.add_requirements(request_id, reqs)
        
        self.repository.update_intent_status(request_id, "requirements_ready")
        self.event_bus.publish("intent.analysis_completed", {"request_id": intent.id})
        
        # Auto-discover candidates for mock
        self._mock_discover_candidates(request_id)
        
        return intent
        
    def _mock_discover_candidates(self, request_id: str):
        self.repository.update_intent_status(request_id, "discovering")
        # Mock catalog search
        candidates = [
            CandidateSolutionSchema(
                name="Basic Text Processing Workflow",
                objective="Process text as requested",
                source="generated",
                solution_blueprint={"nodes": [], "edges": []}
            )
        ]
        self.repository.add_candidates(request_id, candidates)
        self.repository.update_intent_status(request_id, "review_required")
        self.event_bus.publish("intent.candidates_generated", {"request_id": request_id})

    def validate_candidate(self, candidate_id: str) -> ValidationResponse:
        cand = self.repository.get_candidate(candidate_id)
        if not cand:
            return ValidationResponse(is_valid=False, findings=[{"code": "404", "message": "Not found", "source": "system", "severity": "error"}])
        
        self.event_bus.publish("intent.candidate_validated", {"candidate_id": candidate_id})
        return ValidationResponse(is_valid=True, findings=[])

    def simulate_candidate(self, candidate_id: str) -> Dict[str, Any]:
        self.event_bus.publish("intent.candidate_simulated", {"candidate_id": candidate_id})
        return {"status": "success", "findings": []}

    def convert_candidate(self, request_id: str, candidate_id: str) -> Dict[str, Any]:
        intent = self.get_intent(request_id)
        cand = self.repository.get_candidate(candidate_id)
        
        if not intent or not cand:
            return {"status": "error", "message": "Not found"}
            
        self.repository.update_candidate_status(candidate_id, "converted")
        self.repository.update_intent_status(request_id, "completed")
        self.event_bus.publish("intent.candidate_converted", {"candidate_id": candidate_id})
        
        return {"status": "success", "solution_draft_id": "draft_123"}
