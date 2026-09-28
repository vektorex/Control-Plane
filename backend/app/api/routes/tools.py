from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.auth import get_current_user
from backend.app.db.database import get_db
from backend.app.db.models.user import User
from backend.app.services.tools.executor import ToolExecutor, get_tool_executor
from backend.app.services.tools.registry import ToolRegistry, get_tool_registry
from backend.app.services.tools.schemas import (
    ToolExecutionRequest,
    ToolListResponse,
    ToolResult,
)

router = APIRouter(prefix="/tools", tags=["Tools"])


@router.get("", response_model=ToolListResponse)
async def list_available_tools(
    user: User = Depends(get_current_user),
    registry: ToolRegistry = Depends(get_tool_registry),
) -> ToolListResponse:
    """
    List all registered tools, their descriptions, authorization requirements,
    and JSON Schema parameter specifications for the authenticated user.
    """
    metadata_list = registry.list_tool_metadata()
    return ToolListResponse(
        tools=metadata_list,
        total=len(metadata_list),
    )


@router.post("/{tool_name}/execute", response_model=ToolResult)
async def execute_tool(
    tool_name: str,
    request: Optional[ToolExecutionRequest] = None,
    user: User = Depends(get_current_user),
    executor: ToolExecutor = Depends(get_tool_executor),
) -> ToolResult:
    """
    Development/testing endpoint to directly execute a registered tool.
    Enforces authentication, permission validation, schema validation,
    and returns a normalized ToolResult without exposing internal exceptions.
    """
    req_input = request.input if request else {}
    result = await executor.execute(
        tool_name=tool_name,
        raw_input=req_input,
        user=user,
    )
    return result
