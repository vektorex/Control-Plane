import re
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.db.models.task import Task
from backend.app.db.models.user import User
from backend.app.schemas.task import TaskRunRequest
from backend.app.services.orchestration.plan import ExecutionPlan, ExecutionStepPlan, StepType
from backend.app.services.retrieval.router import RetrievalRouter, get_retrieval_router
from backend.app.services.tools.registry import ToolRegistry, get_tool_registry


class ExecutionPlanner:
    """
    Deterministic Execution Planner that synthesizes an ExecutionPlan
    by evaluating task directives, intelligent retrieval routing, available context, and tool configurations.
    """

    # Patterns indicating high likelihood of current/live web information need
    WEB_SEARCH_INDICATORS = [
        r"\b(?:latest|recent|current|today|news|release|released|changelog|updates?)\b",
        r"\b(?:search\s+(?:the\s+)?web|look\s+up|google|online)\b",
        r"\b(?:2024|2025|2026)\b",
    ]

    def __init__(
        self,
        retrieval_router: Optional[RetrievalRouter] = None,
        tool_registry: Optional[ToolRegistry] = None,
    ) -> None:
        self.retrieval_router = retrieval_router or get_retrieval_router()
        self.tool_registry = tool_registry or get_tool_registry()

    def _detect_web_need(self, text: str) -> bool:
        """Heuristic check for live web search need when tool_mode is auto."""
        if not text:
            return False
        clean = text.lower()
        return any(re.search(pat, clean, re.IGNORECASE) for pat in self.WEB_SEARCH_INDICATORS)

    async def plan(
        self,
        task: Task,
        request: Optional[TaskRunRequest] = None,
        user: Optional[User] = None,
        session: Optional[AsyncSession] = None,
        **kwargs: Any,
    ) -> ExecutionPlan:
        """
        Generates a deterministic ExecutionPlan for the specified task.
        """
        req = request or TaskRunRequest()
        steps: List[ExecutionStepPlan] = []
        step_counter = 1

        prompt_text = (task.instructions or "").strip() or (task.description or "").strip() or (task.title or "").strip()

        # 1. Evaluate Knowledge Retrieval via RetrievalRouter
        retrieval_decision = await self.retrieval_router.decide(
            task=task,
            session=session,
            user=user,
            retrieval_mode=req.retrieval_mode,
            strategy_override=req.retrieval_strategy,
            scope_override=req.retrieval_scope,
            top_k_override=req.retrieval_top_k,
            query=req.query,
            retrieval_enabled=req.retrieval_enabled,
            retrieval_project_scope=req.retrieval_project_scope,
        )

        plan_reasons = []

        if retrieval_decision.retrieval_required and retrieval_decision.strategy.value != "none":
            steps.append(
                ExecutionStepPlan(
                    id=f"step_{step_counter}",
                    type=StepType.RETRIEVE,
                    description=f"Retrieve knowledge via {retrieval_decision.strategy.value} search ({retrieval_decision.scope.value} scope)",
                    strategy=retrieval_decision.strategy.value,
                    scope=retrieval_decision.scope.value,
                    top_k=retrieval_decision.top_k or settings.RAG_DEFAULT_TOP_K,
                    query=retrieval_decision.query or prompt_text,
                    required=req.retrieval_mode == "always",
                    metadata={
                        "confidence": retrieval_decision.confidence,
                        "reason": retrieval_decision.reason,
                    },
                )
            )
            step_counter += 1
            plan_reasons.append(f"Knowledge Retrieval ({retrieval_decision.strategy.value})")

        # 2. Evaluate External Tool Usage (Web Search)
        tool_mode = req.tool_mode or "auto"
        tools_enabled = req.tools_enabled or []
        explicitly_requested = req.enable_web_search is True or "web_search" in tools_enabled

        should_include_web_search = False
        if explicitly_requested:
            should_include_web_search = True
        elif tool_mode in ("auto", "enabled"):
            if tool_mode == "enabled" or self._detect_web_need(prompt_text):
                should_include_web_search = True

        if should_include_web_search:
            web_query = (req.web_search_query or "").strip() or prompt_text
            web_limit = req.web_search_limit or settings.WEB_SEARCH_DEFAULT_LIMIT

            steps.append(
                ExecutionStepPlan(
                    id=f"step_{step_counter}",
                    type=StepType.TOOL,
                    description="Query live web search for external grounding",
                    tool="web_search",
                    tool_input={
                        "query": web_query,
                        "limit": web_limit,
                        "recency_days": req.web_search_recency_days,
                    },
                    required=False,  # Default optional failure policy
                    metadata={
                        "limit": web_limit,
                        "recency_days": req.web_search_recency_days,
                    },
                )
            )
            step_counter += 1
            plan_reasons.append("Web Search Grounding")

        # 3. Final Step: Response Generation via LLM
        target_model = req.model or settings.OPENAI_DEFAULT_MODEL
        target_temp = req.temperature if req.temperature is not None else 0.2

        steps.append(
            ExecutionStepPlan(
                id=f"step_{step_counter}",
                type=StepType.GENERATE,
                description=f"Synthesize final response via {target_model}",
                model=target_model,
                temperature=target_temp,
                required=True,
                metadata={
                    "max_context_tokens": req.max_context_tokens or 8000,
                },
            )
        )
        plan_reasons.append(f"LLM Generation ({target_model})")

        plan_summary_reason = " -> ".join(plan_reasons) if plan_reasons else "Direct LLM Generation"

        return ExecutionPlan(
            task_id=str(task.id),
            steps=steps,
            plan_reason=plan_summary_reason,
            estimated_steps=len(steps),
            metadata={
                "retrieval_decision": retrieval_decision.model_dump(),
                "tool_mode": tool_mode,
            },
        )
