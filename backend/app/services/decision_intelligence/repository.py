from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
import uuid
from datetime import datetime, timezone

from backend.app.db.models.decision import (
    DecisionRequest, DecisionEvidence, DecisionRecord, DecisionRequiredAction, DecisionStatus
)
from .schemas import DecisionRequestCreate, DecisionEvidenceSchema

class DecisionRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_request(self, obj_in: DecisionRequestCreate) -> DecisionRequest:
        db_obj = DecisionRequest(id=str(uuid.uuid4()), **obj_in.model_dump())
        self.session.add(db_obj)
        self.session.flush()
        return db_obj

    def get_request(self, decision_id: str) -> Optional[DecisionRequest]:
        return self.session.execute(
            select(DecisionRequest).where(DecisionRequest.id == decision_id)
        ).scalar_one_or_none()

    def list_requests(self, filters: Dict[str, Any] = None) -> List[DecisionRequest]:
        query = select(DecisionRequest)
        if filters:
            conditions = []
            if "status" in filters:
                conditions.append(DecisionRequest.status == filters["status"])
            if conditions:
                query = query.where(and_(*conditions))
        return list(self.session.execute(query.order_by(DecisionRequest.created_at.desc())).scalars().all())

    def update_status(self, decision_id: str, status: str) -> None:
        db_obj = self.get_request(decision_id)
        if db_obj:
            db_obj.status = status
            self.session.flush()
            
    def add_evidence(self, decision_id: str, evidence: List[DecisionEvidenceSchema]) -> List[DecisionEvidence]:
        db_evs = []
        for e in evidence:
            ev = DecisionEvidence(
                id=str(uuid.uuid4()),
                decision_request_id=decision_id,
                **e.model_dump()
            )
            self.session.add(ev)
            db_evs.append(ev)
        self.session.flush()
        return db_evs
        
    def add_record(self, decision_id: str, record_data: Dict[str, Any]) -> DecisionRecord:
        record = DecisionRecord(
            id=str(uuid.uuid4()),
            decision_request_id=decision_id,
            **record_data
        )
        self.session.add(record)
        self.session.flush()
        return record

    def add_actions(self, decision_id: str, actions: List[Dict[str, Any]]) -> List[DecisionRequiredAction]:
        db_actions = []
        for a in actions:
            action = DecisionRequiredAction(
                id=str(uuid.uuid4()),
                decision_request_id=decision_id,
                **a
            )
            self.session.add(action)
            db_actions.append(action)
        self.session.flush()
        return db_actions
