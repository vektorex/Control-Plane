import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.evaluation_lab import (
    EvaluationCase,
    EvaluationDataset,
    EvaluationDatasetVersion,
    EvaluationExperiment,
    EvaluationExperimentRun,
)
from backend.app.db.models.observability import ExecutionTraceEvent
from backend.app.services.evaluation_lab.cases import EvaluationCaseService
from backend.app.services.evaluation_lab.comparisons import EvaluationComparator
from backend.app.services.evaluation_lab.datasets import DatasetService
from backend.app.services.evaluation_lab.experiments import ExperimentService
from backend.app.services.evaluation_lab.regression import RegressionDetector
from backend.app.services.evaluation_lab.schemas import (
    EvaluationCaseCreate,
    EvaluationCaseUpdate,
    EvaluationComparisonResponse,
    EvaluationDatasetCreate,
    EvaluationDatasetUpdate,
    EvaluationDatasetVersionCreate,
    EvaluationExperimentCreate,
    RegressionCheckResponse,
)

logger = logging.getLogger("evaluation_lab.service")


class EvaluationLabService:
    """
    Central facade service for AI Evaluation Lab.
    Provides a unified interface for dataset curation, versioning, case assertions,
    experiment execution, differential comparison, and regression detection.
    """

    def __init__(self, experiment_service: Optional[ExperimentService] = None) -> None:
        self.experiment_service = experiment_service or ExperimentService()

    # --- Dataset Operations ---
    @classmethod
    async def create_dataset(
        cls,
        session: AsyncSession,
        workspace_id: UUID,
        dataset_in: EvaluationDatasetCreate,
        created_by: Optional[UUID] = None,
    ) -> Tuple[EvaluationDataset, EvaluationDatasetVersion]:
        return await DatasetService.create_dataset(
            session=session,
            workspace_id=workspace_id,
            dataset_in=dataset_in,
            created_by=created_by,
        )

    @classmethod
    async def list_datasets(
        cls,
        session: AsyncSession,
        workspace_id: UUID,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[EvaluationDataset], int]:
        return await DatasetService.list_datasets(
            session=session,
            workspace_id=workspace_id,
            status=status,
            limit=limit,
            offset=offset,
        )

    @classmethod
    async def get_dataset(
        cls,
        session: AsyncSession,
        dataset_id: UUID,
        workspace_id: Optional[UUID] = None,
    ) -> EvaluationDataset:
        return await DatasetService.get_dataset(
            session=session,
            dataset_id=dataset_id,
            workspace_id=workspace_id,
        )

    @classmethod
    async def update_dataset(
        cls,
        session: AsyncSession,
        dataset_id: UUID,
        dataset_in: EvaluationDatasetUpdate,
        workspace_id: Optional[UUID] = None,
    ) -> EvaluationDataset:
        return await DatasetService.update_dataset(
            session=session,
            dataset_id=dataset_id,
            dataset_in=dataset_in,
            workspace_id=workspace_id,
        )

    @classmethod
    async def create_dataset_version(
        cls,
        session: AsyncSession,
        dataset_id: UUID,
        version_in: EvaluationDatasetVersionCreate,
        created_by: Optional[UUID] = None,
        workspace_id: Optional[UUID] = None,
    ) -> EvaluationDatasetVersion:
        return await DatasetService.create_dataset_version(
            session=session,
            dataset_id=dataset_id,
            version_in=version_in,
            created_by=created_by,
            workspace_id=workspace_id,
        )

    @classmethod
    async def import_cases(
        cls,
        session: AsyncSession,
        dataset_id: UUID,
        raw_bytes: bytes,
        file_format: str,
        target_version_id: Optional[UUID] = None,
        workspace_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        return await DatasetService.import_cases(
            session=session,
            dataset_id=dataset_id,
            raw_bytes=raw_bytes,
            file_format=file_format,
            target_version_id=target_version_id,
            workspace_id=workspace_id,
        )

    @classmethod
    async def export_cases(
        cls,
        session: AsyncSession,
        dataset_id: UUID,
        export_format: str = "json",
        version_id: Optional[UUID] = None,
        workspace_id: Optional[UUID] = None,
    ) -> str:
        return await DatasetService.export_cases(
            session=session,
            dataset_id=dataset_id,
            export_format=export_format,
            version_id=version_id,
            workspace_id=workspace_id,
        )

    # --- Case Operations ---
    @classmethod
    async def list_cases(
        cls,
        session: AsyncSession,
        dataset_version_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[EvaluationCase]:
        return await EvaluationCaseService.list_cases(
            session=session,
            dataset_version_id=dataset_version_id,
            limit=limit,
            offset=offset,
        )

    @classmethod
    async def get_case(
        cls,
        session: AsyncSession,
        case_id: UUID,
    ) -> EvaluationCase:
        return await EvaluationCaseService.get_case(session=session, case_id=case_id)

    @classmethod
    async def create_case(
        cls,
        session: AsyncSession,
        dataset_version_id: UUID,
        case_in: EvaluationCaseCreate,
    ) -> EvaluationCase:
        return await EvaluationCaseService.create_case(
            session=session,
            dataset_version_id=dataset_version_id,
            case_in=case_in,
        )

    @classmethod
    async def update_case(
        cls,
        session: AsyncSession,
        case_id: UUID,
        update_in: EvaluationCaseUpdate,
    ) -> EvaluationCase:
        return await EvaluationCaseService.update_case(
            session=session,
            case_id=case_id,
            update_in=update_in,
        )

    @classmethod
    async def delete_case(
        cls,
        session: AsyncSession,
        case_id: UUID,
    ) -> None:
        await EvaluationCaseService.delete_case(session=session, case_id=case_id)

    # --- Experiment Operations ---
    @classmethod
    async def create_experiment(
        cls,
        session: AsyncSession,
        workspace_id: UUID,
        exp_in: EvaluationExperimentCreate,
        created_by: Optional[UUID] = None,
    ) -> EvaluationExperiment:
        return await ExperimentService.create_experiment(
            session=session,
            workspace_id=workspace_id,
            exp_in=exp_in,
            created_by=created_by,
        )

    @classmethod
    async def get_experiment(
        cls,
        session: AsyncSession,
        experiment_id: UUID,
        workspace_id: Optional[UUID] = None,
    ) -> EvaluationExperiment:
        return await ExperimentService.get_experiment(
            session=session,
            experiment_id=experiment_id,
            workspace_id=workspace_id,
        )

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
        return await ExperimentService.list_experiments(
            session=session,
            workspace_id=workspace_id,
            status=status,
            target_type=target_type,
            limit=limit,
            offset=offset,
        )

    async def run_experiment(
        self,
        session: AsyncSession,
        experiment_id: UUID,
        workspace_id: Optional[UUID] = None,
    ) -> EvaluationExperiment:
        return await self.experiment_service.run_experiment(
            session=session,
            experiment_id=experiment_id,
            workspace_id=workspace_id,
        )

    @classmethod
    async def cancel_experiment(
        cls,
        session: AsyncSession,
        experiment_id: UUID,
        workspace_id: Optional[UUID] = None,
    ) -> EvaluationExperiment:
        return await ExperimentService.cancel_experiment(
            session=session,
            experiment_id=experiment_id,
            workspace_id=workspace_id,
        )

    @classmethod
    async def get_experiment_results(
        cls,
        session: AsyncSession,
        experiment_id: UUID,
        workspace_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        return await ExperimentService.get_experiment_results(
            session=session,
            experiment_id=experiment_id,
            workspace_id=workspace_id,
        )

    @classmethod
    async def get_experiment_trace(
        cls,
        session: AsyncSession,
        experiment_id: UUID,
    ) -> List[ExecutionTraceEvent]:
        stmt = (
            select(ExecutionTraceEvent)
            .where(ExecutionTraceEvent.run_id == experiment_id)
            .order_by(ExecutionTraceEvent.created_at.asc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    # --- Comparison & Regression ---
    @classmethod
    async def compare_experiments(
        cls,
        session: AsyncSession,
        experiment_a_id: UUID,
        experiment_b_id: UUID,
        workspace_id: Optional[UUID] = None,
    ) -> EvaluationComparisonResponse:
        return await EvaluationComparator.compare_experiments(
            session=session,
            experiment_a_id=experiment_a_id,
            experiment_b_id=experiment_b_id,
            workspace_id=workspace_id,
        )

    @classmethod
    async def detect_regressions(
        cls,
        session: AsyncSession,
        baseline_experiment_id: UUID,
        candidate_experiment_id: UUID,
        workspace_id: Optional[UUID] = None,
    ) -> RegressionCheckResponse:
        return await RegressionDetector.detect_regressions(
            session=session,
            baseline_experiment_id=baseline_experiment_id,
            candidate_experiment_id=candidate_experiment_id,
            workspace_id=workspace_id,
        )
