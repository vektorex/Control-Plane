"""
API Endpoints for Prompt Experiments (Step 28).
Provides A/B variant tracking, deterministic allocation, factual results reporting,
and human-governed version promotion.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.auth import get_current_user
from backend.app.db.database import get_db
from backend.app.db.models.user import User
from backend.app.services.access_control.authorization import AuthorizationService
from backend.app.services.access_control.permissions import (
    PROMPT_EXPERIMENT,
    PROMPT_READ,
    PROMPT_RELEASE,
)
from backend.app.services.prompts.errors import PromptExperimentNotFoundError
from backend.app.services.prompts.experiments import PromptExperimentService
from backend.app.services.prompts.policies import PromptPolicyEngine
from backend.app.services.prompts.schemas import (
    PromptExperimentCreateRequest,
    PromptExperimentResponse,
    PromptExperimentResultsResponse,
    PromptExperimentUpdateRequest,
    PromptExperimentVariantInput,
    PromptExperimentVariantResponse,
    PromptReleaseResponse,
)

router = APIRouter(prefix="/prompt-experiments", tags=["prompt-experiments"])


class PromoteVariantRequest(BaseModel):
    chosen_version_id: UUID
    environment: str = Field(default="production", description="Target release environment")


@router.post("", response_model=PromptExperimentResponse, status_code=status.HTTP_201_CREATED)
async def create_experiment(
    request: PromptExperimentCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PromptExperimentResponse:
    """
    Creates a new A/B prompt experiment.
    """
    if not request.workspace_id:
        from backend.app.services.prompts.repository import PromptRepository
        p_repo = PromptRepository(db)
        prompt = await p_repo.get_prompt_by_id(request.prompt_id, include_relations=False)
        if prompt:
            request.workspace_id = prompt.workspace_id
            request.project_id = request.project_id or prompt.project_id
        else:
            from backend.app.db.models.workspace import Workspace
            from sqlalchemy import select
            ws_res = await db.execute(
                select(Workspace).where(Workspace.owner_user_id == user.id).order_by(Workspace.created_at.desc())
            )
            ws = ws_res.scalar_one_or_none()
            if ws:
                request.workspace_id = ws.id

    auth = AuthorizationService(db)
    await auth.authorize(
        user=user,
        permission=PROMPT_EXPERIMENT,
        workspace_id=request.workspace_id,
        project_id=request.project_id,
    )
    context = await auth.resolve_context(user=user, workspace_id=request.workspace_id)

    service = PromptExperimentService(db)
    exp = await service.create_experiment(
        request=request,
        created_by=user.id,
        organization_id=context.organization_id,
    )
    return PromptExperimentResponse.model_validate(exp)


@router.get("", response_model=List[PromptExperimentResponse])
async def list_experiments(
    workspace_id: Optional[UUID] = Query(None, description="Workspace ID"),
    prompt_id: Optional[UUID] = Query(None, description="Optional prompt filter"),
    status_filter: Optional[str] = Query(None, alias="status", description="Status filter"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[PromptExperimentResponse]:
    """
    Lists experiments for a workspace.
    """
    if not workspace_id and prompt_id:
        from backend.app.services.prompts.repository import PromptRepository
        p_repo = PromptRepository(db)
        prompt = await p_repo.get_prompt_by_id(prompt_id, include_relations=False)
        if prompt:
            workspace_id = prompt.workspace_id

    if not workspace_id:
        from backend.app.db.models.workspace import Workspace
        from sqlalchemy import select
        ws_res = await db.execute(
            select(Workspace).where(Workspace.owner_user_id == user.id).order_by(Workspace.created_at.desc())
        )
        ws = ws_res.scalar_one_or_none()
        if ws:
            workspace_id = ws.id

    if workspace_id:
        auth = AuthorizationService(db)
        await auth.authorize(
            user=user,
            permission=PROMPT_READ,
            workspace_id=workspace_id,
        )
    service = PromptExperimentService(db)
    experiments = await service.repo.list_experiments(
        workspace_id=workspace_id,
        prompt_id=prompt_id,
        status=status_filter,
    )
    return [PromptExperimentResponse.model_validate(e) for e in experiments]


@router.get("/{id}", response_model=PromptExperimentResponse)
async def get_experiment(
    id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PromptExperimentResponse:
    """
    Retrieves full details of an experiment.
    """
    service = PromptExperimentService(db)
    exp = await service.repo.get_experiment_by_id(id)
    if not exp:
        raise PromptExperimentNotFoundError(f"Experiment {id} not found.")

    auth = AuthorizationService(db)
    await auth.authorize(
        user=user,
        permission=PROMPT_READ,
        workspace_id=exp.workspace_id,
        project_id=exp.project_id,
    )
    return PromptExperimentResponse.model_validate(exp)


@router.patch("/{id}", response_model=PromptExperimentResponse)
async def update_experiment(
    id: UUID,
    request: PromptExperimentUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PromptExperimentResponse:
    """
    Updates experiment metadata.
    """
    service = PromptExperimentService(db)
    exp = await service.repo.get_experiment_by_id(id)
    if not exp:
        raise PromptExperimentNotFoundError(f"Experiment {id} not found.")

    auth = AuthorizationService(db)
    await auth.authorize(
        user=user,
        permission=PROMPT_EXPERIMENT,
        workspace_id=exp.workspace_id,
        project_id=exp.project_id,
    )

    if request.name:
        exp.name = request.name
    if request.description is not None:
        exp.description = request.description
    await db.flush()

    return PromptExperimentResponse.model_validate(exp)


@router.post("/{id}/variants", response_model=PromptExperimentResponse)
async def add_variant(
    id: UUID,
    variant_input: PromptExperimentVariantInput,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PromptExperimentResponse:
    """
    Adds a variant to an experiment.
    """
    service = PromptExperimentService(db)
    exp = await service.repo.get_experiment_by_id(id)
    if not exp:
        raise PromptExperimentNotFoundError(f"Experiment {id} not found.")

    auth = AuthorizationService(db)
    await auth.authorize(
        user=user,
        permission=PROMPT_EXPERIMENT,
        workspace_id=exp.workspace_id,
        project_id=exp.project_id,
    )

    from backend.app.services.prompts.models import PromptExperimentVariant
    new_variant = PromptExperimentVariant(
        id=UUID(int=0),  # Assigned by repo or uuid4
        experiment_id=exp.id,
        prompt_version_id=variant_input.prompt_version_id,
        label=variant_input.label.strip(),
        allocation_weight=variant_input.allocation_weight,
    )
    import uuid
    new_variant.id = uuid.uuid4()
    db.add(new_variant)
    await db.flush()

    reloaded = await service.repo.get_experiment_by_id(id)
    return PromptExperimentResponse.model_validate(reloaded)


@router.post("/{id}/start", response_model=PromptExperimentResponse)
async def start_experiment(
    id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PromptExperimentResponse:
    """
    Starts an experiment.
    """
    service = PromptExperimentService(db)
    exp = await service.repo.get_experiment_by_id(id)
    if not exp:
        raise PromptExperimentNotFoundError(f"Experiment {id} not found.")

    auth = AuthorizationService(db)
    await auth.authorize(
        user=user,
        permission=PROMPT_EXPERIMENT,
        workspace_id=exp.workspace_id,
        project_id=exp.project_id,
    )
    started = await service.start_experiment(id, user_id=user.id)
    return PromptExperimentResponse.model_validate(started)


@router.post("/{id}/pause", response_model=PromptExperimentResponse)
async def pause_experiment(
    id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PromptExperimentResponse:
    """
    Pauses an active experiment.
    """
    service = PromptExperimentService(db)
    exp = await service.repo.get_experiment_by_id(id)
    if not exp:
        raise PromptExperimentNotFoundError(f"Experiment {id} not found.")

    auth = AuthorizationService(db)
    await auth.authorize(
        user=user,
        permission=PROMPT_EXPERIMENT,
        workspace_id=exp.workspace_id,
        project_id=exp.project_id,
    )
    paused = await service.pause_experiment(id, user_id=user.id)
    return PromptExperimentResponse.model_validate(paused)


@router.post("/{id}/complete", response_model=PromptExperimentResponse)
async def complete_experiment(
    id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PromptExperimentResponse:
    """
    Completes an experiment.
    """
    service = PromptExperimentService(db)
    exp = await service.repo.get_experiment_by_id(id)
    if not exp:
        raise PromptExperimentNotFoundError(f"Experiment {id} not found.")

    auth = AuthorizationService(db)
    await auth.authorize(
        user=user,
        permission=PROMPT_EXPERIMENT,
        workspace_id=exp.workspace_id,
        project_id=exp.project_id,
    )
    completed = await service.complete_experiment(id, user_id=user.id)
    return PromptExperimentResponse.model_validate(completed)


@router.get("/{id}/results", response_model=PromptExperimentResultsResponse)
async def get_experiment_results(
    id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PromptExperimentResultsResponse:
    """
    Retrieves factual metrics comparison between variants without subjective winner declaration.
    """
    service = PromptExperimentService(db)
    exp = await service.repo.get_experiment_by_id(id)
    if not exp:
        raise PromptExperimentNotFoundError(f"Experiment {id} not found.")

    auth = AuthorizationService(db)
    await auth.authorize(
        user=user,
        permission=PROMPT_READ,
        workspace_id=exp.workspace_id,
        project_id=exp.project_id,
    )
    return await service.get_results(id)


@router.post("/{id}/promote", response_model=PromptReleaseResponse)
async def promote_from_experiment(
    id: UUID,
    request: PromoteVariantRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PromptReleaseResponse:
    """
    Allows authorized human user to promote a tested version from an experiment.
    """
    service = PromptExperimentService(db)
    exp = await service.repo.get_experiment_by_id(id)
    if not exp:
        raise PromptExperimentNotFoundError(f"Experiment {id} not found.")

    auth = AuthorizationService(db)
    await auth.authorize(
        user=user,
        permission=PROMPT_RELEASE,
        workspace_id=exp.workspace_id,
        project_id=exp.project_id,
    )

    release = await service.promote_from_experiment(
        experiment_id=id,
        chosen_version_id=request.chosen_version_id,
        environment=request.environment,
        user_id=user.id,
    )
    return PromptReleaseResponse(
        id=release.id,
        prompt_id=release.prompt_id,
        environment=release.environment,
        version_id=release.version_id,
        version_number=release.version.version_number if release.version else None,
        status=release.status,
        released_by=release.released_by,
        released_at=release.released_at,
        previous_version_id=release.previous_version_id,
    )
