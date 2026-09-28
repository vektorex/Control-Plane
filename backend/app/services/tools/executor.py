import asyncio
import time
from typing import Any, Dict, Optional

from backend.app.core.logging import logger
from backend.app.db.models.user import User
from backend.app.services.tools.errors import (
    ToolError,
    ToolNotFoundError,
    ToolPermissionError,
    ToolTimeoutError,
    ToolValidationError,
)
from backend.app.services.tools.registry import ToolRegistry, get_tool_registry
from backend.app.services.tools.schemas import ToolErrorDetail, ToolResult


class ToolExecutor:
    """
    Core Tool Execution engine.
    Locates tools, enforces permissions, validates inputs, executes tools asynchronously,
    measures latency, and normalizes outputs into structured ToolResult payloads.
    """

    def __init__(self, registry: Optional[ToolRegistry] = None) -> None:
        self.registry = registry or get_tool_registry()

    async def execute(
        self,
        tool_name: str,
        raw_input: Dict[str, Any],
        user: Optional[User] = None,
        timeout_seconds: Optional[float] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> ToolResult:
        """
        Executes the named tool safely and returns a normalized ToolResult.
        Never throws raw unhandled exceptions to the caller.
        """
        start_time = time.perf_counter()

        # 1. Resolve Tool
        try:
            tool = self.registry.get_tool(tool_name)
            if not tool:
                raise ToolNotFoundError(tool_name)
        except ToolError as e:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.warning(f"[ToolExecutor] Tool lookup failed: {e.message}")
            return ToolResult(
                tool_name=tool_name,
                success=False,
                data=None,
                error=ToolErrorDetail(code=e.code, message=e.message),
                latency_ms=latency_ms,
            )

        # 2. Permission Check
        try:
            if not tool.check_permission(user=user, context=context):
                raise ToolPermissionError(f"User is not authorized to execute tool '{tool_name}'.")
        except ToolError as e:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.warning(f"[ToolExecutor] Tool permission rejected for '{tool_name}': {e.message}")
            return ToolResult(
                tool_name=tool_name,
                success=False,
                data=None,
                error=ToolErrorDetail(code=e.code, message=e.message),
                latency_ms=latency_ms,
            )

        # 3. Input Validation
        try:
            validated_input = self.registry.validate_input(tool_name, raw_input or {})
        except ToolError as e:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.warning(f"[ToolExecutor] Tool input validation failed for '{tool_name}': {e.message}")
            return ToolResult(
                tool_name=tool_name,
                success=False,
                data=None,
                error=ToolErrorDetail(code=e.code, message=e.message),
                latency_ms=latency_ms,
            )

        # 4. Tool Execution with Timeout
        try:
            effective_timeout = timeout_seconds or 30.0
            exec_coro = tool.execute(validated_input, user=user, **kwargs)
            result_data = await asyncio.wait_for(exec_coro, timeout=effective_timeout)

            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.info(f"[ToolExecutor] Tool '{tool_name}' completed successfully in {latency_ms}ms")

            return ToolResult(
                tool_name=tool_name,
                success=True,
                data=result_data,
                error=None,
                latency_ms=latency_ms,
            )

        except asyncio.TimeoutError:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(f"[ToolExecutor] Tool '{tool_name}' timed out after {effective_timeout}s")
            return ToolResult(
                tool_name=tool_name,
                success=False,
                data=None,
                error=ToolErrorDetail(code="TOOL_TIMEOUT", message=f"Tool '{tool_name}' execution timed out."),
                latency_ms=latency_ms,
            )
        except ToolError as e:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(f"[ToolExecutor] Tool '{tool_name}' execution error: {e.message}")
            return ToolResult(
                tool_name=tool_name,
                success=False,
                data=None,
                error=ToolErrorDetail(code=e.code, message=e.message),
                latency_ms=latency_ms,
            )
        except Exception as e:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(f"[ToolExecutor] Tool '{tool_name}' unexpected error: {str(e)}", exc_info=True)
            return ToolResult(
                tool_name=tool_name,
                success=False,
                data=None,
                error=ToolErrorDetail(code="TOOL_EXECUTION_ERROR", message=f"Tool execution failed: {str(e)}"),
                latency_ms=latency_ms,
            )


# Default global tool executor instance
_default_tool_executor: Optional[ToolExecutor] = None


def get_tool_executor() -> ToolExecutor:
    """Dependency injection factory for ToolExecutor."""
    global _default_tool_executor
    if _default_tool_executor is None:
        _default_tool_executor = ToolExecutor()
    return _default_tool_executor
