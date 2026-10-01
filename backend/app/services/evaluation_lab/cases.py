import uuid
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.evaluation_lab import EvaluationCase, EvaluationDatasetVersion
from backend.app.services.evaluation_lab.errors import (
    CaseNotFoundError,
    DatasetValidationError,
    DatasetVersionNotFoundError,
)
from backend.app.services.evaluation_lab.policies import EvaluationLabPolicy
from backend.app.services.evaluation_lab.sanitization import validate_and_sanitize_case_payload
from backend.app.services.evaluation_lab.schemas import (
    EvaluationCaseCreate,
    EvaluationCaseUpdate,
)


class EvaluationCaseService:
    """Service for managing evaluation cases within a dataset version."""

    @classmethod
    async def list_cases(
        cls,
        session: AsyncSession,
        dataset_version_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[EvaluationCase]:
        stmt = (
            select(EvaluationCase)
            .where(EvaluationCase.dataset_version_id == dataset_version_id)
            .order_by(EvaluationCase.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def get_case(
        cls,
        session: AsyncSession,
        case_id: UUID,
    ) -> EvaluationCase:
        stmt = select(EvaluationCase).where(EvaluationCase.id == case_id)
        result = await session.execute(stmt)
        case = result.scalar_one_or_none()
        if not case:
            raise CaseNotFoundError(f"Evaluation case {case_id} not found")
        return case

    @classmethod
    async def create_case(
        cls,
        session: AsyncSession,
        dataset_version_id: UUID,
        case_in: EvaluationCaseCreate,
    ) -> EvaluationCase:
        # 1. Verify dataset version exists and is not locked
        stmt = select(EvaluationDatasetVersion).where(EvaluationDatasetVersion.id == dataset_version_id)
        result = await session.execute(stmt)
        version = result.scalar_one_or_none()
        if not version:
            raise DatasetVersionNotFoundError(f"Dataset version {dataset_version_id} not found")

        await EvaluationLabPolicy.assert_dataset_version_editable(session, dataset_version_id)

        # 2. Check case_key uniqueness in this version
        key_check = select(EvaluationCase.id).where(
            EvaluationCase.dataset_version_id == dataset_version_id,
            EvaluationCase.case_key == case_in.case_key,
        )
        existing_key = (await session.execute(key_check)).scalar_one_or_none()
        if existing_key:
            raise DatasetValidationError(f"Case with key '{case_in.case_key}' already exists in this dataset version")

        # 3. Sanitize and validate
        sanitized = validate_and_sanitize_case_payload(
            input_data=case_in.input_data,
            expected_output=case_in.expected_output,
            expected_context=case_in.expected_context,
            expected_sources=case_in.expected_sources,
            assertions=[a.model_dump() for a in case_in.assertions],
            metadata=case_in.metadata,
        )

        case = EvaluationCase(
            id=uuid.uuid4(),
            dataset_version_id=dataset_version_id,
            case_key=case_in.case_key,
            name=case_in.name,
            input_data=sanitized["input_data"],
            expected_output=sanitized["expected_output"],
            expected_context=sanitized["expected_context"],
            expected_sources=sanitized["expected_sources"],
            assertions=sanitized["assertions"],
            case_metadata=sanitized["metadata"],
        )
        session.add(case)
        await session.commit()
        await session.refresh(case)
        return case

    @classmethod
    async def update_case(
        cls,
        session: AsyncSession,
        case_id: UUID,
        update_in: EvaluationCaseUpdate,
    ) -> EvaluationCase:
        case = await cls.get_case(session, case_id)
        await EvaluationLabPolicy.assert_dataset_version_editable(session, case.dataset_version_id)

        update_dict = update_in.model_dump(exclude_unset=True)
        if "assertions" in update_dict and update_dict["assertions"] is not None:
            update_dict["assertions"] = [
                a.model_dump() if hasattr(a, "model_dump") else a for a in update_in.assertions
            ]

        sanitized = validate_and_sanitize_case_payload(
            input_data=update_dict.get("input_data", case.input_data),
            expected_output=update_dict.get("expected_output", case.expected_output),
            expected_context=update_dict.get("expected_context", case.expected_context),
            expected_sources=update_dict.get("expected_sources", case.expected_sources),
            assertions=update_dict.get("assertions", case.assertions),
            metadata=update_dict.get("metadata", case.case_metadata),
        )

        if "name" in update_dict and update_dict["name"] is not None:
            case.name = update_dict["name"]
        case.input_data = sanitized["input_data"]
        case.expected_output = sanitized["expected_output"]
        case.expected_context = sanitized["expected_context"]
        case.expected_sources = sanitized["expected_sources"]
        case.assertions = sanitized["assertions"]
        case.case_metadata = sanitized["metadata"]

        await session.commit()
        await session.refresh(case)
        return case

    @classmethod
    async def delete_case(
        cls,
        session: AsyncSession,
        case_id: UUID,
    ) -> None:
        case = await cls.get_case(session, case_id)
        await EvaluationLabPolicy.assert_dataset_version_editable(session, case.dataset_version_id)
        await session.delete(case)
        await session.commit()

    @classmethod
    def validate_cases_integrity(cls, cases: List[EvaluationCase]) -> List[str]:
        """
        Validates quality and integrity of a list of evaluation cases before running an experiment.
        Returns a list of warnings or error strings.
        """
        errors = []
        keys_seen = set()
        for idx, c in enumerate(cases):
            if not c.case_key:
                errors.append(f"Case #{idx+1} has an empty case_key")
            elif c.case_key in keys_seen:
                errors.append(f"Duplicate case_key detected: '{c.case_key}'")
            else:
                keys_seen.add(c.case_key)

            if not c.input_data:
                errors.append(f"Case '{c.case_key}' has empty input_data")

            # Check if neither assertions nor expected output are defined
            if not c.assertions and not c.expected_output:
                errors.append(f"Case '{c.case_key}' has neither expected_output nor assertions defined")

        return errors
