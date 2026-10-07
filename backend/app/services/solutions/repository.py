from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
import uuid

from backend.app.db.models.solutions import Solution, SolutionVersion, SolutionComponent, SolutionConnection
from .schemas import SolutionCreate, SolutionUpdate, SolutionVersionBase

class SolutionRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_solution(self, obj_in: SolutionCreate) -> Solution:
        db_obj = Solution(id=str(uuid.uuid4()), **obj_in.model_dump())
        self.session.add(db_obj)
        self.session.flush()
        return db_obj

    def get_solution(self, solution_id: str) -> Optional[Solution]:
        return self.session.execute(
            select(Solution).where(Solution.id == solution_id)
        ).scalar_one_or_none()

    def list_solutions(self, filters: Dict[str, Any] = None) -> List[Solution]:
        query = select(Solution)
        if filters:
            conditions = []
            if "status" in filters:
                conditions.append(Solution.status == filters["status"])
            if "visibility" in filters:
                conditions.append(Solution.visibility == filters["visibility"])
            if conditions:
                query = query.where(and_(*conditions))
        return list(self.session.execute(query).scalars().all())

    def update_solution(self, solution_id: str, updates: SolutionUpdate) -> Optional[Solution]:
        db_obj = self.get_solution(solution_id)
        if not db_obj:
            return None
        update_data = updates.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        self.session.flush()
        return db_obj

    def create_version(self, solution_id: str, version_in: SolutionVersionBase) -> SolutionVersion:
        db_obj = SolutionVersion(
            id=str(uuid.uuid4()),
            solution_id=solution_id,
            **version_in.model_dump()
        )
        self.session.add(db_obj)
        self.session.flush()
        return db_obj

    def get_version(self, version_id: str) -> Optional[SolutionVersion]:
        return self.session.execute(
            select(SolutionVersion).where(SolutionVersion.id == version_id)
        ).scalar_one_or_none()

    def get_versions(self, solution_id: str) -> List[SolutionVersion]:
        return list(self.session.execute(
            select(SolutionVersion).where(SolutionVersion.solution_id == solution_id).order_by(SolutionVersion.created_at.desc())
        ).scalars().all())
