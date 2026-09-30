"""
Implementation of 10 Read-Only GitHub Connector Operations.
"""
import base64
from typing import Any, Dict, List, Optional
from backend.app.services.connectors.github.client import GitHubClient
from backend.app.services.connectors.schemas import ConnectorResult


def _extract_repo_summary(r: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": r.get("id"),
        "name": r.get("name"),
        "full_name": r.get("full_name"),
        "owner": r.get("owner", {}).get("login") if isinstance(r.get("owner"), dict) else None,
        "description": r.get("description"),
        "html_url": r.get("html_url"),
        "stars": r.get("stargazers_count", 0),
        "forks": r.get("forks_count", 0),
        "language": r.get("language"),
        "is_private": r.get("private", False),
        "default_branch": r.get("default_branch", "main"),
        "updated_at": r.get("updated_at"),
        "created_at": r.get("created_at"),
    }


def _extract_issue_summary(iss: Dict[str, Any]) -> Dict[str, Any]:
    user_login = iss.get("user", {}).get("login") if isinstance(iss.get("user"), dict) else None
    labels = [lbl.get("name") for lbl in iss.get("labels", []) if isinstance(lbl, dict)]
    is_pr = "pull_request" in iss
    return {
        "id": iss.get("id"),
        "number": iss.get("number"),
        "title": iss.get("title"),
        "state": iss.get("state"),
        "user": user_login,
        "labels": labels,
        "body": iss.get("body"),
        "html_url": iss.get("html_url"),
        "comments": iss.get("comments", 0),
        "is_pull_request": is_pr,
        "created_at": iss.get("created_at"),
        "updated_at": iss.get("updated_at"),
        "closed_at": iss.get("closed_at"),
    }


def _extract_pr_summary(pr: Dict[str, Any]) -> Dict[str, Any]:
    user_login = pr.get("user", {}).get("login") if isinstance(pr.get("user"), dict) else None
    head_ref = pr.get("head", {}).get("ref") if isinstance(pr.get("head"), dict) else None
    base_ref = pr.get("base", {}).get("ref") if isinstance(pr.get("base"), dict) else None
    return {
        "id": pr.get("id"),
        "number": pr.get("number"),
        "title": pr.get("title"),
        "state": pr.get("state"),
        "user": user_login,
        "body": pr.get("body"),
        "html_url": pr.get("html_url"),
        "head_branch": head_ref,
        "base_branch": base_ref,
        "draft": pr.get("draft", False),
        "merged": pr.get("merged", False),
        "created_at": pr.get("created_at"),
        "updated_at": pr.get("updated_at"),
        "closed_at": pr.get("closed_at"),
    }


