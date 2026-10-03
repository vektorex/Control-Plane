"""
Prompt Management API Endpoints for Step 28.
Provides full governance, immutability, environments, previews, and safe test execution.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.auth import get_current_user
from backend.app.db.database import get_db
from backend.app.db.models.user import User
from backend.app.services.access_control.authorization import AuthorizationService
from backend.app.services.access_control.permissions import (
    PROMPT_ARCHIVE,
    PROMPT_CREATE,
    PROMPT_EXECUTE,
    PROMPT_PUBLISH,
    PROMPT_READ,
    PROMPT_RELEASE,
    PROMPT_ROLLBACK,
    PROMPT_UPDATE,
)
from backend.app.services.prompts.constants import PromptEnvironment
from backend.app.services.prompts.policies import PromptPolicyEngine
from backend.app.services.prompts.schemas import (
    PromptCreateRequest,
    PromptDiffResponse,
    PromptPreviewRequest,
    PromptPreviewResponse,
    PromptReleaseRequest,
    PromptReleaseResponse,
    PromptResponse,
    PromptRollbackRequest,
    PromptTestExecutionRequest,
    PromptTestExecutionResponse,
    PromptUpdateRequest,
    PromptVersionCreateRequest,
    PromptVersionResponse,
)
from backend.app.services.prompts.service import PromptService

router = APIRouter(prefix="/prompts", tags=["prompts"])


# =============================================================================
# Prompt CRUD
# =============================================================================

@router.post("", response_model=PromptResponse, status_code=status.HTTP_201_CREATED)
async def create_prompt(
    request: PromptCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PromptResponse:
    """
    Creates a new Prompt asset scoped to a workspace/project.
    """
    if not request.workspace_id:
        from backend.app.db.models.workspace import Workspace
        ws_res = await db.execute(
            select(Workspace).where(Workspace.owner_user_id == user.id).order_by(Workspace.created_at.desc())
        )
        ws = ws_res.scalar_one_or_none()
        if not ws:
            ws = Workspace(
                name="Default Workspace",
                slug=f"ws-{user.id.hex[:8]}",
                owner_user_id=user.id,
            )
            db.add(ws)
            await db.flush()
        request.workspace_id = ws.id

    auth = AuthorizationService(db)
    await auth.authorize(
        user=user,
        permission=PROMPT_CREATE,
        workspace_id=request.workspace_id,
        project_id=request.project_id,
    )
    context = await auth.resolve_context(user=user, workspace_id=request.workspace_id)
    org_id = context.organization_id

    service = PromptService(db)
    return await service.create_prompt(request, owner=user, organization_id=org_id)


@router.get("", response_model=List[PromptResponse])
async def list_prompts(
    workspace_id: Optional[UUID] = Query(None, description="Workspace ID"),
    project_id: Optional[UUID] = Query(None, description="Optional Project ID filter"),
    prompt_type: Optional[str] = Query(None, description="Prompt type filter"),
    status_filter: Optional[str] = Query("active", alias="status", description="Status filter"),
    owner_user_id: Optional[UUID] = Query(None, description="Owner User ID filter"),
    search: Optional[str] = Query(None, description="Search term across name, key, description"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[PromptResponse]:
    """
    Lists prompts for the workspace matching filters.
    """
    if not workspace_id:
        from backend.app.db.models.workspace import Workspace
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
            project_id=project_id,
        )

    service = PromptService(db)
    return await service.list_prompts(
        workspace_id=workspace_id,
        project_id=project_id,
        prompt_type=prompt_type,
        status=status_filter,
        owner_user_id=owner_user_id,
        search=search,
    )


@router.get("/{prompt_id}", response_model=PromptResponse)
async def get_prompt(
    prompt_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PromptResponse:
    """
    Retrieves full details of a Prompt including its active releases.
    """
    service = PromptService(db)
    prompt = await service.get_prompt(prompt_id)
    if not prompt:
        from backend.app.services.prompts.errors import PromptNotFoundError
        raise PromptNotFoundError(f"Prompt {prompt_id} not found.")

    await PromptPolicyEngine.authorize_prompt_access(
        session=db,
        user=user,
        permission=PROMPT_READ,
        prompt=prompt,
    )
    return await service.get_prompt_response(prompt_id)


@router.patch("/{prompt_id}", response_model=PromptResponse)
async def update_prompt(
    prompt_id: UUID,
    request: PromptUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PromptResponse:
    """
    Updates prompt metadata (name, description, prompt_type).
    """
    service = PromptService(db)
    prompt = await service.get_prompt(prompt_id)
    if not prompt:
        from backend.app.services.prompts.errors import PromptNotFoundError
        raise PromptNotFoundError(f"Prompt {prompt_id} not found.")

    await PromptPolicyEngine.authorize_prompt_access(
        session=db,
        user=user,
        permission=PROMPT_UPDATE,
        prompt=prompt,
    )
    return await service.update_prompt(prompt_id, request)


@router.delete("/{prompt_id}", response_model=PromptResponse)
async def delete_prompt(
    prompt_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PromptResponse:
    """
    Archives a prompt.
    """
    service = PromptService(db)
    prompt = await service.get_prompt(prompt_id)
    if not prompt:
        from backend.app.services.prompts.errors import PromptNotFoundError
        raise PromptNotFoundError(f"Prompt {prompt_id} not found.")

    await PromptPolicyEngine.authorize_prompt_access(
        session=db,
        user=user,
        permission=PROMPT_ARCHIVE,
        prompt=prompt,
    )
    return await service.archive_prompt(prompt_id, user_id=user.id)


# =============================================================================
# Version Management
# =============================================================================

@router.post("/{prompt_id}/versions", response_model=PromptVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_version(
    prompt_id: UUID,
    request: PromptVersionCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PromptVersionResponse:
    """
    Creates a new draft version for a prompt.
    """
    service = PromptService(db)
    prompt = await service.get_prompt(prompt_id)
    if not prompt:
        from backend.app.services.prompts.errors import PromptNotFoundError
        raise PromptNotFoundError(f"Prompt {prompt_id} not found.")

    await PromptPolicyEngine.authorize_prompt_access(
        session=db,
        user=user,
        permission=PROMPT_UPDATE,
        prompt=prompt,
    )
    return await service.create_version(prompt_id, request, created_by=user.id)


@router.get("/{prompt_id}/versions", response_model=List[PromptVersionResponse])
async def list_versions(
    prompt_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[PromptVersionResponse]:
    """
    Lists all versions for a prompt.
    """
    service = PromptService(db)
    prompt = await service.get_prompt(prompt_id)
    if not prompt:
        from backend.app.services.prompts.errors import PromptNotFoundError
        raise PromptNotFoundError(f"Prompt {prompt_id} not found.")

    await PromptPolicyEngine.authorize_prompt_access(
        session=db,
        user=user,
        permission=PROMPT_READ,
        prompt=prompt,
    )
    return await service.list_versions(prompt_id)


@router.get("/{prompt_id}/diff", response_model=PromptDiffResponse)
@router.get("/{prompt_id}/versions/diff", response_model=PromptDiffResponse)
async def compare_versions(
    prompt_id: UUID,
    from_version: Optional[int] = Query(None, description="Base version number"),
    to_version: Optional[int] = Query(None, description="Target version number"),
    base_version_id: Optional[UUID] = Query(None, description="Base version UUID"),
    target_version_id: Optional[UUID] = Query(None, description="Target version UUID"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PromptDiffResponse:
    """
    Calculates unified diff and schema/config comparisons between two versions.
    """
    service = PromptService(db)
    prompt = await service.get_prompt(prompt_id)
    if not prompt:
        from backend.app.services.prompts.errors import PromptNotFoundError
        raise PromptNotFoundError(f"Prompt {prompt_id} not found.")

    await PromptPolicyEngine.authorize_prompt_access(
        session=db,
        user=user,
        permission=PROMPT_READ,
        prompt=prompt,
    )

    if from_version is None and base_version_id is not None:
        v_base = await service.repo.get_version_by_id(base_version_id)
        if v_base:
            from_version = v_base.version_number

    if to_version is None and target_version_id is not None:
        v_target = await service.repo.get_version_by_id(target_version_id)
        if v_target:
            to_version = v_target.version_number

    if from_version is None or to_version is None:
        from backend.app.services.prompts.errors import PromptError
        raise PromptError("Must provide from_version and to_version or base_version_id and target_version_id")

    return await service.compare_versions(prompt_id, from_version, to_version)


@router.get("/{prompt_id}/versions/{version_id}", response_model=PromptVersionResponse)
async def get_version(
    prompt_id: UUID,
    version_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PromptVersionResponse:
    """
    Retrieves a specific prompt version.
    """
    service = PromptService(db)
    prompt = await service.get_prompt(prompt_id)
    if not prompt:
        from backend.app.services.prompts.errors import PromptNotFoundError
        raise PromptNotFoundError(f"Prompt {prompt_id} not found.")

    await PromptPolicyEngine.authorize_prompt_access(
        session=db,
        user=user,
        permission=PROMPT_READ,
        prompt=prompt,
    )
    return await service.get_version(version_id)


@router.post("/{prompt_id}/versions/{version_id}/publish", response_model=PromptVersionResponse)
async def publish_version(
    prompt_id: UUID,
    version_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PromptVersionResponse:
    """
    Publishes a version, rendering it permanently immutable.
    """
    service = PromptService(db)
    prompt = await service.get_prompt(prompt_id)
    if not prompt:
        from backend.app.services.prompts.errors import PromptNotFoundError
        raise PromptNotFoundError(f"Prompt {prompt_id} not found.")

    await PromptPolicyEngine.authorize_prompt_access(
        session=db,
        user=user,
        permission=PROMPT_PUBLISH,
        prompt=prompt,
    )
    return await service.publish_version(prompt_id, version_id, user_id=user.id)


# =============================================================================
# Release & Rollback APIs
# =============================================================================

@router.get("/{prompt_id}/releases", response_model=List[PromptReleaseResponse])
async def list_releases(
    prompt_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[PromptReleaseResponse]:
    """
    Lists release transitions for a prompt across environments.
    """
    service = PromptService(db)
    prompt = await service.get_prompt(prompt_id)
    if not prompt:
        from backend.app.services.prompts.errors import PromptNotFoundError
        raise PromptNotFoundError(f"Prompt {prompt_id} not found.")

    await PromptPolicyEngine.authorize_prompt_access(
        session=db,
        user=user,
        permission=PROMPT_READ,
        prompt=prompt,
    )
    releases = await service.repo.list_releases(prompt_id)
    return [
        PromptReleaseResponse(
            id=r.id,
            prompt_id=r.prompt_id,
            environment=r.environment,
            version_id=r.version_id,
            version_number=r.version.version_number if r.version else None,
            status=r.status,
            released_by=r.released_by,
            released_at=r.released_at,
            previous_version_id=r.previous_version_id,
        )
        for r in releases
    ]


@router.post("/{prompt_id}/releases", response_model=PromptReleaseResponse)
async def create_release(
    prompt_id: UUID,
    request: PromptReleaseRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PromptReleaseResponse:
    """
    Releases/promotes a published prompt version to an environment.
    """
    service = PromptService(db)
    prompt = await service.get_prompt(prompt_id)
    if not prompt:
        from backend.app.services.prompts.errors import PromptNotFoundError
        raise PromptNotFoundError(f"Prompt {prompt_id} not found.")

    await PromptPolicyEngine.authorize_prompt_access(
        session=db,
        user=user,
        permission=PROMPT_RELEASE,
        prompt=prompt,
    )

    release = await service.release_version(
        prompt_id=prompt_id,
        environment=request.environment,
        version_id=request.version_id,
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


@router.post("/{prompt_id}/rollback", response_model=PromptReleaseResponse)
async def rollback_release(
    prompt_id: UUID,
    request: PromptRollbackRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PromptReleaseResponse:
    """
    Rolls back an environment's active release to a prior version.
    """
    service = PromptService(db)
    prompt = await service.get_prompt(prompt_id)
    if not prompt:
        from backend.app.services.prompts.errors import PromptNotFoundError
        raise PromptNotFoundError(f"Prompt {prompt_id} not found.")

    await PromptPolicyEngine.authorize_prompt_access(
        session=db,
        user=user,
        permission=PROMPT_ROLLBACK,
        prompt=prompt,
    )

    release = await service.rollback(
        prompt_id=prompt_id,
        environment=request.environment,
        user_id=user.id,
        target_version_id=request.target_version_id,
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


@router.get("/{prompt_id}/resolve")
async def resolve_prompt(
    prompt_id: UUID,
    environment: str = Query("production", description="development, staging, production"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Resolves the active release for a prompt in an environment.
    """
    service = PromptService(db)
    prompt = await service.get_prompt(prompt_id)
    if not prompt:
        from backend.app.services.prompts.errors import PromptNotFoundError
        raise PromptNotFoundError(f"Prompt {prompt_id} not found.")

    await PromptPolicyEngine.authorize_prompt_access(
        session=db,
        user=user,
        permission=PROMPT_READ,
        prompt=prompt,
    )

    resolved = await service.resolver.resolve(
        workspace_id=prompt.workspace_id,
        prompt_id=prompt.id,
        environment=environment,
    )
    return {
        "prompt_id": str(resolved.prompt_id),
        "prompt_key": resolved.prompt_key,
        "version_id": str(resolved.version_id),
        "version_number": resolved.version_number,
        "content_hash": resolved.content_hash,
        "environment": resolved.environment,
        "resolution_mode": resolved.resolution_mode,
        "content": resolved.content,
        "variable_schema": resolved.variable_schema,
        "model_requirements": resolved.model_requirements,
        "execution_config": resolved.execution_config,
        "version": {
            "id": str(resolved.version_id),
            "version_number": resolved.version_number,
            "content": resolved.content,
        },
    }


