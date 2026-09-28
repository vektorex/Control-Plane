from typing import Any, Optional
from backend.app.core.errors import AppError


class ToolError(AppError):
    """Base exception for all tool system errors."""
    code: str = "TOOL_ERROR"
    status_code: int = 400

    def __init__(
        self,
        message: str,
        details: Optional[Any] = None,
        status_code: Optional[int] = None,
        code: Optional[str] = None,
    ):
        super().__init__(message=message, details=details, status_code=status_code)
        if code is not None:
            self.code = code


class ToolNotFoundError(ToolError):
    """Raised when an unregistered tool is requested."""
    code: str = "TOOL_NOT_FOUND"
    status_code: int = 404

    def __init__(self, tool_name: str):
        super().__init__(
            message=f"Tool '{tool_name}' was not found in the registry.",
            status_code=404,
            code="TOOL_NOT_FOUND",
        )


class ToolValidationError(ToolError):
    """Raised when tool inputs fail Pydantic or schema validation."""
    code: str = "TOOL_VALIDATION_ERROR"
    status_code: int = 422

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            details=details,
            status_code=422,
            code="TOOL_VALIDATION_ERROR",
        )


class ToolPermissionError(ToolError):
    """Raised when user or execution context lacks authorization to execute tool."""
    code: str = "TOOL_PERMISSION_DENIED"
    status_code: int = 403

    def __init__(self, message: str = "Permission denied for tool execution."):
        super().__init__(
            message=message,
            status_code=403,
            code="TOOL_PERMISSION_DENIED",
        )


class ToolExecutionError(ToolError):
    """Raised when a tool encounters an internal runtime or external API failure."""
    code: str = "TOOL_EXECUTION_ERROR"
    status_code: int = 500

    def __init__(self, message: str, original_error: Optional[str] = None):
        super().__init__(
            message=message,
            details={"original_error": original_error} if original_error else None,
            status_code=500,
            code="TOOL_EXECUTION_ERROR",
        )


class ToolTimeoutError(ToolError):
    """Raised when tool execution exceeds the configured timeout threshold."""
    code: str = "TOOL_TIMEOUT"
    status_code: int = 504

    def __init__(self, message: str = "Tool execution timed out."):
        super().__init__(
            message=message,
            status_code=504,
            code="TOOL_TIMEOUT",
        )

