import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.evaluation_lab import (
    EvaluationDatasetVersion,
    EvaluationExperiment,
)
from backend.app.services.evaluation_lab.errors import (
    DatasetVersionLockedError,
    SideEffectBlockedError,
)

logger = logging.getLogger("evaluation_lab.policies")


class EvaluationLabPolicy:
    """
    Enforces security, immutability, side-effect isolation, and memory/connector
    guardrails during Evaluation Lab operations.
    """

    @classmethod
    async def assert_dataset_version_editable(
        cls,
        session: AsyncSession,
        dataset_version_id: UUID,
    ) -> None:
        """
        Ensures that a dataset version is not locked by completed experiments.
        Once an experiment reaches 'completed', the referenced version is permanently frozen.
        """
        stmt = select(EvaluationExperiment).where(
            EvaluationExperiment.dataset_version_id == dataset_version_id,
            EvaluationExperiment.status == "completed",
        )
        result = await session.execute(stmt)
        completed_experiment = result.scalars().first()
        if completed_experiment:
            raise DatasetVersionLockedError(
                f"Dataset version {dataset_version_id} is permanently locked because it was evaluated by "
                f"completed experiment '{completed_experiment.name}' ({completed_experiment.id}). "
                "Create a new dataset version to add or modify cases."
            )

    @classmethod
    async def is_dataset_version_locked(
        cls,
        session: AsyncSession,
        dataset_version_id: UUID,
    ) -> bool:
        """
        Checks if the dataset version is locked without raising an error.
        """
        stmt = select(EvaluationExperiment.id).where(
            EvaluationExperiment.dataset_version_id == dataset_version_id,
            EvaluationExperiment.status == "completed",
        ).limit(1)
        result = await session.execute(stmt)
        return result.scalar_one_or_none() is not None

    @classmethod
    def enforce_safe_execution_policy(
        cls,
        operation_name: str,
        is_write: bool = False,
        is_destructive: bool = False,
        has_fresh_approval: bool = False,
    ) -> Dict[str, Any]:
        """
        Enforces side-effect policy for evaluation experiments:
        - Read operations: allowed.
        - Write operations: default to dry-run simulation unless fresh approval is granted.
        - Destructive operations: blocked unless fresh approval is granted.
        """
        if is_destructive and not has_fresh_approval:
            raise SideEffectBlockedError(
                f"Destructive operation '{operation_name}' is blocked during evaluation runs. "
                "Fresh Human-in-the-Loop (HITL) approval is required."
            )

        if is_write and not has_fresh_approval:
            logger.info("Evaluation side-effect isolated: '%s' simulated in dry-run mode", operation_name)
            return {
                "blocked": True,
                "simulated": True,
                "message": f"Would execute '{operation_name}' (simulated in evaluation dry-run mode)",
            }

        return {"blocked": False, "simulated": False}
