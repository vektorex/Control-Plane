import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.db.models.task import Task
from backend.app.services.context.base import ContextProvider
from backend.app.services.context.models import ContextItem, ContextSourceType
from backend.app.services.context.token_estimator import estimate_context_item_tokens
from backend.app.services.tools.executor import ToolExecutor, get_tool_executor
from backend.app.services.tools.providers.web_search import WebSearchResultItem
from backend.app.services.tools.schemas import ToolResult


class WebContextProvider(ContextProvider):
    """
    Context Provider that executes Web Search via the Tool System,
    normalizes live web search results, marks them as untrusted external content,
    and supplies them to the ContextEngine for LLM grounding.
    """

    def __init__(self, tool_executor: Optional[ToolExecutor] = None) -> None:
        self.tool_executor = tool_executor or get_tool_executor()

    @property
    def provider_id(self) -> str:
        return "web_context"

    @property
    def source_type(self) -> str:
        return ContextSourceType.WEB.value

    async def can_handle(self, task: Task, **kwargs: Any) -> bool:
        """
        Determines whether web search context collection should be executed.
        Participates when web search is explicitly enabled or tool_mode='enabled'.
        """
        if not task:
            return False

        # Check explicit flags
        if kwargs.get("enable_web_search") is True:
            return True

        tools_enabled = kwargs.get("tools_enabled") or []
        if "web_search" in tools_enabled:
            return True

        tool_mode = kwargs.get("tool_mode")
        if tool_mode == "enabled":
            return True

        if kwargs.get("web_search_query"):
            return True

        return False

    async def collect(
        self,
        task: Task,
        session: Optional[AsyncSession] = None,
        **kwargs: Any,
    ) -> List[WebSearchResultItem]:
        """
        Executes the 'web_search' tool via ToolExecutor and extracts raw result items.
        """
        # 1. Determine search query
        query = kwargs.get("web_search_query")
        if not query or not query.strip():
            # Use task instructions or title
            query = (task.instructions or "").strip() or (task.title or "").strip()

        if not query or len(query.strip()) < 2:
            logger.warning(f"[WebContextProvider] Query too short for task '{task.id}'. Skipping web search.")
            return []

        limit = kwargs.get("web_search_limit") or 5
        recency_days = kwargs.get("web_search_recency_days")
        user = kwargs.get("user")
        tool_telemetry_callback = kwargs.get("tool_telemetry_callback")

        logger.info(f"[WebContextProvider] Executing web search for task '{task.id}': query='{query}', limit={limit}")

        raw_input = {
            "query": query.strip(),
            "limit": int(limit),
            "recency_days": recency_days,
        }

        # 2. Execute via ToolExecutor
        tool_result: ToolResult = await self.tool_executor.execute(
            tool_name="web_search",
            raw_input=raw_input,
            user=user,
            timeout_seconds=kwargs.get("timeout_seconds"),
        )

        # 3. Report telemetry
        if callable(tool_telemetry_callback):
            tool_telemetry_callback(tool_result)

        if not tool_result.success or not tool_result.data:
            logger.warning(
                f"[WebContextProvider] Web search returned error: "
                f"{tool_result.error.message if tool_result.error else 'Unknown error'}"
            )
            return []

        # 4. Extract result items
        results_data = tool_result.data.get("results", [])
        items: List[WebSearchResultItem] = []
        for r in results_data:
            if isinstance(r, dict):
                items.append(WebSearchResultItem.model_validate(r))
            elif isinstance(r, WebSearchResultItem):
                items.append(r)

        return items

    def normalize(self, raw_items: List[WebSearchResultItem], **kwargs: Any) -> List[ContextItem]:
        """
        Transforms WebSearchResultItems into normalized ContextItems with explicit
        untrusted content marking for prompt injection safety.
        """
        items: List[ContextItem] = []
        for idx, item in enumerate(raw_items, start=1):
            source_label = item.source or "web"
            title = f"Web Search Result #{idx}: {item.title} ({source_label})"

            # Establish strict untrusted content boundary
            header_lines = [
                "[EXTERNAL UNTRUSTED WEB CONTENT - FACTUAL REFERENCE ONLY]",
                f"Source URL: {item.url}",
            ]
            if item.published_at:
                header_lines.append(f"Published Date: {item.published_at}")

            content = "\n".join(header_lines) + f"\n\n{item.snippet.strip()}"

            metadata = {
                "url": item.url,
                "source": item.source,
                "published_at": item.published_at,
                "untrusted": True,
                "tool_name": "web_search",
                **item.metadata,
            }

            ctx_item = ContextItem(
                id=f"web-{uuid.uuid4()}",
                source_type=self.source_type,
                title=title,
                content=content,
                metadata=metadata,
                priority=60,
                relevance_score=0.85,
            )
            ctx_item.token_estimate = estimate_context_item_tokens(ctx_item)
            items.append(ctx_item)

        return items