class GitHubOperations:
    """Dispatches read-only GitHub API operations."""

    @staticmethod
    async def get_repository(client: GitHubClient, args: Dict[str, Any]) -> ConnectorResult:
        owner = args["owner"]
        repo = args["repo"]
        data = await client.get(f"/repos/{owner}/{repo}")
        summary = _extract_repo_summary(data)
        return ConnectorResult(
            success=True,
            connector="github",
            operation="get_repository",
            data=summary,
            items=[summary],
            metadata={"owner": owner, "repo": repo},
            source=summary.get("html_url"),
        )

    @staticmethod
    async def list_repositories(client: GitHubClient, args: Dict[str, Any]) -> ConnectorResult:
        params = {
            "visibility": args.get("visibility", "all"),
            "sort": args.get("sort", "updated"),
            "per_page": min(args.get("limit", 30), 100),
        }
        data = await client.get("/user/repos", params=params)
        items = [_extract_repo_summary(r) for r in (data if isinstance(data, list) else [])]
        return ConnectorResult(
            success=True,
            connector="github",
            operation="list_repositories",
            data={"count": len(items)},
            items=items,
            metadata={"count": len(items)},
            source="https://github.com",
        )

    @staticmethod
    async def search_repositories(client: GitHubClient, args: Dict[str, Any]) -> ConnectorResult:
        params = {
            "q": args["query"],
            "sort": args.get("sort"),
            "order": args.get("order", "desc"),
            "per_page": min(args.get("limit", 30), 100),
        }
        data = await client.get("/search/repositories", params=params)
        raw_items = data.get("items", []) if isinstance(data, dict) else []
        items = [_extract_repo_summary(r) for r in raw_items]
        return ConnectorResult(
            success=True,
            connector="github",
            operation="search_repositories",
            data={"total_count": data.get("total_count", len(items))},
            items=items,
            metadata={"total_count": data.get("total_count", len(items)), "query": args["query"]},
            source="https://github.com/search",
        )

    @staticmethod
    async def get_issue(client: GitHubClient, args: Dict[str, Any]) -> ConnectorResult:
        owner = args["owner"]
        repo = args["repo"]
        issue_number = args["issue_number"]
        data = await client.get(f"/repos/{owner}/{repo}/issues/{issue_number}")
        summary = _extract_issue_summary(data)
        return ConnectorResult(
            success=True,
            connector="github",
            operation="get_issue",
            data=summary,
            items=[summary],
            metadata={"owner": owner, "repo": repo, "issue_number": issue_number},
            source=summary.get("html_url"),
        )

    @staticmethod
    async def list_issues(client: GitHubClient, args: Dict[str, Any]) -> ConnectorResult:
        owner = args["owner"]
        repo = args["repo"]
        params = {
            "state": args.get("state", "open"),
            "per_page": min(args.get("limit", 30), 100),
        }
        data = await client.get(f"/repos/{owner}/{repo}/issues", params=params)
        raw_items = data if isinstance(data, list) else []
        # Filter out pull requests from issues list endpoint
        items = [_extract_issue_summary(i) for i in raw_items if "pull_request" not in i]
        return ConnectorResult(
            success=True,
            connector="github",
            operation="list_issues",
            data={"count": len(items)},
            items=items,
            metadata={"owner": owner, "repo": repo, "count": len(items)},
            source=f"https://github.com/{owner}/{repo}/issues",
        )

    @staticmethod
    async def search_issues(client: GitHubClient, args: Dict[str, Any]) -> ConnectorResult:
        params = {
            "q": args["query"],
            "sort": args.get("sort"),
            "order": args.get("order", "desc"),
            "per_page": min(args.get("limit", 30), 100),
        }
        data = await client.get("/search/issues", params=params)
        raw_items = data.get("items", []) if isinstance(data, dict) else []
        items = [_extract_issue_summary(i) for i in raw_items]
        return ConnectorResult(
            success=True,
            connector="github",
            operation="search_issues",
            data={"total_count": data.get("total_count", len(items))},
            items=items,
            metadata={"total_count": data.get("total_count", len(items)), "query": args["query"]},
            source="https://github.com/search",
        )

    @staticmethod
    async def get_pull_request(client: GitHubClient, args: Dict[str, Any]) -> ConnectorResult:
        owner = args["owner"]
        repo = args["repo"]
        pull_number = args["pull_number"]
        data = await client.get(f"/repos/{owner}/{repo}/pulls/{pull_number}")
        summary = _extract_pr_summary(data)
        return ConnectorResult(
            success=True,
            connector="github",
            operation="get_pull_request",
            data=summary,
            items=[summary],
            metadata={"owner": owner, "repo": repo, "pull_number": pull_number},
            source=summary.get("html_url"),
        )

    @staticmethod
    async def list_pull_requests(client: GitHubClient, args: Dict[str, Any]) -> ConnectorResult:
        owner = args["owner"]
        repo = args["repo"]
        params = {
            "state": args.get("state", "open"),
            "per_page": min(args.get("limit", 30), 100),
        }
        data = await client.get(f"/repos/{owner}/{repo}/pulls", params=params)
        raw_items = data if isinstance(data, list) else []
        items = [_extract_pr_summary(p) for p in raw_items]
        return ConnectorResult(
            success=True,
            connector="github",
            operation="list_pull_requests",
            data={"count": len(items)},
            items=items,
            metadata={"owner": owner, "repo": repo, "count": len(items)},
            source=f"https://github.com/{owner}/{repo}/pulls",
        )

    @staticmethod
    async def get_file_contents(client: GitHubClient, args: Dict[str, Any]) -> ConnectorResult:
        owner = args["owner"]
        repo = args["repo"]
        path = args["path"].lstrip("/")
        params = {}
        if args.get("ref"):
            params["ref"] = args["ref"]

        data = await client.get(f"/repos/{owner}/{repo}/contents/{path}", params=params)
        
        content_text = ""
        encoding = data.get("encoding")
        raw_content = data.get("content", "")
        if encoding == "base64" and raw_content:
            try:
                decoded_bytes = base64.b64decode(raw_content)
                content_text = decoded_bytes.decode("utf-8", errors="replace")
            except Exception:
                content_text = "[UNABLE_TO_DECODE_BINARY_OR_ENCODED_CONTENT]"
        elif isinstance(data, list):
            # Directory listing
            entries = [{"name": item.get("name"), "path": item.get("path"), "type": item.get("type")} for item in data]
            return ConnectorResult(
                success=True,
                connector="github",
                operation="get_file_contents",
                data={"type": "dir", "entries": entries},
                items=entries,
                metadata={"owner": owner, "repo": repo, "path": path, "type": "directory"},
                source=f"https://github.com/{owner}/{repo}/tree/main/{path}",
            )

        file_summary = {
            "name": data.get("name"),
            "path": data.get("path"),
            "sha": data.get("sha"),
            "size": data.get("size"),
            "html_url": data.get("html_url"),
            "download_url": data.get("download_url"),
            "content": content_text,
        }

        return ConnectorResult(
            success=True,
            connector="github",
            operation="get_file_contents",
            data=file_summary,
            items=[file_summary],
            metadata={"owner": owner, "repo": repo, "path": path, "size": data.get("size")},
            source=data.get("html_url"),
        )

    @staticmethod
    async def search_code(client: GitHubClient, args: Dict[str, Any]) -> ConnectorResult:
        params = {
            "q": args["query"],
            "sort": args.get("sort"),
            "order": args.get("order", "desc"),
            "per_page": min(args.get("limit", 30), 100),
        }
        data = await client.get("/search/code", params=params)
        raw_items = data.get("items", []) if isinstance(data, dict) else []
        items = []
        for it in raw_items:
            repo_info = it.get("repository", {})
            items.append({
                "name": it.get("name"),
                "path": it.get("path"),
                "sha": it.get("sha"),
                "html_url": it.get("html_url"),
                "repository": repo_info.get("full_name"),
            })
        return ConnectorResult(
            success=True,
            connector="github",
            operation="search_code",
            data={"total_count": data.get("total_count", len(items))},
            items=items,
            metadata={"total_count": data.get("total_count", len(items)), "query": args["query"]},
            source="https://github.com/search",
        )
