"""
Connector Context Provider for integrating external connector results into the ContextEngine.
"""
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.db.models.task import Task
from backend.app.services.connectors.sanitization import format_untrusted_context_block
from backend.app.services.connectors.schemas import ConnectorResult
from backend.app.services.context.base import ContextProvider
from backend.app.services.context.models import ContextItem, ContextSourceType
from backend.app.services.context.token_estimator import estimate_context_item_tokens


class ConnectorContextProvider(ContextProvider):
    """
    Context Provider that gathers, normalizes, and injects external connector items
    into the Context Engine with explicit untrusted prompt boundaries.
    """

    def __init__(self, connector_executor: Optional[Any] = None) -> None:
        self._connector_executor = connector_executor

    @property
    def connector_executor(self) -> Any:
        if self._connector_executor is None:
            from backend.app.services.connectors.executor import get_connector_executor
            self._connector_executor = get_connector_executor()
        return self._connector_executor

    @property
    def provider_id(self) -> str:
        return "connector_context"


    @property
    def source_type(self) -> str:
        return ContextSourceType.CONNECTOR.value

    async def can_handle(self, task: Task, **kwargs: Any) -> bool:
        """
        Determines whether connector context should participate in context assembly.
        """
        if not task:
            return False

        if kwargs.get("connector_name") and kwargs.get("connector_operation"):
            return True

        if kwargs.get("connector_results") is not None:
            return True

        return False

    async def collect(
        self,
        task: Task,
        session: Optional[AsyncSession] = None,
        **kwargs: Any,
    ) -> List[ConnectorResult]:
        """
        Gathers connector results either by executing the requested connector operation
        or by collecting pre-executed connector results from kwargs.
        """
        # Pre-executed connector results passed directly
        if "connector_results" in kwargs:
            raw = kwargs["connector_results"]
            if isinstance(raw, list):
                return [r if isinstance(r, ConnectorResult) else ConnectorResult.model_validate(r) for r in raw]
            elif isinstance(raw, (dict, ConnectorResult)):
                res = raw if isinstance(raw, ConnectorResult) else ConnectorResult.model_validate(raw)
                return [res]

        connector_name = kwargs.get("connector_name")
        operation = kwargs.get("connector_operation")
        arguments = kwargs.get("connector_arguments", {})
        workspace_id = kwargs.get("workspace_id") or getattr(task, "workspace_id", None)
        user = kwargs.get("user")

        if not connector_name or not operation or not workspace_id:
            return []

        logger.info(f"[ConnectorContextProvider] Executing '{connector_name}.{operation}' for task '{task.id}'")

        result = await self.connector_executor.execute(
            connector_name=connector_name,
            operation=operation,
            arguments=arguments,
            workspace_id=workspace_id,
            user=user,
            session=session,
        )

        if not result.success:
            logger.warning(f"[ConnectorContextProvider] Connector operation failed: {result.error_message}")
            return []

        return [result]

    def normalize(self, raw_items: List[ConnectorResult], **kwargs: Any) -> List[ContextItem]:
        """
        Transforms ConnectorResult objects and their nested items into normalized ContextItems
        with explicit untrusted data markers for prompt injection protection.
        """
        items: List[ContextItem] = []

        for res in raw_items:
            conn_name = res.connector or "connector"
            op = res.operation or "query"

            # Case 1: Result has individual items
            if res.items:
                for idx, item in enumerate(res.items, start=1):
                    item_title = (
                        item.get("title")
                        or item.get("name")
                        or item.get("full_name")
                        or f"{conn_name} Item #{idx}"
                    )
                    
                    # Formulate body text
                    body_parts = []
                    if item.get("description"):
                        body_parts.append(f"Description: {item['description']}")
                    if item.get("body"):
                        body_parts.append(f"Content:\n{item['body']}")
                    if item.get("content"):
                        body_parts.append(f"Content:\n{item['content']}")
                    if item.get("html_url"):
                        body_parts.append(f"URL: {item['html_url']}")

                    raw_body = "\n\n".join(body_parts) if body_parts else str(item)
                    source_url = item.get("html_url") or res.source or ""

                    bounded_content = format_untrusted_context_block(
                        connector_name=conn_name,
                        operation=op,
                        title=item_title,
                        content=raw_body,
                        source_url=source_url,
                    )

                    metadata = {
                        "source_type": "connector",
                        "source_name": conn_name,
                        "trust_level": "external_untrusted",
                        "operation": op,
                        "source_url": source_url,
                        **{k: v for k, v in item.items() if k not in ("body", "content") and isinstance(v, (str, int, float, bool))},
                    }

                    ctx_item = ContextItem(
                        id=f"conn-{uuid.uuid4()}",
                        source_type=self.source_type,
                        title=f"[{conn_name.upper()}] {item_title}",
                        content=bounded_content,
                        metadata=metadata,
                        priority=65,
                        relevance_score=0.85,
                    )
                    ctx_item.token_estimate = estimate_context_item_tokens(ctx_item)
                    items.append(ctx_item)

            # Case 2: Result has data dict but no items list
            elif res.data:
                data = res.data
                title = data.get("title") or data.get("name") or f"[{conn_name.upper()}] {op} Data"
                raw_body = data.get("content") or data.get("body") or str(data)
                source_url = data.get("html_url") or res.source or ""

                bounded_content = format_untrusted_context_block(
                    connector_name=conn_name,
                    operation=op,
                    title=title,
                    content=raw_body,
                    source_url=source_url,
                )

                metadata = {
                    "source_type": "connector",
                    "source_name": conn_name,
                    "trust_level": "external_untrusted",
                    "operation": op,
                    "source_url": source_url,
                }

                ctx_item = ContextItem(
                    id=f"conn-{uuid.uuid4()}",
                    source_type=self.source_type,
                    title=title,
                    content=bounded_content,
                    metadata=metadata,
                    priority=65,
                    relevance_score=0.85,
                )
                ctx_item.token_estimate = estimate_context_item_tokens(ctx_item)
                items.append(ctx_item)

        return items
