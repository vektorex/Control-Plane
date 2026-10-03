"""
AIWorkLayer Python Client.
Provides synchronous and streaming access to public endpoints.
"""
import os
import time
from typing import Any, Dict, Iterator, List, Optional
import httpx

from .exceptions import (
    APIError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    DependencyError,
    ExecutionError,
    GovernanceError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)


class TasksResource:
    def __init__(self, client: "Client"):
        self._client = client

    def run(self, task_id: str, input_text: str, stream: bool = False, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        payload = {"input": input_text, "stream": stream}
        return self._client._request("POST", f"/tasks/{task_id}/runs", json=payload, idempotency_key=idempotency_key)


class RunsResource:
    def __init__(self, client: "Client"):
        self._client = client

    def get(self, run_id: str) -> Dict[str, Any]:
        return self._client._request("GET", f"/runs/{run_id}")

    def result(self, run_id: str) -> Dict[str, Any]:
        return self._client._request("GET", f"/runs/{run_id}/result")

    def events(self, run_id: str) -> Dict[str, Any]:
        return self._client._request("GET", f"/runs/{run_id}/events")

    def usage(self, run_id: str) -> Dict[str, Any]:
        return self._client._request("GET", f"/runs/{run_id}/usage")

    def stream(self, run_id: str) -> Iterator[str]:
        """Streams Server-Sent Events line by line."""
        url = f"{self._client.base_url}/runs/{run_id}/stream"
        headers = {"Authorization": f"Bearer {self._client.api_key}", "Accept": "text/event-stream"}
        with httpx.stream("GET", url, headers=headers, timeout=60.0) as response:
            for line in response.iter_lines():
                if line:
                    yield line


class WorkflowsResource:
    def __init__(self, client: "Client"):
        self._client = client

    def list(self) -> Dict[str, Any]:
        return self._client._request("GET", "/workflows")

    def get(self, workflow_id: str) -> Dict[str, Any]:
        return self._client._request("GET", f"/workflows/{workflow_id}")

    def run(self, workflow_id: str, inputs: Optional[Dict[str, Any]] = None, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        payload = {"inputs": inputs or {}}
        return self._client._request("POST", f"/workflows/{workflow_id}/runs", json=payload, idempotency_key=idempotency_key)

    def run_status(self, run_id: str) -> Dict[str, Any]:
        return self._client._request("GET", f"/workflows/runs/{run_id}")


class ArtifactsResource:
    def __init__(self, client: "Client"):
        self._client = client

    def create(self, name: str, mime_type: str = "application/octet-stream", size_bytes: int = 0) -> Dict[str, Any]:
        return self._client._request("POST", "/artifacts", json={"name": name, "mime_type": mime_type, "size_bytes": size_bytes})

    def get(self, artifact_id: str) -> Dict[str, Any]:
        return self._client._request("GET", f"/artifacts/{artifact_id}")

    def parts(self, artifact_id: str) -> Dict[str, Any]:
        return self._client._request("GET", f"/artifacts/{artifact_id}/parts")


class DocumentsResource:
    def __init__(self, client: "Client"):
        self._client = client

    def list(self) -> Dict[str, Any]:
        return self._client._request("GET", "/documents")

    def get(self, document_id: str) -> Dict[str, Any]:
        return self._client._request("GET", f"/documents/{document_id}")


class ModelsResource:
    def __init__(self, client: "Client"):
        self._client = client

    def list(self) -> Dict[str, Any]:
        return self._client._request("GET", "/models")


class MemoryResource:
    def __init__(self, client: "Client"):
        self._client = client

    def list(self) -> Dict[str, Any]:
        return self._client._request("GET", "/memory")

    def create(self, key: str, content: str) -> Dict[str, Any]:
        return self._client._request("POST", "/memory", json={"key": key, "content": content})


class KnowledgeResource:
    def __init__(self, client: "Client"):
        self._client = client

    def entities(self) -> Dict[str, Any]:
        return self._client._request("GET", "/knowledge/entities")

    def entity(self, entity_id: str) -> Dict[str, Any]:
        return self._client._request("GET", f"/knowledge/entities/{entity_id}")

    def relationships(self, entity_id: str) -> Dict[str, Any]:
        return self._client._request("GET", f"/knowledge/entities/{entity_id}/relationships")


class UsageResource:
    def __init__(self, client: "Client"):
        self._client = client

    def get(self, period_hours: int = 24, endpoint: Optional[str] = None) -> Dict[str, Any]:
        params = {"period_hours": period_hours}
        if endpoint:
            params["endpoint"] = endpoint
        return self._client._request("GET", "/usage", params=params)


class WebhooksResource:
    def __init__(self, client: "Client"):
        self._client = client

    def list(self) -> Dict[str, Any]:
        return self._client._request("GET", "/webhooks")

    def create(self, url: str, events: List[str]) -> Dict[str, Any]:
        return self._client._request("POST", "/webhooks", json={"url": url, "events": events})

    def get(self, subscription_id: str) -> Dict[str, Any]:
        return self._client._request("GET", f"/webhooks/{subscription_id}")

    def delete(self, subscription_id: str) -> None:
        self._client._request("DELETE", f"/webhooks/{subscription_id}")


class MarketplaceResource:
    def __init__(self, client: "Client"):
        self._client = client

    def list(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        package_type: Optional[str] = None,
        visibility: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        params = {
            "query": query,
            "category": category,
            "package_type": package_type,
            "visibility": visibility,
            "status": status,
            "limit": limit,
            "offset": offset,
        }
        params = {k: v for k, v in params.items() if v is not None}
        return self._client._request("GET", "/marketplace/packages", params=params)

    def get(self, slug: str) -> Dict[str, Any]:
        return self._client._request("GET", f"/marketplace/packages/{slug}")

    def versions(self, slug: str) -> Dict[str, Any]:
        return self._client._request("GET", f"/marketplace/packages/{slug}/versions")

    def install(
        self,
        package_id: str,
        package_version_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {
            "package_version_id": package_version_id,
            "workspace_id": workspace_id,
            "configuration": configuration or {},
        }
        return self._client._request(
            "POST",
            f"/marketplace/packages/{package_id}/installations",
            json=payload,
            idempotency_key=idempotency_key,
        )

    def list_installations(
        self,
        workspace_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        params = {"workspace_id": workspace_id, "status": status}
        params = {k: v for k, v in params.items() if v is not None}
        return self._client._request("GET", "/marketplace/installations", params=params)

    def get_installation(self, installation_id: str) -> Dict[str, Any]:
        return self._client._request("GET", f"/marketplace/installations/{installation_id}")

    def update(
        self,
        installation_id: str,
        target_version_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {"target_version_id": target_version_id} if target_version_id else {}
        return self._client._request(
            "POST",
            f"/marketplace/installations/{installation_id}/update",
            json=payload,
            idempotency_key=idempotency_key,
        )

    def rollback(
        self,
        installation_id: str,
        target_version_id: Optional[str] = None,
        reason: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {"target_version_id": target_version_id, "reason": reason}
        payload = {k: v for k, v in payload.items() if v is not None}
        return self._client._request(
            "POST",
            f"/marketplace/installations/{installation_id}/rollback",
            json=payload,
            idempotency_key=idempotency_key,
        )

    def fork(
        self,
        package_id: str,
        new_name: str,
        new_slug: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {"new_name": new_name, "new_slug": new_slug}
        return self._client._request(
            "POST",
            f"/marketplace/packages/{package_id}/fork",
            json=payload,
            idempotency_key=idempotency_key,
        )

    def usage(self, package_id: str) -> Dict[str, Any]:
        return self._client._request("GET", f"/marketplace/packages/{package_id}/usage")


class Client:
    """Official AI Work Layer SDK client for Python applications."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "http://localhost:8000/api/v1",
        max_retries: int = 2,
        timeout: float = 30.0,
    ):
        self.api_key = api_key or os.environ.get("AWL_API_KEY")
        if not self.api_key:
            raise AuthenticationError("API key must be provided explicitly or via AWL_API_KEY environment variable.")

        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.timeout = timeout

        self.tasks = TasksResource(self)
        self.runs = RunsResource(self)
        self.workflows = WorkflowsResource(self)
        self.artifacts = ArtifactsResource(self)
        self.documents = DocumentsResource(self)
        self.models = ModelsResource(self)
        self.memory = MemoryResource(self)
        self.knowledge = KnowledgeResource(self)
        self.usage = UsageResource(self)
        self.webhooks = WebhooksResource(self)
        self.marketplace = MarketplaceResource(self)

    def _request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> Any:
        url = f"{self.base_url}{path if path.startswith('/') else f'/{path}'}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        is_get = method.upper() == "GET"
        allow_retry = is_get or bool(idempotency_key)
        attempts = 0

        while attempts <= (self.max_retries if allow_retry else 0):
            attempts += 1
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.request(method, url, json=json, params=params, headers=headers)

                    if resp.status_code == 204:
                        return None

                    try:
                        data = resp.json()
                    except Exception:
                        data = {"raw": resp.text}

                    if not resp.is_success:
                        self._handle_error(resp.status_code, data, resp.headers)

                    return data
            except (httpx.ConnectError, httpx.TimeoutException) as ex:
                if not allow_retry or attempts > self.max_retries:
                    raise DependencyError(f"Network error communicating with platform: {str(ex)}")
                time.sleep(attempts * 0.5)

    def _handle_error(self, status_code: int, data: Dict[str, Any], headers: httpx.Headers) -> None:
        err = data.get("error", {})
        msg = err.get("message", f"Request failed with status {status_code}")
        req_id = err.get("request_id", headers.get("x-request-id"))
        details = err.get("details")

        if status_code == 401:
            raise AuthenticationError(msg, request_id=req_id)
        elif status_code == 403:
            if err.get("type") == "governance_error":
                raise GovernanceError(msg, request_id=req_id, details=details)
            raise AuthorizationError(msg, request_id=req_id, details=details)
        elif status_code in (400, 422):
            raise ValidationError(msg, request_id=req_id, details=details)
        elif status_code == 404:
            raise NotFoundError(msg, request_id=req_id, details=details)
        elif status_code == 409:
            raise ConflictError(msg, request_id=req_id, details=details)
        elif status_code == 429:
            retry_after = int(headers.get("retry-after", 60))
            raise RateLimitError(msg, request_id=req_id, retry_after=retry_after)
        elif status_code >= 500:
            raise ExecutionError(msg, request_id=req_id)
        else:
            raise APIError(msg, status_code=status_code, request_id=req_id, details=details)
