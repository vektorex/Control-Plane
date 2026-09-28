from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from backend.app.core.logging import logger
from backend.app.services.tools.base import BaseTool
from backend.app.services.tools.errors import ToolNotFoundError, ToolValidationError
from backend.app.services.tools.providers.web_search import WebSearchTool
from backend.app.services.tools.schemas import ToolMetadata


class ToolRegistry:
    """
    Centralized registry managing available tools and their metadata.
    Enables dynamic registration/unregistration of external integrations without modifying the core executor.
    """

    def __init__(self) -> None:
        self._tools: Dict[str, BaseTool] = {}
        # Register default tools
        self.register(WebSearchTool())

    def register(self, tool: BaseTool) -> None:
        """Registers a tool in the registry."""
        if not isinstance(tool, BaseTool):
            raise TypeError(f"Expected BaseTool instance, got {type(tool)}")
        self._tools[tool.name] = tool
        logger.info(f"[ToolRegistry] Registered tool '{tool.name}'")

    def unregister(self, tool_name: str) -> Optional[BaseTool]:
        """Removes a tool from the registry."""
        tool = self._tools.pop(tool_name, None)
        if tool:
            logger.info(f"[ToolRegistry] Unregistered tool '{tool_name}'")
        return tool

    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Retrieves a registered tool by identifier."""
        return self._tools.get(tool_name)

    def get(self, tool_name: str) -> Optional[BaseTool]:
        """Alias for get_tool."""
        return self._tools.get(tool_name)

    def has_tool(self, tool_name: str) -> bool:
        """Returns True if the tool identifier is registered in the registry."""
        return tool_name in self._tools

    def get_tool_or_raise(self, tool_name: str) -> BaseTool:
        """Retrieves a registered tool or raises ToolNotFoundError."""
        tool = self.get_tool(tool_name)
        if not tool:
            raise ToolNotFoundError(tool_name)
        return tool

    def list_tools(self) -> List[BaseTool]:
        """Returns all registered tool instances."""
        return list(self._tools.values())

    def list_tool_metadata(self) -> List[ToolMetadata]:
        """Returns metadata and JSON schemas for all registered tools."""
        return [
            ToolMetadata(
                name=tool.name,
                description=tool.description,
                input_schema=tool.get_input_json_schema(),
                requires_auth=tool.requires_auth,
                metadata=tool.metadata,
            )
            for tool in self._tools.values()
        ]

    def validate_input(self, tool_name: str, raw_input: Dict[str, Any]) -> BaseModel:
        """
        Validates raw input dictionary against tool's Pydantic input schema.
        Raises ToolValidationError on schema mismatch.
        """
        tool = self.get_tool_or_raise(tool_name)
        try:
            return tool.input_schema.model_validate(raw_input)
        except Exception as e:
            raise ToolValidationError(f"Input validation failed for '{tool_name}': {str(e)}")


# Default global tool registry instance
_default_tool_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Dependency injection factory for ToolRegistry."""
    global _default_tool_registry
    if _default_tool_registry is None:
        _default_tool_registry = ToolRegistry()
    return _default_tool_registry
