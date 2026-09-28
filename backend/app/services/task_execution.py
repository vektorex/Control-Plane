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
from backend.app.services.context.engine import ContextEngine, get_context_engine
from backend.app.services.llm.factory import LLMProviderFactory


class TaskExecutionService:
    """
    Service responsible for turning a Task entity into an AI request via the Context Engine,
    orchestrating provider invocation, and persisting execution runs with full context telemetry.
    """

    def __init__(
        self,
        session: AsyncSession,
        factory: LLMProviderFactory,
        context_engine: Optional[ContextEngine] = None,
    ):
        self.session = session
        self.factory = factory
        self.context_engine = context_engine or get_context_engine()
        self.task_repo = TaskRepository(session)
        self.run_repo = RunRepository(session)

    async def execute_task(
        self,
        task_id: UUID,
        user: User,
        request: TaskRunRequest,
    ) -> Run:
        """
        Executes a task synchronously against the LLM abstraction and records the run outcome.
        Context is gathered, normalized, and budget-enforced by the ContextEngine.
        """
        task = await self.task_repo.get_by_id_and_owner_or_raise(task_id, user.id)

        prompt_check = (task.instructions or "").strip() or (task.description or "").strip() or (task.title or "").strip()
        if not prompt_check:
            raise InvalidStateError("Task has no instructions, description, or title to execute.")

        # 1. Gather & package context via ContextEngine
        max_context_tokens = request.max_context_tokens or 8000
        retrieval_telemetry = {}

        def _on_retrieval_telemetry(result):
            retrieval_telemetry["result"] = result

        context_package = await self.context_engine.build_context(
            task=task,
            session=self.session,
            max_context_tokens=max_context_tokens,
            retrieval_enabled=request.retrieval_enabled,
            retrieval_top_k=request.retrieval_top_k,
            retrieval_project_scope=request.retrieval_project_scope,
            retrieval_telemetry_callback=_on_retrieval_telemetry,
        )

        ret_res = retrieval_telemetry.get("result")
        ret_sources = None
        ret_chunk_count = 0
        ret_latency = 0
        if ret_res:
            ret_chunk_count = len(ret_res.candidates)
            ret_latency = ret_res.retrieval_latency_ms
            ret_sources = [
                {
                    "document_id": str(c.document_id),
                    "chunk_id": str(c.chunk_id),
                    "filename": c.filename,
                    "page_number": c.page_number,
                    "score": round(c.rerank_score or c.fusion_score, 4),
                    "vector_score": round(c.vector_score, 4) if c.vector_score is not None else None,
                    "keyword_score": round(c.keyword_score, 4) if c.keyword_score is not None else None,
                }
                for c in ret_res.candidates
            ]

        # 2. Build structured messages from context package
        messages = self.context_engine.builder.format_as_messages(context_package, task)

        model_name = request.model or "gpt-4o-mini"
        provider = self.factory.get_provider_for_model(model_name)

        # 3. Create Run in 'queued' status with full context and retrieval telemetry
        input_snapshot = {
            "model": model_name,
            "temperature": request.temperature,
            "max_context_tokens": max_context_tokens,
            "retrieval_enabled": bool(request.retrieval_enabled),
            "context_summary": {
                "item_count": context_package.total_items,
                "estimated_tokens": context_package.estimated_tokens,
                "sources": context_package.sources,
                "truncated": context_package.truncated,
                "dropped_items": context_package.dropped_items_count,
            },
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }

        run = Run(
            task_id=task.id,
            status=RunStatus.QUEUED.value,
            model_provider=provider.provider_id,
            model_name=model_name,
            input_snapshot=input_snapshot,
            context_item_count=context_package.total_items,
            estimated_context_tokens=context_package.estimated_tokens,
            context_truncated=context_package.truncated,
            context_sources=context_package.sources,
            retrieval_enabled=bool(request.retrieval_enabled),
            retrieved_chunk_count=ret_chunk_count if request.retrieval_enabled else None,
            retrieval_latency_ms=ret_latency if request.retrieval_enabled else None,
            retrieval_sources=ret_sources if request.retrieval_enabled else None,
        )
        self.session.add(run)
        await self.session.flush()
        await self.session.refresh(run)

        # 4. Transition Run to 'running'
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
            logger.info(
                f"[TaskExecution] Invoking model '{model_name}' for task '{task.id}' "
                f"(run '{run.id}', context_items={context_package.total_items}, "
                f"context_tokens={context_package.estimated_tokens})"
            )
            response = await provider.generate(llm_request)
            latency_ms = int((time.perf_counter() - start_time) * 1000)

            # 5. Persist completed Run
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
        Context is gathered, normalized, and budget-enforced by the ContextEngine.
        """
        task = await self.task_repo.get_by_id_and_owner_or_raise(task_id, user.id)

        prompt_check = (task.instructions or "").strip() or (task.description or "").strip() or (task.title or "").strip()
        if not prompt_check:
            raise InvalidStateError("Task has no instructions, description, or title to execute.")

        # 1. Gather & package context via ContextEngine
        max_context_tokens = request.max_context_tokens or 8000
        retrieval_telemetry = {}

        def _on_retrieval_telemetry(result):
            retrieval_telemetry["result"] = result

        context_package = await self.context_engine.build_context(
            task=task,
            session=self.session,
            max_context_tokens=max_context_tokens,
            retrieval_enabled=request.retrieval_enabled,
            retrieval_top_k=request.retrieval_top_k,
            retrieval_project_scope=request.retrieval_project_scope,
            retrieval_telemetry_callback=_on_retrieval_telemetry,
        )

        ret_res = retrieval_telemetry.get("result")
        ret_sources = None
        ret_chunk_count = 0
        ret_latency = 0
        if ret_res:
            ret_chunk_count = len(ret_res.candidates)
            ret_latency = ret_res.retrieval_latency_ms
            ret_sources = [
                {
                    "document_id": str(c.document_id),
                    "chunk_id": str(c.chunk_id),
                    "filename": c.filename,
                    "page_number": c.page_number,
                    "score": round(c.rerank_score or c.fusion_score, 4),
                    "vector_score": round(c.vector_score, 4) if c.vector_score is not None else None,
                    "keyword_score": round(c.keyword_score, 4) if c.keyword_score is not None else None,
                }
                for c in ret_res.candidates
            ]

        # 2. Build structured messages from context package
        messages = self.context_engine.builder.format_as_messages(context_package, task)

        model_name = request.model or "gpt-4o-mini"
        provider = self.factory.get_provider_for_model(model_name)

        input_snapshot = {
            "model": model_name,
            "temperature": request.temperature,
            "max_context_tokens": max_context_tokens,
            "retrieval_enabled": bool(request.retrieval_enabled),
            "context_summary": {
                "item_count": context_package.total_items,
                "estimated_tokens": context_package.estimated_tokens,
                "sources": context_package.sources,
                "truncated": context_package.truncated,
                "dropped_items": context_package.dropped_items_count,
            },
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }

        # 3. Initialize Run in 'running' status with context and retrieval telemetry
        run = Run(
            task_id=task.id,
            status=RunStatus.RUNNING.value,
            model_provider=provider.provider_id,
            model_name=model_name,
            input_snapshot=input_snapshot,
            context_item_count=context_package.total_items,
            estimated_context_tokens=context_package.estimated_tokens,
            context_truncated=context_package.truncated,
            context_sources=context_package.sources,
            retrieval_enabled=bool(request.retrieval_enabled),
            retrieved_chunk_count=ret_chunk_count if request.retrieval_enabled else None,
            retrieval_latency_ms=ret_latency if request.retrieval_enabled else None,
            retrieval_sources=ret_sources if request.retrieval_enabled else None,
            started_at=datetime.now(timezone.utc),
        )
        self.session.add(run)
        await self.session.flush()
        await self.session.refresh(run)

        # Notify frontend of run ID and context telemetry immediately
        yield f"data: {json.dumps({'type': 'run_start', 'run_id': str(run.id), 'status': run.status, 'context_item_count': context_package.total_items, 'estimated_context_tokens': context_package.estimated_tokens, 'context_truncated': context_package.truncated, 'retrieval_enabled': bool(request.retrieval_enabled), 'retrieved_chunk_count': ret_chunk_count})}\n\n"

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
