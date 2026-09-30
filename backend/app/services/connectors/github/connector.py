"""
GitHub Connector implementation adhering to BaseConnector.
"""
from typing import Any, Dict, Optional
from backend.app.services.connectors.base import BaseConnector
from backend.app.services.connectors.errors import (
    ConnectorOperationNotFoundError,
    ConnectorValidationError,
)
from backend.app.services.connectors.github.client import GitHubClient
from backend.app.services.connectors.github.operations import GitHubOperations
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
from backend.app.services.connectors.schemas import (
    ConnectorCapability,
    ConnectorCategory,
    ConnectorOperationMetadata,
    ConnectorResult,
    PermissionLevel,
)


class GitHubConnector(BaseConnector):
    """
    Official GitHub connector providing read-only operations for repositories, issues,
    pull requests, file contents, and code search.
    """
    name = "github"
    display_name = "GitHub"
    description = "Repository and development data"
    category = ConnectorCategory.CODE.value
    version = "1.0.0"
    capabilities = [
        ConnectorCapability.READ.value,
        ConnectorCapability.SEARCH.value,
        ConnectorCapability.LIST.value,
    ]
    auth_type = "pat"

    supported_operations = [
        ConnectorOperationMetadata(
            name="get_repository",
            display_name="Get Repository",
            description="Retrieve details and metadata for a specific repository.",
            capability=ConnectorCapability.READ,
            permission_level=PermissionLevel.READ,
            parameters_schema=GetRepositoryArgs.model_json_schema(),
        ),
        ConnectorOperationMetadata(
            name="list_repositories",
            display_name="List Repositories",
            description="List repositories accessible to the authenticated user.",
            capability=ConnectorCapability.LIST,
            permission_level=PermissionLevel.READ,
            parameters_schema=ListRepositoriesArgs.model_json_schema(),
        ),
        ConnectorOperationMetadata(
            name="search_repositories",
            display_name="Search Repositories",
            description="Search repositories by query string with filters.",
            capability=ConnectorCapability.SEARCH,
            permission_level=PermissionLevel.READ,
            parameters_schema=SearchRepositoriesArgs.model_json_schema(),
        ),
        ConnectorOperationMetadata(
            name="get_issue",
            display_name="Get Issue",
            description="Retrieve details for a specific repository issue.",
            capability=ConnectorCapability.READ,
            permission_level=PermissionLevel.READ,
            parameters_schema=GetIssueArgs.model_json_schema(),
        ),
        ConnectorOperationMetadata(
            name="list_issues",
            display_name="List Issues",
            description="List issues in a repository with state filtering.",
            capability=ConnectorCapability.LIST,
            permission_level=PermissionLevel.READ,
            parameters_schema=ListIssuesArgs.model_json_schema(),
        ),
        ConnectorOperationMetadata(
            name="search_issues",
            display_name="Search Issues",
            description="Search issues across repositories using GitHub issue search query syntax.",
            capability=ConnectorCapability.SEARCH,
            permission_level=PermissionLevel.READ,
            parameters_schema=SearchIssuesArgs.model_json_schema(),
        ),
        ConnectorOperationMetadata(
            name="get_pull_request",
            display_name="Get Pull Request",
            description="Retrieve details for a specific pull request.",
            capability=ConnectorCapability.READ,
            permission_level=PermissionLevel.READ,
            parameters_schema=GetPullRequestArgs.model_json_schema(),
        ),
        ConnectorOperationMetadata(
            name="list_pull_requests",
            display_name="List Pull Requests",
            description="List pull requests in a repository.",
            capability=ConnectorCapability.LIST,
            permission_level=PermissionLevel.READ,
            parameters_schema=ListPullRequestsArgs.model_json_schema(),
        ),
        ConnectorOperationMetadata(
            name="get_file_contents",
            display_name="Get File Contents",
            description="Fetch file text contents or directory listing from a repository.",
            capability=ConnectorCapability.READ,
            permission_level=PermissionLevel.READ,
            parameters_schema=GetFileContentsArgs.model_json_schema(),
        ),
        ConnectorOperationMetadata(
            name="search_code",
            display_name="Search Code",
            description="Search code across repositories using GitHub code search syntax.",
            capability=ConnectorCapability.SEARCH,
            permission_level=PermissionLevel.READ,
            parameters_schema=SearchCodeArgs.model_json_schema(),
        ),
    ]

    async def test_connection(
        self,
        credentials: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Validates token validity against GitHub `/user` endpoint.
        Returns safe account info (never returns secret token).
        """
        client = GitHubClient(token=credentials)
        data = await client.get("/user")
        return {
            "login": data.get("login"),
            "name": data.get("name"),
            "html_url": data.get("html_url"),
            "avatar_url": data.get("avatar_url"),
            "public_repos": data.get("public_repos", 0),
            "total_private_repos": data.get("total_private_repos", 0),
            "company": data.get("company"),
        }

    async def execute_operation(
        self,
        operation: str,
        arguments: Dict[str, Any],
        credentials: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConnectorResult:
        """
        Validates input arguments and executes the requested GitHub operation.
        """
        client = GitHubClient(token=credentials)

        try:
            if operation == "get_repository":
                parsed = GetRepositoryArgs.model_validate(arguments)
                return await GitHubOperations.get_repository(client, parsed.model_dump())

            elif operation == "list_repositories":
                parsed = ListRepositoriesArgs.model_validate(arguments)
                return await GitHubOperations.list_repositories(client, parsed.model_dump())

            elif operation == "search_repositories":
                parsed = SearchRepositoriesArgs.model_validate(arguments)
                return await GitHubOperations.search_repositories(client, parsed.model_dump())

            elif operation == "get_issue":
                parsed = GetIssueArgs.model_validate(arguments)
                return await GitHubOperations.get_issue(client, parsed.model_dump())

            elif operation == "list_issues":
                parsed = ListIssuesArgs.model_validate(arguments)
                return await GitHubOperations.list_issues(client, parsed.model_dump())

            elif operation == "search_issues":
                parsed = SearchIssuesArgs.model_validate(arguments)
                return await GitHubOperations.search_issues(client, parsed.model_dump())

            elif operation == "get_pull_request":
                parsed = GetPullRequestArgs.model_validate(arguments)
                return await GitHubOperations.get_pull_request(client, parsed.model_dump())

            elif operation == "list_pull_requests":
                parsed = ListPullRequestsArgs.model_validate(arguments)
                return await GitHubOperations.list_pull_requests(client, parsed.model_dump())

            elif operation == "get_file_contents":
                parsed = GetFileContentsArgs.model_validate(arguments)
                return await GitHubOperations.get_file_contents(client, parsed.model_dump())

            elif operation == "search_code":
                parsed = SearchCodeArgs.model_validate(arguments)
                return await GitHubOperations.search_code(client, parsed.model_dump())

            else:
                raise ConnectorOperationNotFoundError(self.name, operation)

        except (ValueError, TypeError) as e:
            raise ConnectorValidationError(f"Invalid arguments for operation '{operation}': {str(e)}")
