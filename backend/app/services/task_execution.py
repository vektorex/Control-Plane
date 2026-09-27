import asyncio
import json
import time
from datetime import datetime, timezone
from typing import AsyncIterator, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.errors import InvalidStateError, AppError
from backend.app.core.logging import logger
from backend.app.db.models.enums import TaskStatus, RunStatus
from backend.app.db.models.run import Run
from backend.app.db.models.task import Task
from backend.app.db.models.user import User
from backend.app.repositories.task import TaskRepository
from backend.app.repositories.run import RunRepository
from backend.app.schemas.llm import ChatMessage, LLMGenerateRequest
from backend.app.schemas.run import RunResponse
from backend.app.schemas.task import TaskRunRequest
from backend.app.services.llm.factory import LLMProviderFactory


class TaskExecutionService:
    """
    Service responsible for turning a Task entity into an AI request,
    orchestrating provider invocation, and persisting execution runs with full telemetry.
    """

    def __init__(self, session: AsyncSession, factory: LLMProviderFactory):
        self.session = session
        self.factory = factory
        self.task_repo = TaskRepository(session)
        self.run_repo = RunRepository(session)

    def _build_llm_messages(self, task: Task) -> list[ChatMessage]:
        """Constructs system and user messages from Task attributes."""
        prompt = (task.instructions or "").strip()
        if not prompt:
            prompt = (task.description or "").strip()
        if not prompt:
            prompt = (task.title or "").strip()

        if not prompt:
            raise InvalidStateError("Task has no instructions, description, or title to execute.")

        if task.context_text and task.context_text.strip():
            prompt = f"{prompt}\n\n--- Context ---\n{task.context_text.strip()}"

        return [
            ChatMessage(
                role="system",
                content="You are an AI assistant helping the user complete a task accurately.",
            ),
            ChatMessage(role="user", content=prompt),
        ]

    async def execute_task(
        self,
        task_id: UUID,
        user: User,
        request: TaskRunRequest,
    ) -> Run:
        """
        Executes a task synchronously against the LLM abstraction and records the run outcome.
        """
        task = await self.task_repo.get_by_id_and_owner_or_raise(task_id, user.id)
        messages = self._build_llm_messages(task)

        model_name = request.model or "gpt-4o-mini"
        provider = self.factory.get_provider_for_model(model_name)

        # 1. Create Run in 'queued' status
        input_snapshot = {
            "model": model_name,
            "temperature": request.temperature,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }

        run = Run(
            task_id=task.id,
            status=RunStatus.QUEUED.value,
            model_provider=provider.provider_id,
            model_name=model_name,
            input_snapshot=input_snapshot,
        )
        self.session.add(run)
        await self.session.flush()
        await self.session.refresh(run)

        # 2. Transition Run to 'running'
        start_time = time.perf_counter()
        run.status = RunStatus.RUNNING.value
        run.started_at = datetime.now(timezone.utc)
        await self.session.flush()

        llm_request = LLMGenerateRequest(
            model=model_name,
            messages=messages,
            temperature=request.temperature,
        )

        try:
            logger.info(f"[TaskExecution] Invoking model '{model_name}' for task '{task.id}' (run '{run.id}')")
            response = await provider.generate(llm_request)
            latency_ms = int((time.perf_counter() - start_time) * 1000)

            # 3. Persist completed Run
            run.status = RunStatus.COMPLETED.value
            run.output_content = response.content
            run.latency_ms = latency_ms
            run.completed_at = datetime.now(timezone.utc)

            if response.usage:
                run.input_tokens = response.usage.input_tokens
                run.output_tokens = response.usage.output_tokens
                run.total_tokens = response.usage.total_tokens

            # Update task status to active if still draft
            if task.status == TaskStatus.DRAFT.value:
                task.status = TaskStatus.ACTIVE.value

            await self.session.commit()
            await self.session.refresh(run)
            return run

        except Exception as e:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(f"[TaskExecution] Execution failed for run '{run.id}': {str(e)}")

            run.status = RunStatus.FAILED.value
            run.error_message = str(e)
            run.latency_ms = latency_ms
            run.completed_at = datetime.now(timezone.utc)

            await self.session.commit()
            await self.session.refresh(run)
            raise

    async def execute_task_stream(
        self,
        task_id: UUID,
        user: User,
        request: TaskRunRequest,
    ) -> AsyncIterator[str]:
        """
        Executes a task with Server-Sent Events (SSE) streaming while persisting the Run.
        """
        task = await self.task_repo.get_by_id_and_owner_or_raise(task_id, user.id)
        messages = self._build_llm_messages(task)

        model_name = request.model or "gpt-4o-mini"
        provider = self.factory.get_provider_for_model(model_name)

        input_snapshot = {
            "model": model_name,
            "temperature": request.temperature,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }

        # 1. Initialize Run in 'running' status
        run = Run(
            task_id=task.id,
            status=RunStatus.RUNNING.value,
            model_provider=provider.provider_id,
            model_name=model_name,
            input_snapshot=input_snapshot,
            started_at=datetime.now(timezone.utc),
        )
        self.session.add(run)
        await self.session.flush()
        await self.session.refresh(run)

        # Notify frontend of run ID immediately
        yield f"data: {json.dumps({'type': 'run_start', 'run_id': str(run.id), 'status': run.status})}\n\n"

        llm_request = LLMGenerateRequest(
            model=model_name,
            messages=messages,
            temperature=request.temperature,
        )

        start_time = time.perf_counter()
        accumulated_chunks = []
        final_usage = None

        try:
            async for chunk in provider.generate_stream(llm_request):
                accumulated_chunks.append(chunk.content)
                if chunk.usage:
                    final_usage = chunk.usage

                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk.content, 'is_finished': chunk.is_finished})}\n\n"

            # Completed normally
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            full_content = "".join(accumulated_chunks)

            run.status = RunStatus.COMPLETED.value
            run.output_content = full_content
            run.latency_ms = latency_ms
            run.completed_at = datetime.now(timezone.utc)

            if final_usage:
                run.input_tokens = final_usage.input_tokens
                run.output_tokens = final_usage.output_tokens
                run.total_tokens = final_usage.total_tokens

            if task.status == TaskStatus.DRAFT.value:
                task.status = TaskStatus.ACTIVE.value

            await self.session.commit()
            await self.session.refresh(run)

            # Send final run payload
            final_payload = {
                "type": "run_completed",
                "run": RunResponse.model_validate(run).model_dump(mode="json"),
            }
            yield f"data: {json.dumps(final_payload)}\n\n"
            yield "data: [DONE]\n\n"

        except (asyncio.CancelledError, GeneratorExit):
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.warning(f"[TaskExecution] Stream cancelled by client for run '{run.id}'")
            run.status = RunStatus.CANCELLED.value
            run.output_content = "".join(accumulated_chunks) or None
            run.error_message = "Stream cancelled or interrupted by client"
            run.latency_ms = latency_ms
            run.completed_at = datetime.now(timezone.utc)
            await self.session.commit()
            raise

        except Exception as e:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(f"[TaskExecution] Stream error for run '{run.id}': {str(e)}")
            run.status = RunStatus.FAILED.value
            run.output_content = "".join(accumulated_chunks) or None
            run.error_message = str(e)
            run.latency_ms = latency_ms
            run.completed_at = datetime.now(timezone.utc)
            await self.session.commit()

            error_payload = {
                "type": "error",
                "error": {
                    "code": getattr(e, "code", "EXECUTION_ERROR"),
                    "message": str(e),
                },
            }
            yield f"data: {json.dumps(error_payload)}\n\n"
            yield "data: [DONE]\n\n"
