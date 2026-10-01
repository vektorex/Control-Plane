import asyncio
import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.db.models.evaluation_lab import (
    EvaluationCase,
    EvaluationDatasetVersion,
    EvaluationExperiment,
    EvaluationExperimentRun,
)
from backend.app.services.evaluation_lab.cases import EvaluationCaseService
from backend.app.services.evaluation_lab.errors import (
    DatasetValidationError,
    DatasetVersionNotFoundError,
    ExperimentNotFoundError,
    ExperimentStateError,
)
from backend.app.services.evaluation_lab.runners import EvaluationRunner
from backend.app.services.evaluation_lab.schemas import (
    CaseRunStatus,
    EvaluationExperimentCreate,
    ExperimentStatus,
)
from backend.app.services.observability.events import TraceEventStatus, TraceEventType
from backend.app.services.observability.tracer import ExecutionTracer

logger = logging.getLogger("evaluation_lab.experiments")

# In-memory registry of cancellation events for in-flight experiments
_active_cancellations: Dict[str, asyncio.Event] = {}


class ExperimentService:
    """Manages experiment creation, orchestration, concurrency, and cooperative cancellation."""

    def __init__(self, runner: Optional[EvaluationRunner] = None) -> None:
        self.runner = runner or EvaluationRunner()

    @classmethod
    async def create_experiment(
        cls,
        session: AsyncSession,
        workspace_id: UUID,
        exp_in: EvaluationExperimentCreate,
        created_by: Optional[UUID] = None,
    ) -> EvaluationExperiment:
        """
        Creates an experiment record in draft state after verifying target and dataset version.
        """
        stmt = select(EvaluationDatasetVersion).where(
            EvaluationDatasetVersion.id == exp_in.dataset_version_id
        )
        version = (await session.execute(stmt)).scalar_one_or_none()
        if not version:
            raise DatasetVersionNotFoundError(f"Dataset version {exp_in.dataset_version_id} not found")

        exp = EvaluationExperiment(
            id=uuid.uuid4(),
            workspace_id=workspace_id,
            project_id=exp_in.project_id,
            dataset_version_id=exp_in.dataset_version_id,
            target_type=exp_in.target_type.value if hasattr(exp_in.target_type, "value") else str(exp_in.target_type),
            target_configuration=exp_in.target_configuration,
            name=exp_in.name,
            description=exp_in.description,
            status=ExperimentStatus.DRAFT.value,
            created_by=created_by,
        )
        session.add(exp)
        await session.commit()
        await session.refresh(exp)
        return exp

    @classmethod
    async def get_experiment(
        cls,
        session: AsyncSession,
        experiment_id: UUID,
        workspace_id: Optional[UUID] = None,
    ) -> EvaluationExperiment:
        stmt = select(EvaluationExperiment).where(EvaluationExperiment.id == experiment_id)
        if workspace_id:
            stmt = stmt.where(EvaluationExperiment.workspace_id == workspace_id)
        exp = (await session.execute(stmt)).scalar_one_or_none()
        if not exp:
            raise ExperimentNotFoundError(f"Evaluation experiment {experiment_id} not found in this workspace")
        return exp

    @classmethod
    async def list_experiments(
        cls,
        session: AsyncSession,
        workspace_id: UUID,
        status: Optional[str] = None,
        target_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[EvaluationExperiment], int]:
        query = select(EvaluationExperiment).where(EvaluationExperiment.workspace_id == workspace_id)
        if status:
            query = query.where(EvaluationExperiment.status == status)
        if target_type:
            query = query.where(EvaluationExperiment.target_type == target_type)

        count_stmt = select(func.count()).select_from(query.subquery())
        total = (await session.execute(count_stmt)).scalar_one()

        query = query.order_by(EvaluationExperiment.created_at.desc()).limit(limit).offset(offset)
        result = await session.execute(query)
        return list(result.scalars().all()), total

    async def run_experiment(
        self,
        session: AsyncSession,
        experiment_id: UUID,
        workspace_id: Optional[UUID] = None,
    ) -> EvaluationExperiment:
        """
        Executes all evaluation cases for the experiment version with bounded concurrency.
        """
        exp = await self.get_experiment(session, experiment_id, workspace_id=workspace_id)
        if exp.status in (ExperimentStatus.RUNNING.value, ExperimentStatus.COMPLETED.value):
            raise ExperimentStateError(f"Experiment is already in status '{exp.status}'")

        # Fetch cases for the dataset version
        cases_stmt = (
            select(EvaluationCase)
            .where(EvaluationCase.dataset_version_id == exp.dataset_version_id)
            .order_by(EvaluationCase.created_at.asc())
        )
        cases = list((await session.execute(cases_stmt)).scalars().all())
        if not cases:
            raise DatasetValidationError("Cannot run experiment on a dataset version with 0 cases")

        # Validate case integrity
        validation_errors = EvaluationCaseService.validate_cases_integrity(cases)
        if validation_errors:
            raise DatasetValidationError(f"Dataset validation failed: {'; '.join(validation_errors)}")

        # Register cancellation token
        cancel_token = asyncio.Event()
        _active_cancellations[str(exp.id)] = cancel_token

        tracer = ExecutionTracer(run_id=exp.id, workspace_id=exp.workspace_id)
        tracer.record_event(
            event_type=TraceEventType.EVALUATION_EXPERIMENT_STARTED,
            status=TraceEventStatus.STARTED,
            step_type="experiment_started",
            metadata={"case_count": len(cases), "target_type": exp.target_type},
        )
        await tracer.flush_to_db(session)

        # Mark experiment as running
        exp.status = ExperimentStatus.RUNNING.value
        exp.started_at = func.now() if hasattr(func, "now") else None
        await session.commit()

        # Initialize experiment run records
        run_records: List[EvaluationExperimentRun] = []
        for c in cases:
            run_rec = EvaluationExperimentRun(
                id=uuid.uuid4(),
                experiment_id=exp.id,
                case_id=c.id,
                status=CaseRunStatus.QUEUED.value,
                input_snapshot=c.input_data,
            )
            session.add(run_rec)
            run_records.append(run_rec)
        await session.commit()

        # Bounded concurrency execution
        semaphore = asyncio.Semaphore(settings.MAX_EVALUATION_CONCURRENCY)

        async def _run_single_case(c: EvaluationCase, r: EvaluationExperimentRun):
            async with semaphore:
                if cancel_token.is_set():
                    r.status = CaseRunStatus.CANCELLED.value
                    await session.commit()
                    return
                await self.runner.execute_case_run(
                    session=session,
                    experiment=exp,
                    case=c,
                    experiment_run=r,
                    cancellation_token=cancel_token,
                )

        tasks = [_run_single_case(c, r) for c, r in zip(cases, run_records)]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Cleanup cancellation event
        _active_cancellations.pop(str(exp.id), None)

        # Final experiment status update
        await session.refresh(exp)
        if cancel_token.is_set():
            exp.status = ExperimentStatus.CANCELLED.value
            tracer.record_event(
                event_type=TraceEventType.EVALUATION_EXPERIMENT_CANCELLED,
                status=TraceEventStatus.COMPLETED,
                step_type="experiment_cancelled",
            )
        else:
            exp.status = ExperimentStatus.COMPLETED.value
            tracer.record_event(
                event_type=TraceEventType.EVALUATION_EXPERIMENT_COMPLETED,
                status=TraceEventStatus.COMPLETED,
                step_type="experiment_completed",
            )

        exp.completed_at = func.now() if hasattr(func, "now") else None
        try:
            await tracer.flush_to_db(session)
        except Exception:
            pass

        await session.commit()
        await session.refresh(exp)
        return exp

    @classmethod
    async def cancel_experiment(
        cls,
        session: AsyncSession,
        experiment_id: UUID,
        workspace_id: Optional[UUID] = None,
    ) -> EvaluationExperiment:
        """
        Cooperatively cancels an in-flight experiment.
        """
        exp = await cls.get_experiment(session, experiment_id, workspace_id=workspace_id)
        if exp.status != ExperimentStatus.RUNNING.value:
            raise ExperimentStateError(f"Cannot cancel experiment in status '{exp.status}'")

        token = _active_cancellations.get(str(exp.id))
        if token:
            token.set()

        exp.status = ExperimentStatus.CANCELLED.value
        exp.completed_at = func.now() if hasattr(func, "now") else None

        # Mark all pending / queued runs as cancelled
        await session.execute(
            update(EvaluationExperimentRun)
            .where(
                EvaluationExperimentRun.experiment_id == exp.id,
                EvaluationExperimentRun.status.in_([CaseRunStatus.QUEUED.value, CaseRunStatus.RUNNING.value]),
            )
            .values(status=CaseRunStatus.CANCELLED.value)
        )

        await session.commit()
        await session.refresh(exp)
        return exp

    @classmethod
    async def get_experiment_results(
        cls,
        session: AsyncSession,
        experiment_id: UUID,
        workspace_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Calculates factual summary statistics and returns case run records.
        """
        exp = await cls.get_experiment(session, experiment_id, workspace_id=workspace_id)
        runs_stmt = (
            select(EvaluationExperimentRun)
            .where(EvaluationExperimentRun.experiment_id == exp.id)
            .order_by(EvaluationExperimentRun.created_at.asc())
        )
        runs = list((await session.execute(runs_stmt)).scalars().all())

        total = len(runs)
        passed = sum(1 for r in runs if r.status == CaseRunStatus.PASSED.value)
        failed = sum(1 for r in runs if r.status == CaseRunStatus.FAILED.value)
        warning = sum(1 for r in runs if r.status == CaseRunStatus.WARNING.value)
        error = sum(1 for r in runs if r.status == CaseRunStatus.ERROR.value)
        cancelled = sum(1 for r in runs if r.status == CaseRunStatus.CANCELLED.value)

        total_latency = sum(r.latency_ms or 0 for r in runs)
        avg_latency = round(total_latency / total, 1) if total > 0 else 0
        total_tokens = sum((r.input_tokens or 0) + (r.output_tokens or 0) for r in runs)
        total_cost = round(sum(r.estimated_cost or 0.0 for r in runs), 6)

        return {
            "experiment": {
                "id": str(exp.id),
                "name": exp.name,
                "status": exp.status,
                "target_type": exp.target_type,
                "target_configuration": exp.target_configuration,
                "started_at": exp.started_at.isoformat() if exp.started_at else None,
                "completed_at": exp.completed_at.isoformat() if exp.completed_at else None,
            },
            "summary": {
                "total_cases": total,
                "passed": passed,
                "failed": failed,
                "warning": warning,
                "error": error,
                "cancelled": cancelled,
                "average_latency_ms": avg_latency,
                "total_tokens": total_tokens,
                "estimated_cost": total_cost,
            },
            "runs": [
                {
                    "id": str(r.id),
                    "case_id": str(r.case_id),
                    "status": r.status,
                    "latency_ms": r.latency_ms,
                    "input_tokens": r.input_tokens,
                    "output_tokens": r.output_tokens,
                    "estimated_cost": r.estimated_cost,
                    "error_code": r.error_code,
                    "error_message": r.error_message,
                    "evaluation_result": r.evaluation_result,
                }
                for r in runs
            ],
        }
