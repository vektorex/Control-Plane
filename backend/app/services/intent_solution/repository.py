from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
import uuid
from datetime import datetime, timezone

from backend.app.db.models.intent import (
    IntentRequest, IntentRequirement, IntentClarification, CandidateSolution, CandidateStatus, IntentStatus
)
from .schemas import IntentRequestCreate, IntentRequirementSchema, IntentClarificationSchema, CandidateSolutionSchema

class IntentRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_intent_request(self, obj_in: IntentRequestCreate) -> IntentRequest:
        db_obj = IntentRequest(id=str(uuid.uuid4()), **obj_in.model_dump())
        self.session.add(db_obj)
        self.session.flush()
        return db_obj

    def get_intent_request(self, request_id: str) -> Optional[IntentRequest]:
        return self.session.execute(
            select(IntentRequest).where(IntentRequest.id == request_id)
        ).scalar_one_or_none()

    def list_intent_requests(self, filters: Dict[str, Any] = None) -> List[IntentRequest]:
        query = select(IntentRequest)
        if filters:
            conditions = []
            if "status" in filters:
                conditions.append(IntentRequest.status == filters["status"])
            if conditions:
                query = query.where(and_(*conditions))
        return list(self.session.execute(query.order_by(IntentRequest.created_at.desc())).scalars().all())

    def update_intent_status(self, request_id: str, status: str) -> None:
        db_obj = self.get_intent_request(request_id)
        if db_obj:
            db_obj.status = status
            self.session.flush()
            
    def add_requirements(self, request_id: str, requirements: List[IntentRequirementSchema]) -> List[IntentRequirement]:
        db_reqs = []
        for r in requirements:
            req = IntentRequirement(
                id=str(uuid.uuid4()),
                intent_request_id=request_id,
                **r.model_dump()
            )
            self.session.add(req)
            db_reqs.append(req)
        self.session.flush()
        return db_reqs
        
    def add_candidates(self, request_id: str, candidates: List[CandidateSolutionSchema]) -> List[CandidateSolution]:
        db_cands = []
        for c in candidates:
            cand = CandidateSolution(
                id=str(uuid.uuid4()),
                intent_request_id=request_id,
                **c.model_dump()
            )
            self.session.add(cand)
            db_cands.append(cand)
        self.session.flush()
        return db_cands

    def get_candidate(self, candidate_id: str) -> Optional[CandidateSolution]:
        return self.session.execute(
            select(CandidateSolution).where(CandidateSolution.id == candidate_id)
        ).scalar_one_or_none()
        
    def update_candidate_status(self, candidate_id: str, status: str) -> None:
        cand = self.get_candidate(candidate_id)
        if cand:
            cand.status = status
            self.session.flush()
