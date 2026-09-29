from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.auth import get_current_user
from backend.app.db.database import get_db
from backend.app.core.errors import InvalidStateError, NotFoundError
from backend.app.db.models.enums import RunStatus
from backend.app.db.models.user import User
from backend.app.repositories.evaluation import EvaluationRepository
from backend.app.repositories.run import RunRepository
from backend.app.repositories.task import TaskRepository
from backend.app.schemas.evaluation import (
    EvaluateTaskRequest,
    EvaluateTaskResponse,
    EvaluationRunResponse,
    RunEvaluationHistoryResponse,
)
from backend.app.services.evaluation.engine import get_evaluation_engine
from backend.app.services.evaluation.policies import EvaluationPolicy

router = APIRouter(tags=["Evaluation & Verification"])


@router.post(
    "/tasks/{task_id}/evaluate",
    response_model=EvaluateTaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate the most recent run of a task",
    description="Evaluates output quality, grounding, completeness, citations, format, and safety for the latest completed run of a task.",
)
async def evaluate_task(
    task_id: UUID,
    body: Optional[EvaluateTaskRequest] = None,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> EvaluateTaskResponse:
    task_repo = TaskRepository(session)
    run_repo = RunRepository(session)
    eval_repo = EvaluationRepository(session)
    engine = get_evaluation_engine()

    # 1. Verify task ownership
    task = await task_repo.get_by_id_and_owner_or_raise(task_id, user.id)

    # 2. Find most recent completed run
    runs, _ = await run_repo.list_by_task(task_id, user.id, skip=0, limit=1)
    if not runs:
        raise NotFoundError(f"No execution runs found for task '{task_id}'.")

    latest_run = runs[0]
    if not latest_run.output_content:
        raise InvalidStateError("Latest run has no generated output content to evaluate.")

    # 3. Determine evaluation policy
    req = body or EvaluateTaskRequest()
    policy = EvaluationPolicy.from_mode(
        mode=req.mode or task.evaluation_mode or "standard",
        strict=req.strict if req.strict is not None else (task.strict_evaluation or False),
        max_revisions=req.max_revisions,
    )

    # Harvest context and sources from run
    context_items = latest_run.input_snapshot.get("context_items", []) if latest_run.input_snapshot else []
    retrieval_sources = latest_run.retrieval_sources or []
    web_sources = latest_run.input_snapshot.get("web_sources", []) if latest_run.input_snapshot else []
    expected_format = req.expected_format or task.expected_format

    # 4. Execute evaluation
    eval_result = await engine.evaluate(
        task=task,
        output_text=latest_run.output_content,
        context_items=context_items,
        retrieval_sources=retrieval_sources,
        web_sources=web_sources,
        expected_format=expected_format,
        policy=policy,
        attempt=1,
    )

    # 5. Persist EvaluationRun and EvaluationFinding records
    eval_run_db = await eval_repo.record_evaluation_result(
        run_id=latest_run.id,
        result=eval_result,
        evaluator_type="engine",
    )

    # 6. Update Run metadata
    latest_run.evaluation_status = eval_result.status.value
    latest_run.evaluation_mode = eval_result.mode.value
    latest_run.evaluation_duration_ms = eval_result.duration_ms
    latest_run.evaluation_attempts = (latest_run.evaluation_attempts or 0) + 1
    latest_run.evaluation_result = eval_result.model_dump(mode="json")
    session.add(latest_run)
    await session.commit()

    # Re-fetch evaluation run with findings loaded for response serialization
    eval_runs = await eval_repo.list_by_run(run_id=latest_run.id, owner_user_id=user.id)
    eval_run_response = eval_runs[-1] if eval_runs else eval_run_db

    return EvaluateTaskResponse(
        evaluation_run=EvaluationRunResponse.model_validate(eval_run_response),
        result=eval_result,
    )


@router.get(
    "/runs/{run_id}/evaluation",
    response_model=RunEvaluationHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get evaluation history for a run",
    description="Returns all evaluation runs and verification findings for a specific task run.",
)
async def get_run_evaluation_history(
    run_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> RunEvaluationHistoryResponse:
    eval_repo = EvaluationRepository(session)
    eval_runs = await eval_repo.list_by_run(run_id=run_id, owner_user_id=user.id)

    eval_responses = [EvaluationRunResponse.model_validate(er) for er in eval_runs]
    latest_status = eval_responses[-1].status if eval_responses else None
    latest_rec = eval_responses[-1].recommendation if eval_responses else None

    return RunEvaluationHistoryResponse(
        run_id=run_id,
        evaluation_runs=eval_responses,
        total_evaluations=len(eval_responses),
        latest_status=latest_status,
        latest_recommendation=latest_rec,
    )
