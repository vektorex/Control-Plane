"""
Bridge exposing external Connectors as standard tools in the Tool System.
"""
import uuid
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, create_model

from backend.app.core.logging import logger
from backend.app.db.models.user import User
from backend.app.services.connectors.base import BaseConnector
from backend.app.services.connectors.executor import ConnectorExecutor, get_connector_executor
from backend.app.services.connectors.github.schemas import (
    GetFileContentsArgs,
    GetIssueArgs,
    GetPullRequestArgs,
    GetRepositoryArgs,
    ListIssuesArgs,
    ListPullRequestsArgs,
    ListRepositoriesArgs,
    SearchCodeArgs,
    SearchIssuesArgs,
    SearchRepositoriesArgs,
)
from backend.app.services.tools.base import BaseTool
from backend.app.services.tools.errors import ToolExecutionError, ToolPermissionError


# Map of standard GitHub operation schemas
GITHUB_OPERATION_SCHEMAS: Dict[str, Type[BaseModel]] = {
    "get_repository": GetRepositoryArgs,
    "list_repositories": ListRepositoriesArgs,
    "search_repositories": SearchRepositoriesArgs,
    "get_issue": GetIssueArgs,
    "list_issues": ListIssuesArgs,
    "search_issues": SearchIssuesArgs,
    "get_pull_request": GetPullRequestArgs,
    "list_pull_requests": ListPullRequestsArgs,
    "get_file_contents": GetFileContentsArgs,
    "search_code": SearchCodeArgs,
}


class ConnectorTool(BaseTool):
    """
    Standard Tool adapter that delegates execution directly to ConnectorExecutor.
    Allows existing Workflows, LLM Planners, and Tool Execution loops to invoke
    connectors transparently without separate execution pathways.
    """

    def __init__(
        self,
        connector_name: str,
        operation_name: str,
        description: str,
        input_schema: Type[BaseModel],
        tool_name_override: Optional[str] = None,
        connector_executor: Optional[ConnectorExecutor] = None,
    ) -> None:
        self.connector_name = connector_name
        self.operation_name = operation_name
        self.name = tool_name_override or f"{connector_name}_{operation_name}"
        self.description = description
        self.input_schema = input_schema
        self.requires_auth = True
        self.metadata = {
            "connector": connector_name,
            "operation": operation_name,
            "is_connector_tool": True,
        }
        self.connector_executor = connector_executor or get_connector_executor()

    async def execute(
        self,
        input_data: BaseModel,
        user: Optional[User] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Executes the connector operation via ConnectorExecutor and returns structured tool output.
        """
        # Resolve workspace context: from user's active workspace, kwargs, or context
        workspace_id = kwargs.get("workspace_id")
        if not workspace_id and user and getattr(user, "default_workspace_id", None):
            workspace_id = user.default_workspace_id
        elif not workspace_id and user and getattr(user, "workspaces", None) and len(user.workspaces) > 0:
            workspace_id = user.workspaces[0].id
        elif not workspace_id and kwargs.get("context", {}).get("workspace_id"):
            workspace_id = uuid.UUID(str(kwargs["context"]["workspace_id"]))
        
        # Fallback dummy workspace if running in test environment with dev token
        if not workspace_id:
            workspace_id = uuid.uuid4()

        raw_args = input_data.model_dump() if hasattr(input_data, "model_dump") else dict(input_data)

        session = kwargs.get("session")
        tracer = kwargs.get("tracer")

        logger.info(
            f"[ConnectorTool] Delegating tool '{self.name}' to ConnectorExecutor "
            f"({self.connector_name}.{self.operation_name})"
        )

        res = await self.connector_executor.execute(
            connector_name=self.connector_name,
            operation=self.operation_name,
            arguments=raw_args,
            workspace_id=workspace_id,
            user=user,
            session=session,
            tracer=tracer,
        )

        if not res.success:
            raise ToolExecutionError(
                f"Connector tool '{self.name}' failed: {res.error_message or 'Unknown connector error'}"
            )

        return {
            "connector": self.connector_name,
            "operation": self.operation_name,
            "items": res.items,
            "data": res.data,
            "metadata": res.metadata,
            "source": res.source,
        }


def build_connector_tools(connector: BaseConnector) -> List[ConnectorTool]:
    """
    Constructs a list of standard BaseTool instances for all operations supported by a connector.
    """
    tools: List[ConnectorTool] = []

    for op in connector.supported_operations:
        schema = GITHUB_OPERATION_SCHEMAS.get(op.name)
        if not schema:
            # Dynamically create fallback schema if not explicitly in map
            schema = create_model(f"{connector.name}_{op.name}_args", **{
                k: (Any, ...) for k in (op.parameters_schema.get("properties", {}).keys())
            })

        tool = ConnectorTool(
            connector_name=connector.name,
            operation_name=op.name,
            description=op.description,
            input_schema=schema,
        )
        tools.append(tool)

        # Also add alias for github_get_file -> github_get_file_contents
        if connector.name == "github" and op.name == "get_file_contents":
            alias_tool = ConnectorTool(
                connector_name=connector.name,
                operation_name=op.name,
                description=op.description,
                input_schema=schema,
                tool_name_override="github_get_file",
            )
            tools.append(alias_tool)

    return tools