# =============================================================================
# Preview & Test Execution APIs
# =============================================================================

@router.post("/{prompt_id}/preview", response_model=PromptPreviewResponse)
async def preview_prompt(
    prompt_id: UUID,
    request: PromptPreviewRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PromptPreviewResponse:
    """
    Renders variables deterministically without calling any AI model.
    """
    service = PromptService(db)
    prompt = await service.get_prompt(prompt_id)
    if not prompt:
        from backend.app.services.prompts.errors import PromptNotFoundError
        raise PromptNotFoundError(f"Prompt {prompt_id} not found.")

    await PromptPolicyEngine.authorize_prompt_access(
        session=db,
        user=user,
        permission=PROMPT_READ,
        prompt=prompt,
    )
    return await service.preview_prompt(prompt_id, request)


@router.post("/{prompt_id}/test", response_model=PromptTestExecutionResponse)
async def test_prompt_execution(
    prompt_id: UUID,
    request: PromptTestExecutionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PromptTestExecutionResponse:
    """
    Safely tests prompt execution through the authoritative AI Gateway runtime.
    """
    service = PromptService(db)
    prompt = await service.get_prompt(prompt_id)
    if not prompt:
        from backend.app.services.prompts.errors import PromptNotFoundError
        raise PromptNotFoundError(f"Prompt {prompt_id} not found.")

    await PromptPolicyEngine.authorize_prompt_access(
        session=db,
        user=user,
        permission=PROMPT_EXECUTE,
        prompt=prompt,
    )
    return await service.test_execution(
        prompt_id=prompt_id,
        request=request,
        workspace_id=prompt.workspace_id,
        user=user,
    )
