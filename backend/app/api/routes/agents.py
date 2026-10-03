"""
API Routes for Step 40: Governed AI Agent Runtime and Multi-Agent Teams.
Internal endpoints mounted under /api/agents, /api/agent-teams, /api/agent-runs, /api/agent-team-runs.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.db.database import get_db
from backend.app.db.models.user import User
from backend.app.services.agents.errors import (
    AgentError,
    AgentLifecycleError,
    AgentNotFoundError,
    AgentRunNotFoundError,
    AgentTeamNotFoundError,
    AgentTeamRunNotFoundError,
    AgentVersionNotFoundError,
    CapabilityNotGrantedError,
    DelegationBudgetExceededError,
    DelegationCycleDetectedError,
    DelegationDepthExceededError,
)
from backend.app.services.agents.schemas import (
    AgentConflictResolveRequest,
    AgentConflictResponse,
    AgentCreate,
    AgentDelegationCreate,
    AgentDelegationResponse,
    AgentDetailResponse,
    AgentResponse,
    AgentRunCreate,
    AgentRunResponse,
    AgentTeamCreate,
    AgentTeamDetailResponse,
    AgentTeamResponse,
    AgentTeamRunCreate,
    AgentTeamRunResponse,
    AgentTeamUpdate,
    AgentUpdate,
    AgentVersionCreate,
    AgentVersionResponse,
    EffectivePolicyPreview,
)
from backend.app.services.agents.service import AgentService

agents_router = APIRouter(prefix="/agents", tags=["Agents"])
teams_router = APIRouter(prefix="/agent-teams", tags=["Agent Teams"])
runs_router = APIRouter(tags=["Agent Runs"])


def _extract_workspace_id(workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")) -> str:
    if not workspace_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Header 'X-Workspace-ID' is required.",
        )
    return workspace_id


# =============================================================================
# AGENT CRUD & LIFECYCLE
# =============================================================================

@agents_router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    req: AgentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = AgentService(db)
    agent, _ = await service.create_agent(workspace_id, str(current_user.id), req)
    return agent


@agents_router.get("", response_model=List[AgentResponse])
async def list_agents(
    project_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = AgentService(db)
    agents, _ = await service.list_agents(workspace_id, project_id, status, limit, offset)
    return agents


@agents_router.get("/{agent_id}", response_model=AgentDetailResponse)
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = AgentService(db)
    try:
        agent = await service.get_agent(agent_id, workspace_id)
        current_ver = None
        if agent.current_version_id:
            ver = await service.repo.get_version(agent.current_version_id)
            if ver:
                current_ver = AgentVersionResponse.model_validate(ver)

        vers = await service.repo.list_versions(agent_id)
        runs, run_count = await service.repo.list_runs(workspace_id, agent_id=agent_id, limit=1)

        resp = AgentDetailResponse.model_validate(agent)
        resp.current_version = current_ver
        resp.versions_count = len(vers)
        resp.runs_count = run_count
        return resp
    except AgentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@agents_router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    req: AgentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = AgentService(db)
    try:
        return await service.update_agent(agent_id, workspace_id, req)
    except AgentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@agents_router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = AgentService(db)
    try:
        agent = await service.get_agent(agent_id, workspace_id)
        await service.repo.delete_agent(agent)
        await db.commit()
    except AgentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@agents_router.post("/{agent_id}/versions", response_model=AgentVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_agent_version(
    agent_id: str,
    req: AgentVersionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = AgentService(db)
    try:
        return await service.create_agent_version(agent_id, workspace_id, str(current_user.id), req)
    except AgentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@agents_router.get("/{agent_id}/versions", response_model=List[AgentVersionResponse])
async def list_agent_versions(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = AgentService(db)
    await service.get_agent(agent_id, workspace_id)
    return await service.repo.list_versions(agent_id)


@agents_router.post("/{agent_id}/publish", response_model=AgentVersionResponse)
async def publish_agent_version(
    agent_id: str,
    version_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = AgentService(db)
    try:
        target_version_id = version_id
        if not target_version_id:
            agent = await service.get_agent(agent_id, workspace_id)
            target_version_id = agent.current_version_id
        if not target_version_id:
            raise HTTPException(status_code=400, detail="No version specified or found on agent.")
        return await service.publish_version(agent_id, target_version_id, workspace_id, str(current_user.id))
    except (AgentNotFoundError, AgentVersionNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@agents_router.post("/{agent_id}/activate", response_model=AgentResponse)
async def activate_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = AgentService(db)
    try:
        return await service.activate_agent(agent_id, workspace_id, str(current_user.id))
    except AgentLifecycleError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except AgentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@agents_router.post("/{agent_id}/pause", response_model=AgentResponse)
async def pause_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = AgentService(db)
    try:
        return await service.pause_agent(agent_id, workspace_id, str(current_user.id))
    except AgentLifecycleError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except AgentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@agents_router.get("/{agent_id}/preview", response_model=EffectivePolicyPreview)
async def preview_agent_policy(
    agent_id: str,
    version_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = AgentService(db)
    try:
        return await service.preview_effective_policy(agent_id, workspace_id, version_id)
    except (AgentNotFoundError, AgentVersionNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# =============================================================================
# AGENT RUNS & DELEGATION
# =============================================================================

@agents_router.post("/{agent_id}/runs", response_model=AgentRunResponse, status_code=status.HTTP_201_CREATED)
async def run_agent(
    agent_id: str,
    req: AgentRunCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = AgentService(db)
    try:
        return await service.run_agent(agent_id, workspace_id, str(current_user.id), req)
    except (AgentNotFoundError, AgentVersionNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AgentLifecycleError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except CapabilityNotGrantedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@agents_router.get("/{agent_id}/runs", response_model=List[AgentRunResponse])
async def list_agent_runs(
    agent_id: str,
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = AgentService(db)
    runs, _ = await service.list_runs(workspace_id, agent_id=agent_id, status=status, limit=limit, offset=offset)
    return runs


@agents_router.post("/{agent_id}/delegate", response_model=AgentDelegationResponse, status_code=status.HTTP_201_CREATED)
async def delegate_agent(
    agent_id: str,
    req: AgentDelegationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = AgentService(db)
    try:
        return await service.delegate_agent(agent_id, workspace_id, str(current_user.id), req)
    except (DelegationCycleDetectedError, DelegationDepthExceededError, DelegationBudgetExceededError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except (AgentNotFoundError, AgentVersionNotFoundError, AgentRunNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# =============================================================================
# MULTI-AGENT TEAMS
# =============================================================================

@teams_router.post("", response_model=AgentTeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    req: AgentTeamCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = AgentService(db)
    try:
        team, _ = await service.create_team(workspace_id, str(current_user.id), req)
        return team
    except (AgentNotFoundError, AgentVersionNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@teams_router.get("", response_model=List[AgentTeamResponse])
async def list_teams(
    project_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = AgentService(db)
    teams, _ = await service.list_teams(workspace_id, project_id, status, limit, offset)
    return teams


@teams_router.get("/{team_id}", response_model=AgentTeamDetailResponse)
async def get_team(
    team_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = AgentService(db)
    try:
        team = await service.get_team(team_id, workspace_id)
        current_ver = None
        members_count = 0
        if team.current_version_id:
            ver = await service.repo.get_team_version(team.current_version_id)
            if ver:
                current_ver = ver
                members_count = len(ver.members)

        runs, run_count = await service.repo.list_team_runs(workspace_id, team_id=team_id, limit=1)
        resp = AgentTeamDetailResponse.model_validate(team)
        resp.current_version = current_ver
        resp.members_count = members_count
        resp.runs_count = run_count
        return resp
    except AgentTeamNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@teams_router.patch("/{team_id}", response_model=AgentTeamResponse)
async def update_team(
    team_id: str,
    req: AgentTeamUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = AgentService(db)
    try:
        return await service.update_team(team_id, workspace_id, req)
    except AgentTeamNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@teams_router.post("/{team_id}/activate", response_model=AgentTeamResponse)
async def activate_team(
    team_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = AgentService(db)
    try:
        return await service.activate_team(team_id, workspace_id, str(current_user.id))
    except AgentLifecycleError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except AgentTeamNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@teams_router.post("/{team_id}/pause", response_model=AgentTeamResponse)
async def pause_team(
    team_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = AgentService(db)
    try:
        return await service.pause_team(team_id, workspace_id, str(current_user.id))
    except AgentLifecycleError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except AgentTeamNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@teams_router.post("/{team_id}/runs", response_model=AgentTeamRunResponse, status_code=status.HTTP_201_CREATED)
async def run_team(
    team_id: str,
    req: AgentTeamRunCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = AgentService(db)
    try:
        return await service.run_team(team_id, workspace_id, str(current_user.id), req)
    except AgentTeamNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AgentLifecycleError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@teams_router.get("/{team_id}/runs", response_model=List[AgentTeamRunResponse])
async def list_team_runs(
    team_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = AgentService(db)
    runs, _ = await service.list_team_runs(workspace_id, team_id=team_id, limit=limit, offset=offset)
    return runs


# =============================================================================
# RUN TRACE, REPLAY & CONFLICTS
# =============================================================================

@runs_router.get("/agent-runs/{run_id}", response_model=AgentRunResponse)
async def get_agent_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = AgentService(db)
    try:
        return await service.get_run(run_id, workspace_id)
    except AgentRunNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@runs_router.get("/agent-runs/{run_id}/trace")
async def get_agent_run_trace(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = AgentService(db)
    try:
        return await service.get_run_trace(run_id, workspace_id)
    except AgentRunNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@runs_router.get("/agent-runs/{run_id}/replay")
async def replay_agent_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = AgentService(db)
    try:
        return await service.replay_run(run_id, workspace_id, str(current_user.id))
    except AgentRunNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@runs_router.get("/agent-team-runs/{run_id}", response_model=AgentTeamRunResponse)
async def get_team_run_detail(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = AgentService(db)
    try:
        team_run = await service.get_team_run(run_id, workspace_id)
        resp = AgentTeamRunResponse.model_validate(team_run)
        resp.messages_count = len(team_run.messages)
        resp.conflicts_count = len(team_run.conflicts)
        return resp
    except AgentTeamRunNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@runs_router.post("/agent-team-runs/{run_id}/conflicts/{conflict_id}/resolve", response_model=AgentConflictResponse)
async def resolve_team_conflict(
    run_id: str,
    conflict_id: str,
    req: AgentConflictResolveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: str = Depends(_extract_workspace_id),
):
    service = AgentService(db)
    try:
        return await service.resolve_conflict(
            conflict_id=conflict_id,
            status=req.status,
            resolution=req.resolution,
            resolved_by=str(current_user.id),
        )
    except AgentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
