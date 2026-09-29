import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.errors import DatabaseError, NotFoundError
from backend.app.db.models.evaluation import EvaluationFinding, EvaluationRun
from backend.app.db.models.project import Project
from backend.app.db.models.run import Run
from backend.app.db.models.task import Task
from backend.app.db.models.workspace import Workspace
from backend.app.services.evaluation.schemas import EvaluationResult


class EvaluationRepository:
    """Repository handling persistence and multi-tenant querying for EvaluationRuns and EvaluationFindings."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id_and_owner(self, eval_run_id: UUID, owner_user_id: UUID) -> Optional[EvaluationRun]:
        stmt = (
            select(EvaluationRun)
            .join(Run, EvaluationRun.run_id == Run.id)
            .join(Task, Run.task_id == Task.id)
            .join(Project, Task.project_id == Project.id)
            .join(Workspace, Project.workspace_id == Workspace.id)
            .options(selectinload(EvaluationRun.findings))
            .where(
                EvaluationRun.id == eval_run_id,
                Workspace.owner_user_id == owner_user_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_run(
        self,
        run_id: UUID,
        owner_user_id: UUID,
    ) -> List[EvaluationRun]:
        """
        Retrieves all evaluation runs and nested findings for a specific Run,
        enforcing multi-tenant workspace ownership isolation.
        """
        # Verify run belongs to user
        run_stmt = (
            select(Run.id)
            .join(Task, Run.task_id == Task.id)
            .join(Project, Task.project_id == Project.id)
            .join(Workspace, Project.workspace_id == Workspace.id)
            .where(
                Run.id == run_id,
                Workspace.owner_user_id == owner_user_id,
            )
        )
        run_res = await self.session.execute(run_stmt)
        if not run_res.scalar_one_or_none():
            raise NotFoundError(f"Run with id '{run_id}' not found.")

        stmt = (
            select(EvaluationRun)
            .options(selectinload(EvaluationRun.findings))
            .where(EvaluationRun.run_id == run_id)
            .order_by(EvaluationRun.created_at.asc())
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def record_evaluation_result(
        self,
        run_id: UUID,
        result: EvaluationResult,
        evaluator_type: str = "engine",
    ) -> EvaluationRun:
        """
        Persists an EvaluationRun and all its individual EvaluationFinding records atomically.
        """
        now = datetime.now(timezone.utc)
        eval_run = EvaluationRun(
            id=uuid.uuid4(),
            run_id=run_id,
            status=result.status.value if hasattr(result.status, "value") else str(result.status),
            evaluator_type=evaluator_type,
            recommendation=result.recommendation.value if hasattr(result.recommendation, "value") else str(result.recommendation),
            mode=result.mode.value if hasattr(result.mode, "value") else str(result.mode),
            attempt=result.attempt,
            started_at=now,
            completed_at=now,
            duration_ms=result.duration_ms,
            raw_summary=result.summary,
            metadata_snapshot={
                "revision_suggested": result.revision_suggested,
                "revision_reasons": result.revision_reasons,
                "missing_requirements": result.missing_requirements,
                "format_issues": result.format_issues,
                "citation_issues": result.citation_issues,
                "safety_issues": result.safety_issues,
                "unsupported_claims_count": len(result.unsupported_claims),
            },
        )
        self.session.add(eval_run)
        await self.session.flush()

        # Add findings
        for finding in result.findings:
            ef = EvaluationFinding(
                id=uuid.uuid4(),
                evaluation_run_id=eval_run.id,
                check_type=finding.check_type.value if hasattr(finding.check_type, "value") else str(finding.check_type),
                status=finding.status.value if hasattr(finding.status, "value") else str(finding.status),
                confidence=finding.confidence,
                description=finding.description,
                evidence_ids=finding.evidence_ids,
                metadata_snapshot=finding.metadata,
                created_at=now,
            )
            self.session.add(ef)

        await self.session.flush()
        
        # Load with findings relationship populated
        stmt = (
            select(EvaluationRun)
            .options(selectinload(EvaluationRun.findings))
            .where(EvaluationRun.id == eval_run.id)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one()

