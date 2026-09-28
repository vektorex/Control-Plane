from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ToolMetadata(BaseModel):
    """
    Public metadata and parameter schema for a registered tool.
    """
    name: str = Field(..., description="Unique tool identifier")
    description: str = Field(..., description="Description of tool functionality and capabilities")
    input_schema: Dict[str, Any] = Field(..., description="JSON Schema definition for tool inputs")
    requires_auth: bool = Field(default=True, description="Whether authentication is mandatory")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional tool categorization metadata")


class ToolErrorDetail(BaseModel):
    """
    Normalized error payload for failed tool executions.
    """
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-interpretable error description")


class ToolResult(BaseModel):
    """
    Normalized result format returned by ToolExecutor for all tool executions.
    Guarantees consistent structure whether execution succeeded or failed.
    """
    tool_name: str = Field(..., description="Name of the executed tool")
    success: bool = Field(..., description="Whether tool completed successfully")
    data: Optional[Any] = Field(default=None, description="Tool-specific structured output data")
    error: Optional[ToolErrorDetail] = Field(default=None, description="Error detail if execution failed")
    latency_ms: int = Field(default=0, ge=0, description="Execution duration in milliseconds")


class ToolExecutionRequest(BaseModel):
    """
    Payload sent to POST /api/tools/{tool_name}/execute for direct testing/execution.
    """
    input: Dict[str, Any] = Field(default_factory=dict, description="Tool input arguments")


class ToolListResponse(BaseModel):
    """
    Response returned by GET /api/tools.
    """
    tools: List[ToolMetadata] = Field(default_factory=list, description="List of registered tools")
    total: int = Field(default=0, description="Total count of available tools")
