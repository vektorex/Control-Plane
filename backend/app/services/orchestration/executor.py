import asyncio
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.core.logging import logger
from backend.app.db.models.task import Task
from backend.app.db.models.user import User
from backend.app.schemas.llm import ChatMessage, LLMGenerateRequest
from backend.app.services.context.builders.context_builder import ContextBuilder
from backend.app.services.context.engine import ContextEngine, get_context_engine
from backend.app.services.context.models import ContextBudget, ContextItem, ContextPackage
from backend.app.services.context.providers.web_context import WebContextProvider
from backend.app.services.llm.factory import LLMProviderFactory, get_llm_factory
from backend.app.services.orchestration.errors import (
    ExecutionLimitExceededError,
    OrchestrationTimeoutError,
    PlanExecutionAbortedError,
    StepExecutionError,
)
from backend.app.services.orchestration.plan import ExecutionPlan, ExecutionStepPlan, StepStatus, StepType
from backend.app.services.orchestration.policies import FailurePolicy
from backend.app.services.orchestration.state import ExecutionState, ExecutionStepRecord
from backend.app.services.tools.executor import ToolExecutor, get_tool_executor
from backend.app.services.tools.schemas import ToolResult


class OrchestrationExecutor:
    """
    Executes a validated ExecutionPlan sequentially, updating intermediate ExecutionState,
    orchestrating retrieval, tools, context merging, and final synthesis.
    """

    def __init__(
        self,
        context_engine: Optional[ContextEngine] = None,
        tool_executor: Optional[ToolExecutor] = None,
        llm_factory: Optional[LLMProviderFactory] = None,
    ) -> None:
        self.context_engine = context_engine or get_context_engine()
        self.tool_executor = tool_executor or ToolExecutor()
        self.llm_factory = llm_factory or get_llm_factory()
        self.web_context_provider = WebContextProvider(tool_executor=self.tool_executor)

    async def execute_single_step(
        self,
        step: ExecutionStepPlan,
        step_index: int,
        task: Task,
        state: ExecutionState,
        accumulated_context_items: List[ContextItem],
        retrieval_sources_meta: List[Dict[str, Any]],
        user: Optional[User] = None,
        session: Optional[AsyncSession] = None,
        policy: Optional[FailurePolicy] = None,
        on_step_start: Optional[Callable[[ExecutionStepRecord], Any]] = None,
        on_step_complete: Optional[Callable[[ExecutionStepRecord], Any]] = None,
        on_step_failed: Optional[Callable[[ExecutionStepRecord], Any]] = None,
    ) -> ExecutionStepRecord:
        """
        Executes a single step, updating step records and accumulated items.
        """
        active_policy = policy or FailurePolicy()
        tool_name = step.tool if step.type == StepType.TOOL else None
        strategy = step.strategy if step.type == StepType.RETRIEVE else None

        record = state.get_or_create_step_record(
            step_id=step.id,
            step_index=step_index,
            step_type=step.type.value if hasattr(step.type, "value") else str(step.type),
            tool_name=tool_name,
            retrieval_strategy=strategy,
        )
        record.mark_started()

        if callable(on_step_start):
            try:
                on_step_start(record)
            except Exception as cb_err:
                logger.warning(f"[OrchestrationExecutor] on_step_start callback error: {cb_err}")

        try:
            step_type_str = step.type.value if hasattr(step.type, "value") else str(step.type)

            if step_type_str == StepType.RETRIEVE.value:
                res_summary = await self._execute_retrieve_step(
                    step=step,
                    task=task,
                    session=session,
                    user=user,
                    accumulated_items=accumulated_context_items,
                    retrieval_sources=retrieval_sources_meta,
                    state=state,
                )
                record.mark_completed(res_summary)

            elif step_type_str == StepType.TOOL.value:
                res_summary = await self._execute_tool_step(
                    step=step,
                    user=user,
                    accumulated_items=accumulated_context_items,
                    state=state,
                )
                record.mark_completed(res_summary)

            elif step_type_str == StepType.CONTEXT.value:
                res_summary = await self._execute_context_step(
                    step=step,
                    task=task,
                    session=session,
                    accumulated_items=accumulated_context_items,
                    state=state,
                )
                record.mark_completed(res_summary)

            elif step_type_str == StepType.GENERATE.value:
                res_summary = await self._execute_generate_step(
                    step=step,
                    task=task,
                    accumulated_items=accumulated_context_items,
                    retrieval_sources=retrieval_sources_meta,
                    state=state,
                    session=session,
                )
                record.mark_completed(res_summary)

            else:
                raise StepExecutionError(f"Unhandled step type: {step_type_str}", step_id=step.id)

            if callable(on_step_complete):
                try:
                    on_step_complete(record)
                except Exception as cb_err:
                    logger.warning(f"[OrchestrationExecutor] on_step_complete callback error: {cb_err}")

            return record

        except Exception as step_err:
            err_msg = str(step_err)
            err_code = getattr(step_err, "code", "STEP_EXECUTION_ERROR")
            logger.error(f"[OrchestrationExecutor] Step '{step.id}' ({step.type}) failed: {err_msg}")

            record.mark_failed(error_code=err_code, error_message=err_msg)
            state.record_error(step.id, error_code=err_code, error_message=err_msg)

            if callable(on_step_failed):
                try:
                    on_step_failed(record)
                except Exception as cb_err:
                    logger.warning(f"[OrchestrationExecutor] on_step_failed callback error: {cb_err}")

            is_required = step.required or active_policy.strict_mode
            if step.type == StepType.RETRIEVE and active_policy.retrieval_required:
                is_required = True
            elif step.type == StepType.TOOL and step.tool == "web_search" and active_policy.web_search_required:
                is_required = True

            if is_required:
                state.complete()
                raise StepExecutionError(
                    f"Required plan step '{step.id}' failed: {err_msg}",
                    step_id=step.id,
                    details={"error_code": err_code, "error_message": err_msg},
                )
            else:
                logger.info(
                    f"[OrchestrationExecutor] Optional step '{step.id}' failed; continuing execution per policy."
                )
                return record

    async def execute(
        self,
        task: Task,
        plan: ExecutionPlan,
        user: Optional[User] = None,
        session: Optional[AsyncSession] = None,
        policy: Optional[FailurePolicy] = None,
        on_step_start: Optional[Callable[[ExecutionStepRecord], Any]] = None,
        on_step_complete: Optional[Callable[[ExecutionStepRecord], Any]] = None,
        on_step_failed: Optional[Callable[[ExecutionStepRecord], Any]] = None,
        state: Optional[ExecutionState] = None,
        accumulated_items: Optional[List[ContextItem]] = None,
        **kwargs: Any,
    ) -> ExecutionState:
        """
        Synchronously executes all steps in the plan from start to finish.
        """
        active_policy = policy or FailurePolicy()
        exec_state = state or ExecutionState(task_id=str(task.id), plan=plan)

        start_perf = time.perf_counter()
        timeout_seconds = settings.MAX_EXECUTION_TIME_SECONDS

        logger.info(f"[OrchestrationExecutor] Starting execution for task '{task.id}' with {len(plan.steps)} steps.")

        accumulated_context_items = accumulated_items if accumulated_items is not None else []
        retrieval_sources_meta: List[Dict[str, Any]] = []

        for idx, step in enumerate(plan.steps):
            exec_state.current_step_index = idx

            elapsed_seconds = time.perf_counter() - start_perf
            if elapsed_seconds > timeout_seconds:
                raise OrchestrationTimeoutError(
                    f"Execution exceeded maximum allowed timeout of {timeout_seconds}s (elapsed: {elapsed_seconds:.2f}s)."
                )

            await self.execute_single_step(
                step=step,
                step_index=idx,
                task=task,
                state=exec_state,
                accumulated_context_items=accumulated_context_items,
                retrieval_sources_meta=retrieval_sources_meta,
                user=user,
                session=session,
                policy=active_policy,
                on_step_start=on_step_start,
                on_step_complete=on_step_complete,
                on_step_failed=on_step_failed,
            )

        exec_state.complete()
        return exec_state

    async def _execute_retrieve_step(
        self,
        step: ExecutionStepPlan,
        task: Task,
        session: Optional[AsyncSession],
        user: Optional[User],
        accumulated_items: List[ContextItem],
        retrieval_sources: List[Dict[str, Any]],
        state: ExecutionState,
    ) -> Dict[str, Any]:
        """Executes retrieval step through RAGContextProvider / HybridRetriever."""
        rag_provider = self.context_engine.get_provider("rag_context")
        if not rag_provider:
            raise StepExecutionError("RAG context provider not registered in ContextEngine.", step_id=step.id)

        raw_items = await rag_provider.collect(
            task=task,
            session=session,
            user=user,
            retrieval_strategy=step.strategy or "hybrid",
            retrieval_scope=step.scope or "project",
            retrieval_top_k=step.top_k or 8,
            query=step.query or task.instructions,
            retrieval_enabled=True,
            retrieval_project_scope=(step.scope == "project"),
        )

        normalized = rag_provider.normalize(raw_items)
        accumulated_items.extend(normalized)
        state.retrieval_results.extend([it.model_dump() for it in normalized])

        for it in raw_items:
            retrieval_sources.append({
                "document_id": str(getattr(it, "document_id", "")),
                "chunk_id": str(getattr(it, "chunk_id", "")),
                "filename": getattr(it, "filename", "Unknown Document"),
                "page_number": getattr(it, "page_number", None),
                "score": round(getattr(it, "rerank_score", None) or getattr(it, "fusion_score", 0.0), 4),
            })
        state.metadata["retrieval_sources"] = retrieval_sources

        return {
            "strategy": step.strategy,
            "chunks_retrieved": len(normalized),
            "scope": step.scope,
        }

    async def _execute_tool_step(
        self,
        step: ExecutionStepPlan,
        user: Optional[User],
        accumulated_items: List[ContextItem],
        state: ExecutionState,
    ) -> Dict[str, Any]:
        """Executes tool step through ToolExecutor and normalizes results into ContextItems."""
        tool_name = step.tool
        raw_input = step.tool_input or {}

        tool_result: ToolResult = await self.tool_executor.execute(
            tool_name=tool_name,
            raw_input=raw_input,
            user=user,
        )

        state.tool_results.append(tool_result.model_dump())

        if not tool_result.success:
            err_msg = tool_result.error.message if tool_result.error else "Unknown tool execution failure."
            raise StepExecutionError(f"Tool '{tool_name}' failed: {err_msg}", step_id=step.id)

        # If tool is web_search, convert into untrusted ContextItems
        if tool_name == "web_search" and tool_result.data:
            from backend.app.services.tools.providers.web_search import WebSearchResultItem
            raw_list = tool_result.data.get("results", [])
            search_items = [WebSearchResultItem.model_validate(r) for r in raw_list]
            normalized = self.web_context_provider.normalize(search_items)
            accumulated_items.extend(normalized)

        return {
            "tool": tool_name,
            "success": tool_result.success,
            "latency_ms": tool_result.latency_ms,
            "result_count": len(tool_result.data.get("results", [])) if tool_result.data else 0,
        }

    async def _execute_context_step(
        self,
        step: ExecutionStepPlan,
        task: Task,
        session: Optional[AsyncSession],
        accumulated_items: List[ContextItem],
        state: ExecutionState,
    ) -> Dict[str, Any]:
        """Loads task & manual contexts."""
        task_provider = self.context_engine.get_provider("task_context")
        manual_provider = self.context_engine.get_provider("manual_context")

        count = 0
        if task_provider:
            t_items = await task_provider.collect(task, session=session)
            norm_t = task_provider.normalize(t_items)
            accumulated_items.extend(norm_t)
            count += len(norm_t)

        if manual_provider:
            m_items = await manual_provider.collect(task, session=session)
            norm_m = manual_provider.normalize(m_items)
            accumulated_items.extend(norm_m)
            count += len(norm_m)

        return {"context_items_loaded": count}

    async def _execute_generate_step(
        self,
        step: ExecutionStepPlan,
        task: Task,
        accumulated_items: List[ContextItem],
        retrieval_sources: List[Dict[str, Any]],
        state: ExecutionState,
        session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """Assembles context package, enforces budget, formats messages, and executes LLM generation."""
        has_task_ctx = any(it.source_type == "task" for it in accumulated_items)
        if not has_task_ctx:
            task_provider = self.context_engine.get_provider("task_context")
            if task_provider:
                t_items = await task_provider.collect(task, session=session)
                accumulated_items.extend(task_provider.normalize(t_items))

        has_manual_ctx = any(it.source_type == "manual" for it in accumulated_items)
        if not has_manual_ctx:
            manual_provider = self.context_engine.get_provider("manual_context")
            if manual_provider:
                m_items = await manual_provider.collect(task, session=session)
                accumulated_items.extend(manual_provider.normalize(m_items))

        max_context_tokens = step.metadata.get("max_context_tokens", 8000) if step.metadata else 8000
        budget = ContextBudget(max_context_tokens=max_context_tokens)
        context_package = self.context_engine.builder.build(
            raw_items=accumulated_items,
            budget=budget,
        )

        state.context_items = [it.model_dump() for it in context_package.items]
        state.metadata["context_package"] = {
            "estimated_tokens": context_package.estimated_tokens,
            "truncated": context_package.truncated,
            "total_items": context_package.total_items,
            "dropped_items_count": context_package.dropped_items_count,
            "sources": list(context_package.sources),
        }

        messages = self.context_engine.builder.format_as_messages(context_package, task)

        target_model = step.model or settings.OPENAI_DEFAULT_MODEL
        target_temp = step.temperature if step.temperature is not None else 0.2

        provider = self.llm_factory.get_provider_for_model(target_model)

        llm_request = LLMGenerateRequest(
            model=target_model,
            messages=messages,
            temperature=target_temp,
        )

        gen_resp = await provider.generate(llm_request)

        state.generated_output = gen_resp.content
        state.token_usage = {
            "input_tokens": getattr(gen_resp.usage, "input_tokens", None) or getattr(gen_resp.usage, "prompt_tokens", 0) if gen_resp.usage else 0,
            "output_tokens": getattr(gen_resp.usage, "output_tokens", None) or getattr(gen_resp.usage, "completion_tokens", 0) if gen_resp.usage else 0,
            "total_tokens": getattr(gen_resp.usage, "total_tokens", 0) if gen_resp.usage else 0,
        }

        return {
            "model": target_model,
            "tokens": state.token_usage,
            "output_length": len(gen_resp.content),
        }
