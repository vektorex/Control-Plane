import csv
import io
import json
import uuid
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.db.models.evaluation_lab import (
    EvaluationCase,
    EvaluationDataset,
    EvaluationDatasetVersion,
)
from backend.app.services.evaluation_lab.cases import EvaluationCaseService
from backend.app.services.evaluation_lab.errors import (
    DatasetImportError,
    DatasetNotFoundError,
    DatasetValidationError,
    DatasetVersionLockedError,
    DatasetVersionNotFoundError,
)
from backend.app.services.evaluation_lab.policies import EvaluationLabPolicy
from backend.app.services.evaluation_lab.sanitization import (
    validate_and_sanitize_case_payload,
    validate_dataset_import_payload,
)
from backend.app.services.evaluation_lab.schemas import (
    EvaluationCaseCreate,
    EvaluationDatasetCreate,
    EvaluationDatasetUpdate,
    EvaluationDatasetVersionCreate,
)


class DatasetService:
    """Service for managing evaluation datasets, versions, import/export, and quality checks."""

    @classmethod
    async def create_dataset(
        cls,
        session: AsyncSession,
        workspace_id: UUID,
        dataset_in: EvaluationDatasetCreate,
        created_by: Optional[UUID] = None,
    ) -> Tuple[EvaluationDataset, EvaluationDatasetVersion]:
        """
        Creates an EvaluationDataset and initializes its initial version 1.
        """
        dataset_id = uuid.uuid4()
        dataset = EvaluationDataset(
            id=dataset_id,
            workspace_id=workspace_id,
            project_id=dataset_in.project_id,
            name=dataset_in.name,
            description=dataset_in.description,
            version=1,
            status="draft",
            created_by=created_by,
        )
        session.add(dataset)

        version_id = uuid.uuid4()
        initial_version = EvaluationDatasetVersion(
            id=version_id,
            dataset_id=dataset_id,
            version=1,
            created_by=created_by,
            description=dataset_in.initial_version_description or "Initial dataset version",
        )
        session.add(initial_version)

        await session.commit()
        await session.refresh(dataset)
        await session.refresh(initial_version)
        return dataset, initial_version

    @classmethod
    async def list_datasets(
        cls,
        session: AsyncSession,
        workspace_id: UUID,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[EvaluationDataset], int]:
        query = select(EvaluationDataset).where(EvaluationDataset.workspace_id == workspace_id)
        if status:
            query = query.where(EvaluationDataset.status == status)

        count_stmt = select(func.count()).select_from(query.subquery())
        total = (await session.execute(count_stmt)).scalar_one()

        query = query.order_by(EvaluationDataset.updated_at.desc()).limit(limit).offset(offset)
        result = await session.execute(query)
        return list(result.scalars().all()), total

    @classmethod
    async def get_dataset(
        cls,
        session: AsyncSession,
        dataset_id: UUID,
        workspace_id: Optional[UUID] = None,
    ) -> EvaluationDataset:
        stmt = select(EvaluationDataset).where(EvaluationDataset.id == dataset_id)
        if workspace_id:
            stmt = stmt.where(EvaluationDataset.workspace_id == workspace_id)
        result = await session.execute(stmt)
        dataset = result.scalar_one_or_none()
        if not dataset:
            raise DatasetNotFoundError(f"Evaluation dataset {dataset_id} not found in this workspace")
        return dataset

    @classmethod
    async def update_dataset(
        cls,
        session: AsyncSession,
        dataset_id: UUID,
        dataset_in: EvaluationDatasetUpdate,
        workspace_id: Optional[UUID] = None,
    ) -> EvaluationDataset:
        dataset = await cls.get_dataset(session, dataset_id, workspace_id=workspace_id)
        if dataset_in.name is not None:
            dataset.name = dataset_in.name
        if dataset_in.description is not None:
            dataset.description = dataset_in.description
        if dataset_in.status is not None:
            dataset.status = dataset_in.status.value

        await session.commit()
        await session.refresh(dataset)
        return dataset

    @classmethod
    async def create_dataset_version(
        cls,
        session: AsyncSession,
        dataset_id: UUID,
        version_in: EvaluationDatasetVersionCreate,
        created_by: Optional[UUID] = None,
        workspace_id: Optional[UUID] = None,
    ) -> EvaluationDatasetVersion:
        """
        Creates a new immutable version for a dataset.
        Optionally clones all cases from a previous version.
        """
        dataset = await cls.get_dataset(session, dataset_id, workspace_id=workspace_id)

        # Increment version number
        next_version = dataset.version + 1
        dataset.version = next_version

        new_version_id = uuid.uuid4()
        new_version = EvaluationDatasetVersion(
            id=new_version_id,
            dataset_id=dataset_id,
            version=next_version,
            created_by=created_by,
            description=version_in.description or f"Version {next_version}",
        )
        session.add(new_version)

        # Clone cases if specified
        if version_in.clone_from_version_id:
            old_cases_stmt = select(EvaluationCase).where(
                EvaluationCase.dataset_version_id == version_in.clone_from_version_id
            )
            old_cases = (await session.execute(old_cases_stmt)).scalars().all()
            for oc in old_cases:
                cloned_case = EvaluationCase(
                    id=uuid.uuid4(),
                    dataset_version_id=new_version_id,
                    case_key=oc.case_key,
                    name=oc.name,
                    input_data=dict(oc.input_data or {}),
                    expected_output=oc.expected_output,
                    expected_context=dict(oc.expected_context or {}) if oc.expected_context else None,
                    expected_sources=list(oc.expected_sources or []) if oc.expected_sources else None,
                    assertions=list(oc.assertions or []),
                    case_metadata=dict(oc.case_metadata or {}),
                )
                session.add(cloned_case)

        await session.commit()
        await session.refresh(new_version)
        return new_version

    @classmethod
    async def get_latest_version(
        cls,
        session: AsyncSession,
        dataset_id: UUID,
    ) -> EvaluationDatasetVersion:
        stmt = (
            select(EvaluationDatasetVersion)
            .where(EvaluationDatasetVersion.dataset_id == dataset_id)
            .order_by(EvaluationDatasetVersion.version.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        version = result.scalar_one_or_none()
        if not version:
            raise DatasetVersionNotFoundError(f"No versions found for dataset {dataset_id}")
        return version

    @classmethod
    async def import_cases(
        cls,
        session: AsyncSession,
        dataset_id: UUID,
        raw_bytes: bytes,
        file_format: str,  # "json" | "jsonl" | "csv"
        target_version_id: Optional[UUID] = None,
        workspace_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Parses and imports evaluation cases from JSON, JSONL, or CSV format.
        Enforces MAX_DATASET_BYTES and MAX_EVALUATION_CASES limits.
        """
        validate_dataset_import_payload(raw_bytes)
        dataset = await cls.get_dataset(session, dataset_id, workspace_id=workspace_id)

        version = None
        if target_version_id:
            stmt = select(EvaluationDatasetVersion).where(EvaluationDatasetVersion.id == target_version_id)
            version = (await session.execute(stmt)).scalar_one_or_none()
            if not version:
                raise DatasetVersionNotFoundError(f"Version {target_version_id} not found")
        else:
            version = await cls.get_latest_version(session, dataset_id)

        await EvaluationLabPolicy.assert_dataset_version_editable(session, version.id)

        text_content = raw_bytes.decode("utf-8", errors="replace")
        parsed_rows: List[Dict[str, Any]] = []

        fmt = file_format.lower().strip()
        if fmt == "json":
            try:
                data = json.loads(text_content)
                if isinstance(data, list):
                    parsed_rows = data
                elif isinstance(data, dict) and "cases" in data:
                    parsed_rows = data["cases"]
                else:
                    raise DatasetImportError("JSON payload must be a list of case objects or have a 'cases' key")
            except json.JSONDecodeError as e:
                raise DatasetImportError(f"Malformed JSON import: {str(e)}")

        elif fmt == "jsonl":
            for idx, line in enumerate(text_content.splitlines()):
                line = line.strip()
                if not line:
                    continue
                try:
                    parsed_rows.append(json.loads(line))
                except json.JSONDecodeError as e:
                    raise DatasetImportError(f"Malformed JSONL line {idx+1}: {str(e)}")

        elif fmt == "csv":
            try:
                reader = csv.DictReader(io.StringIO(text_content))
                for row in reader:
                    # Parse JSON subfields if serialized
                    input_data = {}
                    if "input_data" in row and row["input_data"]:
                        try:
                            input_data = json.loads(row["input_data"])
                        except Exception:
                            input_data = {"input": row["input_data"]}
                    elif "input" in row:
                        input_data = {"input": row["input"]}

                    assertions = []
                    if "assertions" in row and row["assertions"]:
                        try:
                            assertions = json.loads(row["assertions"])
                        except Exception:
                            pass

                    parsed_rows.append({
                        "case_key": row.get("case_key") or row.get("key"),
                        "name": row.get("name") or row.get("title") or "Imported Case",
                        "input_data": input_data,
                        "expected_output": row.get("expected_output") or row.get("output"),
                        "assertions": assertions,
                    })
            except Exception as e:
                raise DatasetImportError(f"Malformed CSV import: {str(e)}")
        else:
            raise DatasetImportError(f"Unsupported import format: {file_format}. Supported: json, jsonl, csv")

        if len(parsed_rows) > settings.MAX_EVALUATION_CASES:
            raise DatasetImportError(
                f"Import exceeds MAX_EVALUATION_CASES ({len(parsed_rows)} > {settings.MAX_EVALUATION_CASES})"
            )

        # Check existing keys in version to prevent collisions
        existing_cases_stmt = select(EvaluationCase.case_key).where(EvaluationCase.dataset_version_id == version.id)
        existing_keys = set((await session.execute(existing_cases_stmt)).scalars().all())

        imported_count = 0
        skipped_count = 0

        for idx, row in enumerate(parsed_rows):
            key = row.get("case_key") or row.get("key") or f"case_{idx+1}"
            if key in existing_keys:
                skipped_count += 1
                continue

            name = row.get("name") or row.get("title") or f"Case {key}"
            input_data = row.get("input_data") or {"input": row.get("input", "")}

            sanitized = validate_and_sanitize_case_payload(
                input_data=input_data,
                expected_output=row.get("expected_output"),
                expected_context=row.get("expected_context"),
                expected_sources=row.get("expected_sources"),
                assertions=row.get("assertions", []),
                metadata=row.get("metadata", {}),
            )

            case = EvaluationCase(
                id=uuid.uuid4(),
                dataset_version_id=version.id,
                case_key=key,
                name=name,
                input_data=sanitized["input_data"],
                expected_output=sanitized["expected_output"],
                expected_context=sanitized["expected_context"],
                expected_sources=sanitized["expected_sources"],
                assertions=sanitized["assertions"],
                case_metadata=sanitized["metadata"],
            )
            session.add(case)
            existing_keys.add(key)
            imported_count += 1

        await session.commit()
        return {
            "dataset_id": str(dataset.id),
            "version_id": str(version.id),
            "version": version.version,
            "total_rows": len(parsed_rows),
            "imported_count": imported_count,
            "skipped_count": skipped_count,
        }

    @classmethod
    async def export_cases(
        cls,
        session: AsyncSession,
        dataset_id: UUID,
        export_format: str = "json",  # "json" | "jsonl"
        version_id: Optional[UUID] = None,
        workspace_id: Optional[UUID] = None,
    ) -> str:
        """
        Exports all cases of a dataset version as JSON or JSONL.
        """
        await cls.get_dataset(session, dataset_id, workspace_id=workspace_id)
        if version_id:
            v_stmt = select(EvaluationDatasetVersion).where(EvaluationDatasetVersion.id == version_id)
            version = (await session.execute(v_stmt)).scalar_one_or_none()
            if not version:
                raise DatasetVersionNotFoundError(f"Version {version_id} not found")
        else:
            version = await cls.get_latest_version(session, dataset_id)

        cases_stmt = (
            select(EvaluationCase)
            .where(EvaluationCase.dataset_version_id == version.id)
            .order_by(EvaluationCase.created_at.asc())
        )
        cases = (await session.execute(cases_stmt)).scalars().all()

        exported_items = []
        for c in cases:
            exported_items.append({
                "case_key": c.case_key,
                "name": c.name,
                "input_data": c.input_data,
                "expected_output": c.expected_output,
                "expected_context": c.expected_context,
                "expected_sources": c.expected_sources,
                "assertions": c.assertions,
                "metadata": c.case_metadata,
            })

        if export_format.lower() == "jsonl":
            return "\n".join(json.dumps(item) for item in exported_items)
        return json.dumps({"cases": exported_items, "dataset_id": str(dataset_id), "version": version.version}, indent=2)
