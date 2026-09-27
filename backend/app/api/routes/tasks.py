from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.auth import get_current_user
from backend.app.db.database import get_db
from backend.app.db.models.user import User
from backend.app.repositories.task import TaskRepository
from backend.app.repositories.run import RunRepository
from backend.app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
    TaskRunRequest,
)
from backend.app.schemas.run import (
    RunCreate,
    RunResponse,
    RunListResponse,
)
from backend.app.services.llm.factory import LLMProviderFactory, get_llm_factory
from backend.app.services.task_execution import TaskExecutionService

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("", response_model=TaskListResponse)
async def list_all_tasks(
    status: Optional[str] = Query(None, description="Filter by status (draft, active, completed, archived)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TaskListResponse:
    """
    List all tasks belonging to the authenticated user across all owned projects.
    """
    repo = TaskRepository(session)
    tasks, total = await repo.list_by_owner(user.id, status=status, skip=skip, limit=limit)
    response_items = []
    for t in tasks:
        item = TaskResponse.model_validate(t)
        item.run_count = len(t.runs) if hasattr(t, "runs") and t.runs is not None else 0
        response_items.append(item)
    return TaskListResponse(tasks=response_items, total=total)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """
    Retrieve task details for an owned task. Returns 404 if not found or unowned.
    """
    repo = TaskRepository(session)
    task = await repo.get_by_id_and_owner_or_raise(task_id, user.id)
    response = TaskResponse.model_validate(task)
    response.run_count = len(task.runs) if hasattr(task, "runs") and task.runs is not None else 0
    return response


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    data: TaskUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """
    Update task title, description, instructions, context, or lifecycle status for an owned task.
    """
    repo = TaskRepository(session)
    task = await repo.update(task_id, user.id, data)
    response = TaskResponse.model_validate(task)
    response.run_count = len(task.runs) if hasattr(task, "runs") and task.runs is not None else 0
    return response


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Delete an owned task and cascade-delete all associated execution runs.
    """
    repo = TaskRepository(session)
    await repo.delete(task_id, user.id)
    return None


# --- Task AI Execution Endpoints ---

@router.post("/{task_id}/run", response_model=RunResponse, status_code=status.HTTP_201_CREATED)
async def execute_task(
    task_id: UUID,
    request: Optional[TaskRunRequest] = None,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    factory: LLMProviderFactory = Depends(get_llm_factory),
) -> RunResponse:
    """
    Execute a Task against the LLM abstraction and record the resulting execution Run.
    Enforces user ownership and full telemetry capture.
    """
    req = request or TaskRunRequest()
    service = TaskExecutionService(session, factory)
    run = await service.execute_task(task_id, user, req)
    return RunResponse.model_validate(run)


@router.post("/{task_id}/run/stream")
async def execute_task_stream(
    task_id: UUID,
    request: Optional[TaskRunRequest] = None,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    factory: LLMProviderFactory = Depends(get_llm_factory),
):
    """
    Execute a Task with Server-Sent Events (SSE) streaming while persisting the Run record.
    """
    req = request or TaskRunRequest()
    service = TaskExecutionService(session, factory)

    return StreamingResponse(
        service.execute_task_stream(task_id, user, req),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Type": "text/event-stream; charset=utf-8",
        },
    )


# --- Nested Task Runs History Routes ---

@router.get("/{task_id}/runs", response_model=RunListResponse)
async def list_task_runs(
    task_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> RunListResponse:
    """
    Retrieve execution telemetry runs associated with an owned task.
    """
    repo = RunRepository(session)
    runs, total = await repo.list_by_task(task_id, user.id, skip=skip, limit=limit)
    return RunListResponse(
        runs=[RunResponse.model_validate(r) for r in runs],
        total=total,
    )


@router.post("/{task_id}/runs", response_model=RunResponse, status_code=status.HTTP_201_CREATED)
async def create_task_run(
    task_id: UUID,
    data: RunCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> RunResponse:
    """
    Record an execution run against an owned task.
    """
    repo = RunRepository(session)
    run = await repo.create(task_id, user.id, data)
    return RunResponse.model_validate(run)
