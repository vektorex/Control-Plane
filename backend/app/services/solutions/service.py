from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from .repository import SolutionRepository
from .schemas import (
    SolutionCreate, 
    SolutionUpdate, 
    SolutionVersionBase,
    ValidationResponse,
    ValidationFinding
)
from backend.app.db.models.solutions import Solution, SolutionVersion
from backend.app.services.events.service import EventBus

class SolutionService:
    def __init__(self, session: Session, event_bus: EventBus):
        self.session = session
        self.repository = SolutionRepository(session)
        self.event_bus = event_bus

    def create_solution(self, obj_in: SolutionCreate) -> Solution:
        solution = self.repository.create_solution(obj_in)
        
        # Create initial draft version
        version = self.repository.create_version(solution.id, SolutionVersionBase(
            version="1.0.0",
            created_by=obj_in.created_by,
            status="draft"
        ))
        
        solution.current_version_id = version.id
        self.session.flush()

        self.event_bus.publish("solution.created", {"solution_id": solution.id})
        return solution

    def get_solution(self, solution_id: str) -> Optional[Solution]:
        return self.repository.get_solution(solution_id)

    def list_solutions(self, filters: Dict[str, Any] = None) -> List[Solution]:
        return self.repository.list_solutions(filters)

    def update_solution(self, solution_id: str, updates: SolutionUpdate) -> Optional[Solution]:
        solution = self.repository.update_solution(solution_id, updates)
        if solution:
            self.event_bus.publish("solution.updated", {"solution_id": solution.id})
        return solution

    def get_versions(self, solution_id: str) -> List[SolutionVersion]:
        return self.repository.get_versions(solution_id)
        
    def validate_solution(self, solution_id: str, version_id: str = None) -> ValidationResponse:
        solution = self.get_solution(solution_id)
        if not solution:
            return ValidationResponse(is_valid=False, findings=[
                ValidationFinding(code="NOT_FOUND", message="Solution not found", source="system", severity="error")
            ])
            
        version_id_to_check = version_id or solution.current_version_id
        version = self.repository.get_version(version_id_to_check)
        
        if not version:
            return ValidationResponse(is_valid=False, findings=[
                ValidationFinding(code="NOT_FOUND", message="Solution version not found", source="system", severity="error")
            ])

        # Example simplistic validation
        findings = []
        if not version.components:
            findings.append(ValidationFinding(
                code="NO_COMPONENTS",
                message="Solution has no configured components.",
                source="validator",
                severity="warning"
            ))

        is_valid = not any(f.severity == "error" for f in findings)
        
        self.event_bus.publish(
            "solution.validation_passed" if is_valid else "solution.validation_failed",
            {"solution_id": solution.id, "version_id": version.id}
        )
        
        return ValidationResponse(is_valid=is_valid, findings=findings)
        
    def simulate_solution(self, solution_id: str) -> Dict[str, Any]:
        return {
            "status": "success",
            "estimated_path": [],
            "warnings": ["Simulation executed in sandbox mode."]
        }
