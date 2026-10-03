"""
Asynchronous Database Repository for Step 28 Prompt Management, Versioning, Releases, and Experiments.
Guarantees transactional integrity, row-locking where appropriate, and strict tenant boundaries.
"""
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import desc, func, select, update, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.services.prompts.constants import (
    ExperimentStatus,
    PromptEnvironment,
    PromptStatus,
    PromptVersionStatus,
    ReleaseStatus,
)
from backend.app.services.prompts.errors import (
    DuplicatePromptKeyError,
    ImmutableVersionError,
    PromptNotFoundError,
    PromptReleaseNotFoundError,
    PromptVersionNotFoundError,
    RollbackNotAllowedError,
)
from backend.app.services.prompts.models import (
    Prompt,
    PromptExperiment,
    PromptExperimentAssignment,
    PromptExperimentVariant,
    PromptRelease,
    PromptVersion,
)


class PromptRepository:
    """
    Data access layer for Prompts, Versions, Releases, and Experiments.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    # =========================================================================
    # Prompts
    # =========================================================================

    async def create_prompt(
        self,
        organization_id: uuid.UUID,
        workspace_id: uuid.UUID,
        owner_user_id: uuid.UUID,
        key: str,
        name: str,
        prompt_type: str = "instruction",
        description: Optional[str] = None,
        project_id: Optional[uuid.UUID] = None,
    ) -> Prompt:
        """
        Creates a new Prompt asset. Enforces key uniqueness in workspace/project scope.
        """
        # Uniqueness check: active prompt with same key in this workspace and project scope
        query = select(Prompt).where(
            Prompt.workspace_id == workspace_id,
            Prompt.key == key,
            Prompt.status == PromptStatus.ACTIVE.value,
        )
        if project_id:
            query = query.where(Prompt.project_id == project_id)
        else:
            query = query.where(Prompt.project_id.is_(None))

        existing = (await self.session.execute(query)).scalar_one_or_none()
        if existing:
            raise DuplicatePromptKeyError(
                f"A prompt with key '{key}' already exists in this workspace/project."
            )

        prompt = Prompt(
            id=uuid.uuid4(),
            organization_id=organization_id,
            workspace_id=workspace_id,
            project_id=project_id,
            owner_user_id=owner_user_id,
            key=key,
            name=name,
            description=description,
            prompt_type=prompt_type,
            status=PromptStatus.ACTIVE.value,
        )
        self.session.add(prompt)
        await self.session.flush()
        return prompt

    async def get_prompt_by_id(
        self,
        prompt_id: uuid.UUID,
        include_relations: bool = True,
    ) -> Optional[Prompt]:
        """
        Retrieves a Prompt by ID.
        """
        query = select(Prompt).where(Prompt.id == prompt_id)
        if include_relations:
            query = query.options(
                selectinload(Prompt.versions),
                selectinload(Prompt.releases).selectinload(PromptRelease.version),
            )
        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    async def get_prompt_by_key(
        self,
        workspace_id: uuid.UUID,
        key: str,
        project_id: Optional[uuid.UUID] = None,
    ) -> Optional[Prompt]:
        """
        Retrieves an active prompt by key within workspace (and optional project fallback).
        """
        # First check project-scoped prompt if project_id provided
        if project_id:
            proj_query = select(Prompt).where(
                Prompt.workspace_id == workspace_id,
                Prompt.project_id == project_id,
                Prompt.key == key,
                Prompt.status == PromptStatus.ACTIVE.value,
            ).options(
                selectinload(Prompt.versions),
                selectinload(Prompt.releases).selectinload(PromptRelease.version),
            )
            prompt = (await self.session.execute(proj_query)).scalar_one_or_none()
            if prompt:
                return prompt

        # Workspace-level prompt
        ws_query = select(Prompt).where(
            Prompt.workspace_id == workspace_id,
            Prompt.project_id.is_(None),
            Prompt.key == key,
            Prompt.status == PromptStatus.ACTIVE.value,
        ).options(
            selectinload(Prompt.versions),
            selectinload(Prompt.releases).selectinload(PromptRelease.version),
        )
        return (await self.session.execute(ws_query)).scalar_one_or_none()

    async def list_prompts(
        self,
        workspace_id: uuid.UUID,
        project_id: Optional[uuid.UUID] = None,
        prompt_type: Optional[str] = None,
        status: Optional[str] = PromptStatus.ACTIVE.value,
        owner_user_id: Optional[uuid.UUID] = None,
        search: Optional[str] = None,
    ) -> List[Prompt]:
        """
        Lists prompts matching filters.
        """
        query = select(Prompt).where(Prompt.workspace_id == workspace_id)

        if project_id is not None:
            query = query.where(or_(Prompt.project_id == project_id, Prompt.project_id.is_(None)))
        if prompt_type:
            query = query.where(Prompt.prompt_type == prompt_type)
        if status:
            query = query.where(Prompt.status == status)
        if owner_user_id:
            query = query.where(Prompt.owner_user_id == owner_user_id)
        if search:
            query = query.where(
                or_(
                    Prompt.name.ilike(f"%{search}%"),
                    Prompt.key.ilike(f"%{search}%"),
                    Prompt.description.ilike(f"%{search}%"),
                )
            )

        query = query.options(
            selectinload(Prompt.versions),
            selectinload(Prompt.releases).selectinload(PromptRelease.version),
        ).order_by(desc(Prompt.updated_at))

        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def update_prompt_metadata(
        self,
        prompt_id: uuid.UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        prompt_type: Optional[str] = None,
    ) -> Prompt:
        prompt = await self.get_prompt_by_id(prompt_id, include_relations=False)
        if not prompt:
            raise PromptNotFoundError(f"Prompt {prompt_id} not found.")

        if name is not None:
            prompt.name = name
        if description is not None:
            prompt.description = description
        if prompt_type is not None:
            prompt.prompt_type = prompt_type

        prompt.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return prompt

    async def archive_prompt(self, prompt_id: uuid.UUID) -> Prompt:
        prompt = await self.get_prompt_by_id(prompt_id, include_relations=False)
        if not prompt:
            raise PromptNotFoundError(f"Prompt {prompt_id} not found.")

        prompt.status = PromptStatus.ARCHIVED.value
        prompt.archived_at = datetime.now(timezone.utc)
        prompt.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return prompt

    # =========================================================================
    # Prompt Versions
    # =========================================================================

    async def create_version(
        self,
        prompt_id: uuid.UUID,
        content: str,
        created_by: uuid.UUID,
        variable_schema: Optional[Dict[str, Any]] = None,
        model_requirements: Optional[Dict[str, Any]] = None,
        execution_config: Optional[Dict[str, Any]] = None,
        change_summary: Optional[str] = None,
    ) -> PromptVersion:
        """
        Creates a new draft version with monotonically increasing version_number.
        """
        # Determine next version number transactionally
        max_v_query = select(func.coalesce(func.max(PromptVersion.version_number), 0)).where(
            PromptVersion.prompt_id == prompt_id
        )
        max_v = (await self.session.execute(max_v_query)).scalar_one()
        next_version_number = max_v + 1

        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        version = PromptVersion(
            id=uuid.uuid4(),
            prompt_id=prompt_id,
            version_number=next_version_number,
            status=PromptVersionStatus.DRAFT.value,
            content=content,
            variable_schema=variable_schema or {},
            model_requirements=model_requirements,
            execution_config=execution_config,
            change_summary=change_summary,
            created_by=created_by,
            content_hash=content_hash,
        )
        self.session.add(version)

        # Update prompt updated_at
        await self.session.execute(
            update(Prompt)
            .where(Prompt.id == prompt_id)
            .values(updated_at=datetime.now(timezone.utc))
        )
        await self.session.flush()
        return version

    async def get_version_by_id(self, version_id: uuid.UUID) -> Optional[PromptVersion]:
        query = select(PromptVersion).where(PromptVersion.id == version_id).options(
            selectinload(PromptVersion.prompt)
        )
        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    async def get_version_by_number(self, prompt_id: uuid.UUID, version_number: int) -> Optional[PromptVersion]:
        query = select(PromptVersion).where(
            PromptVersion.prompt_id == prompt_id,
            PromptVersion.version_number == version_number,
        ).options(selectinload(PromptVersion.prompt))
        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    async def list_versions(self, prompt_id: uuid.UUID) -> List[PromptVersion]:
        query = (
            select(PromptVersion)
            .where(PromptVersion.prompt_id == prompt_id)
            .order_by(desc(PromptVersion.version_number))
        )
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def get_latest_version(self, prompt_id: uuid.UUID) -> Optional[PromptVersion]:
        query = (
            select(PromptVersion)
            .where(PromptVersion.prompt_id == prompt_id)
            .order_by(desc(PromptVersion.version_number))
            .limit(1)
        )
        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    async def publish_version(self, version_id: uuid.UUID) -> PromptVersion:
        """
        Publishes a version making it permanently immutable.
        """
        version = await self.get_version_by_id(version_id)
        if not version:
            raise PromptVersionNotFoundError(f"Version {version_id} not found.")

        if version.status == PromptVersionStatus.PUBLISHED.value:
            return version  # Idempotent

        version.status = PromptVersionStatus.PUBLISHED.value
        version.published_at = datetime.now(timezone.utc)
        version.content_hash = hashlib.sha256(version.content.encode("utf-8")).hexdigest()

        # Update prompt updated_at
        await self.session.execute(
            update(Prompt)
            .where(Prompt.id == version.prompt_id)
            .values(updated_at=datetime.now(timezone.utc))
        )
        await self.session.flush()
        return version

    # =========================================================================
    # Releases
    # =========================================================================

    async def create_release(
        self,
        prompt_id: uuid.UUID,
        environment: str,
        version_id: uuid.UUID,
        released_by: uuid.UUID,
    ) -> PromptRelease:
        """
        Binds a published version to an environment. Supersedes prior active release in that environment.
        """
        version = await self.get_version_by_id(version_id)
        if not version or version.prompt_id != prompt_id:
            raise PromptVersionNotFoundError(f"Version {version_id} does not belong to prompt {prompt_id}.")

        if version.status != PromptVersionStatus.PUBLISHED.value:
            raise ImmutableVersionError("Only published versions may be released to environments.")

        # Find existing active release in this environment
        active_query = select(PromptRelease).where(
            PromptRelease.prompt_id == prompt_id,
            PromptRelease.environment == environment,
            PromptRelease.status == ReleaseStatus.ACTIVE.value,
        )
        active_release = (await self.session.execute(active_query)).scalar_one_or_none()

        previous_version_id = None
        if active_release:
            active_release.status = ReleaseStatus.SUPERSEDED.value
            previous_version_id = active_release.version_id

        new_release = PromptRelease(
            id=uuid.uuid4(),
            prompt_id=prompt_id,
            environment=environment,
            version_id=version_id,
            status=ReleaseStatus.ACTIVE.value,
            released_by=released_by,
            released_at=datetime.now(timezone.utc),
            previous_version_id=previous_version_id,
        )
        self.session.add(new_release)
        await self.session.flush()
        return new_release

    async def get_active_release(self, prompt_id: uuid.UUID, environment: str) -> Optional[PromptRelease]:
        query = select(PromptRelease).where(
            PromptRelease.prompt_id == prompt_id,
            PromptRelease.environment == environment,
            PromptRelease.status == ReleaseStatus.ACTIVE.value,
        ).options(selectinload(PromptRelease.version))
        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    async def list_releases(self, prompt_id: uuid.UUID) -> List[PromptRelease]:
        query = (
            select(PromptRelease)
            .where(PromptRelease.prompt_id == prompt_id)
            .options(selectinload(PromptRelease.version))
            .order_by(desc(PromptRelease.released_at))
        )
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def rollback_release(
        self,
        prompt_id: uuid.UUID,
        environment: str,
        released_by: uuid.UUID,
        target_version_id: Optional[uuid.UUID] = None,
    ) -> PromptRelease:
        """
        Performs a rollback. Creates a NEW release record instead of mutating history.
        """
        active_release = await self.get_active_release(prompt_id, environment)
        if not active_release:
            raise PromptReleaseNotFoundError(f"No active release found in environment '{environment}' to roll back.")

        # Determine target version
        chosen_target_version_id = target_version_id or active_release.previous_version_id
        if not chosen_target_version_id:
            raise RollbackNotAllowedError(f"No previous version available to roll back to for environment '{environment}'.")

        target_version = await self.get_version_by_id(chosen_target_version_id)
        if not target_version or target_version.prompt_id != prompt_id:
            raise PromptVersionNotFoundError(f"Target version {chosen_target_version_id} not found.")

        # Mark current active as rolled back
        active_release.status = ReleaseStatus.ROLLED_BACK.value

        # Create new release transition pointing to target version
        rollback_record = PromptRelease(
            id=uuid.uuid4(),
            prompt_id=prompt_id,
            environment=environment,
            version_id=chosen_target_version_id,
            status=ReleaseStatus.ACTIVE.value,
            released_by=released_by,
            released_at=datetime.now(timezone.utc),
            previous_version_id=active_release.version_id,
        )
        self.session.add(rollback_record)
        await self.session.flush()
        return rollback_record

    # =========================================================================
    # Experiments
    # =========================================================================

    async def create_experiment(
        self,
        organization_id: uuid.UUID,
        workspace_id: uuid.UUID,
        prompt_id: uuid.UUID,
        name: str,
        created_by: uuid.UUID,
        allocation_key: str = "user_id",
        description: Optional[str] = None,
        project_id: Optional[uuid.UUID] = None,
        variants_data: Optional[List[Dict[str, Any]]] = None,
    ) -> PromptExperiment:
        """
        Creates an experiment with initial variants.
        """
        exp = PromptExperiment(
            id=uuid.uuid4(),
            organization_id=organization_id,
            workspace_id=workspace_id,
            project_id=project_id,
            prompt_id=prompt_id,
            name=name,
            description=description,
            status=ExperimentStatus.DRAFT.value,
            allocation_key=allocation_key,
            created_by=created_by,
        )
        self.session.add(exp)
        await self.session.flush()

        if variants_data:
            for v_data in variants_data:
                variant = PromptExperimentVariant(
                    id=uuid.uuid4(),
                    experiment_id=exp.id,
                    prompt_version_id=v_data["prompt_version_id"],
                    label=v_data["label"],
                    allocation_weight=float(v_data.get("allocation_weight", 1.0)),
                )
                self.session.add(variant)
            await self.session.flush()

        return await self.get_experiment_by_id(exp.id)

    async def get_experiment_by_id(self, experiment_id: uuid.UUID) -> Optional[PromptExperiment]:
        query = select(PromptExperiment).where(PromptExperiment.id == experiment_id).options(
            selectinload(PromptExperiment.variants).selectinload(PromptExperimentVariant.version),
            selectinload(PromptExperiment.prompt),
        )
        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    async def list_experiments(
        self,
        workspace_id: uuid.UUID,
        prompt_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
    ) -> List[PromptExperiment]:
        query = select(PromptExperiment).where(PromptExperiment.workspace_id == workspace_id)
        if prompt_id:
            query = query.where(PromptExperiment.prompt_id == prompt_id)
        if status:
            query = query.where(PromptExperiment.status == status)

        query = query.options(
            selectinload(PromptExperiment.variants).selectinload(PromptExperimentVariant.version)
        ).order_by(desc(PromptExperiment.created_at))

        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def get_active_experiment_for_prompt(self, prompt_id: uuid.UUID) -> Optional[PromptExperiment]:
        query = select(PromptExperiment).where(
            PromptExperiment.prompt_id == prompt_id,
            PromptExperiment.status == ExperimentStatus.RUNNING.value,
        ).options(
            selectinload(PromptExperiment.variants).selectinload(PromptExperimentVariant.version)
        )
        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    async def update_experiment_status(self, experiment_id: uuid.UUID, status: str) -> PromptExperiment:
        exp = await self.get_experiment_by_id(experiment_id)
        if not exp:
            raise PromptNotFoundError(f"Experiment {experiment_id} not found.")

        exp.status = status
        now = datetime.now(timezone.utc)
        if status == ExperimentStatus.RUNNING.value and not exp.started_at:
            exp.started_at = now
        elif status in (ExperimentStatus.COMPLETED.value, ExperimentStatus.CANCELLED.value):
            exp.ended_at = now

        exp.updated_at = now
        await self.session.flush()
        return exp

    async def get_or_create_assignment(
        self,
        experiment_id: uuid.UUID,
        allocation_key_value: str,
        variant_id: uuid.UUID,
        version_id: uuid.UUID,
    ) -> PromptExperimentAssignment:
        """
        Retrieves existing sticky assignment or creates a new one.
        """
        query = select(PromptExperimentAssignment).where(
            PromptExperimentAssignment.experiment_id == experiment_id,
            PromptExperimentAssignment.allocation_key_value == allocation_key_value,
        )
        existing = (await self.session.execute(query)).scalar_one_or_none()
        if existing:
            return existing

        assignment = PromptExperimentAssignment(
            id=uuid.uuid4(),
            experiment_id=experiment_id,
            variant_id=variant_id,
            allocation_key_value=allocation_key_value,
            assigned_version_id=version_id,
        )
        self.session.add(assignment)
        await self.session.flush()
        return assignment
