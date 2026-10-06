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


class CollaborationCommentsResource:
    def __init__(self, client: "Client"):
        self._client = client

    def list(
        self,
        session_id: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        params = {"resource_type": resource_type, "resource_id": resource_id, "limit": limit, "offset": offset}
        params = {k: v for k, v in params.items() if v is not None}
        return self._client._request("GET", f"/collaboration/sessions/{session_id}/comments", params=params)

    def create(
        self,
        session_id: str,
        body: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        parent_comment_id: Optional[str] = None,
        is_ai: bool = False,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {
            "body": body,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "parent_comment_id": parent_comment_id,
            "is_ai": is_ai,
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        return self._client._request(
            "POST",
            f"/collaboration/sessions/{session_id}/comments",
            json=payload,
            idempotency_key=idempotency_key,
        )


class CollaborationAssignmentsResource:
    def __init__(self, client: "Client"):
        self._client = client

    def list(
        self,
        session_id: str,
        status: Optional[str] = None,
        assigned_to: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        params = {"status": status, "assigned_to": assigned_to, "limit": limit, "offset": offset}
        params = {k: v for k, v in params.items() if v is not None}
        return self._client._request("GET", f"/collaboration/sessions/{session_id}/assignments", params=params)

    def create(
        self,
        session_id: str,
        assigned_to: str,
        assignment_type: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        due_at: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {
            "assigned_to": assigned_to,
            "assignment_type": assignment_type,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "due_at": due_at,
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        return self._client._request(
            "POST",
            f"/collaboration/sessions/{session_id}/assignments",
            json=payload,
            idempotency_key=idempotency_key,
        )


class CollaborationSessionsResource:
    def __init__(self, client: "Client"):
        self._client = client
        self.comments = CollaborationCommentsResource(client)
        self.assignments = CollaborationAssignmentsResource(client)

    def create(
        self,
        resource_type: str,
        resource_id: str,
        workspace_id: Optional[str] = None,
        project_id: Optional[str] = None,
        expires_at: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {
            "resource_type": resource_type,
            "resource_id": resource_id,
            "workspace_id": workspace_id,
            "project_id": project_id,
            "expires_at": expires_at,
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        return self._client._request(
            "POST",
            "/collaboration/sessions",
            json=payload,
            idempotency_key=idempotency_key,
        )

    def list(
        self,
        workspace_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        params = {
            "workspace_id": workspace_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "status": status,
            "limit": limit,
            "offset": offset,
        }
        params = {k: v for k, v in params.items() if v is not None}
        return self._client._request("GET", "/collaboration/sessions", params=params)

    def get(self, session_id: str) -> Dict[str, Any]:
        return self._client._request("GET", f"/collaboration/sessions/{session_id}")

    def events(self, session_id: str) -> Iterator[str]:
        """Streams Server-Sent Events line by line."""
        url = f"{self._client.base_url}/collaboration/sessions/{session_id}/events"
        headers = {"Authorization": f"Bearer {self._client.api_key}", "Accept": "text/event-stream"}
        with httpx.stream("GET", url, headers=headers, timeout=60.0) as response:
            for line in response.iter_lines():
                if line:
                    yield line


class CollaborationResource:
    def __init__(self, client: "Client"):
        self._client = client
        self.sessions = CollaborationSessionsResource(client)


class AgentsResource:
    def __init__(self, client: "Client"):
        self._client = client

    def list(self, project_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {}
        if project_id:
            params["project_id"] = project_id
        if status:
            params["status"] = status
        return self._client._request("GET", "/agents", params=params)

    def get(self, agent_id: str) -> Dict[str, Any]:
        return self._client._request("GET", f"/agents/{agent_id}")

    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._client._request("POST", "/agents", json=payload)

    def update(self, agent_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._client._request("PATCH", f"/agents/{agent_id}", json=payload)

    def delete(self, agent_id: str) -> None:
        return self._client._request("DELETE", f"/agents/{agent_id}")

    def create_version(self, agent_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._client._request("POST", f"/agents/{agent_id}/versions", json=payload)

    def publish(self, agent_id: str, version_id: Optional[str] = None) -> Dict[str, Any]:
        params = {"version_id": version_id} if version_id else None
        return self._client._request("POST", f"/agents/{agent_id}/publish", params=params)

    def activate(self, agent_id: str) -> Dict[str, Any]:
        return self._client._request("POST", f"/agents/{agent_id}/activate")

    def pause(self, agent_id: str) -> Dict[str, Any]:
        return self._client._request("POST", f"/agents/{agent_id}/pause")

    def run(self, agent_id: str, input_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        payload = {"input": input_data, **kwargs}
        return self._client._request("POST", f"/agents/{agent_id}/runs", json=payload)

    def list_runs(self, agent_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {"status": status} if status else None
        return self._client._request("GET", f"/agents/{agent_id}/runs", params=params)

    def get_run(self, run_id: str) -> Dict[str, Any]:
        return self._client._request("GET", f"/agent-runs/{run_id}")

    def delegate(self, agent_id: str, child_agent_id: str, reason: str, **kwargs) -> Dict[str, Any]:
        payload = {"child_agent_id": child_agent_id, "reason": reason, **kwargs}
        return self._client._request("POST", f"/agents/{agent_id}/delegate", json=payload)

    def trace(self, run_id: str) -> Dict[str, Any]:
        return self._client._request("GET", f"/agent-runs/{run_id}/trace")

    def replay(self, run_id: str) -> Dict[str, Any]:
        return self._client._request("GET", f"/agent-runs/{run_id}/replay")


class AgentTeamsResource:
    def __init__(self, client: "Client"):
        self._client = client

    def list(self, project_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {}
        if project_id:
            params["project_id"] = project_id
        if status:
            params["status"] = status
        return self._client._request("GET", "/agent-teams", params=params)

    def get(self, team_id: str) -> Dict[str, Any]:
        return self._client._request("GET", f"/agent-teams/{team_id}")

    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._client._request("POST", "/agent-teams", json=payload)

    def update(self, team_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._client._request("PATCH", f"/agent-teams/{team_id}", json=payload)

    def run(self, team_id: str, input_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        payload = {"input": input_data, **kwargs}
        return self._client._request("POST", f"/agent-teams/{team_id}/runs", json=payload)

    def list_runs(self, team_id: str) -> List[Dict[str, Any]]:
        return self._client._request("GET", f"/agent-teams/{team_id}/runs")

    def get_run(self, run_id: str) -> Dict[str, Any]:
        return self._client._request("GET", f"/agent-team-runs/{run_id}")


class SimulationsResource:
    def __init__(self, client: "Client"):
        self._client = client

    def create(self, payload: Dict[str, Any], idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        return self._client._request("POST", "/simulations", json=payload, idempotency_key=idempotency_key)

    def get(self, simulation_id: str) -> Dict[str, Any]:
        return self._client._request("GET", f"/simulations/{simulation_id}")

    def list(self, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        return self._client._request("GET", "/simulations", params=params)

    def update(self, simulation_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._client._request("PATCH", f"/simulations/{simulation_id}", json=payload)

    def create_version(self, simulation_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._client._request("POST", f"/simulations/{simulation_id}/versions", json=payload)

    def run(self, simulation_id: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self._client._request("POST", f"/simulations/{simulation_id}/run", json=payload or {})

    def list_runs(self, simulation_id: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        return self._client._request("GET", f"/simulations/{simulation_id}/runs", params=params)

    def get_run(self, run_id: str) -> Dict[str, Any]:
        return self._client._request("GET", f"/simulation-runs/{run_id}")

    def get_trace(self, run_id: str) -> Dict[str, Any]:
        return self._client._request("GET", f"/simulation-runs/{run_id}/trace")

    def get_report(self, run_id: str) -> Dict[str, Any]:
        return self._client._request("GET", f"/simulation-runs/{run_id}/report")

    def get_side_effects(self, run_id: str) -> List[Dict[str, Any]]:
        return self._client._request("GET", f"/simulation-runs/{run_id}/side-effects")

    def get_assertions(self, run_id: str) -> List[Dict[str, Any]]:
        return self._client._request("GET", f"/simulation-runs/{run_id}/assertions")

    def compare(self, run_id: str, comparison_run_id: str) -> Dict[str, Any]:
        return self._client._request("POST", f"/simulation-runs/{run_id}/compare", json={"comparison_run_id": comparison_run_id})


class ScenariosResource:
    def __init__(self, client: "Client"):
        self._client = client

    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._client._request("POST", "/simulation-scenarios", json=payload)

    def get(self, scenario_id: str) -> Dict[str, Any]:
        return self._client._request("GET", f"/simulation-scenarios/{scenario_id}")

    def update(self, scenario_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._client._request("PATCH", f"/simulation-scenarios/{scenario_id}", json=payload)


class SuitesResource:
    def __init__(self, client: "Client"):
        self._client = client

    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._client._request("POST", "/simulation-suites", json=payload)

    def get(self, suite_id: str) -> Dict[str, Any]:
        return self._client._request("GET", f"/simulation-suites/{suite_id}")

    def list(self, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        return self._client._request("GET", "/simulation-suites", params=params)

    def run(self, suite_id: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self._client._request("POST", f"/simulation-suites/{suite_id}/run", json=payload or {})


class ObjectivesResource:
    def __init__(self, client: "Client"):
        self._client = client

    def create(self, payload: Dict[str, Any], idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        return self._client._request("POST", "/objectives", json=payload, idempotency_key=idempotency_key)

    def get(self, objective_id: str) -> Dict[str, Any]:
        return self._client._request("GET", f"/objectives/{objective_id}")

    def list(self, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        return self._client._request("GET", "/objectives", params=params)

    def update(self, objective_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._client._request("PATCH", f"/objectives/{objective_id}", json=payload)

    def delete(self, objective_id: str) -> Dict[str, Any]:
        return self._client._request("DELETE", f"/objectives/{objective_id}")

    def get_health(self, objective_id: str) -> Dict[str, Any]:
        return self._client._request("GET", f"/objectives/{objective_id}/health")

    def get_work_map(self, objective_id: str) -> Dict[str, Any]:
        return self._client._request("GET", f"/objectives/{objective_id}/work-map")


class OutcomesResource:
    def __init__(self, client: "Client"):
        self._client = client

    def create(self, payload: Dict[str, Any], idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        return self._client._request("POST", "/outcomes", json=payload, idempotency_key=idempotency_key)

    def get(self, outcome_id: str) -> Dict[str, Any]:
        return self._client._request("GET", f"/outcomes/{outcome_id}")

    def list(self, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        return self._client._request("GET", "/outcomes", params=params)

    def add_evidence(self, outcome_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._client._request("POST", f"/outcomes/{outcome_id}/evidence", json=payload)

    def verify(self, outcome_id: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self._client._request("POST", f"/outcomes/{outcome_id}/verify", json=payload or {})

    def dispute(self, outcome_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._client._request("POST", f"/outcomes/{outcome_id}/dispute", json=payload)

    def get_impact(self, outcome_id: str) -> List[Dict[str, Any]]:
        return self._client._request("GET", f"/outcomes/{outcome_id}/impact")

    def get_work(self, outcome_id: str) -> List[Dict[str, Any]]:
        return self._client._request("GET", f"/outcomes/{outcome_id}/work")

    def get_graph(self, outcome_id: str) -> Dict[str, Any]:
        return self._client._request("GET", f"/outcomes/{outcome_id}/graph")


class DecisionsResource:
    def __init__(self, client: "Client"):
        self._client = client

    def create(self, payload: Dict[str, Any], idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        return self._client._request("POST", "/decisions", json=payload, idempotency_key=idempotency_key)

    def get(self, decision_id: str) -> Dict[str, Any]:
        return self._client._request("GET", f"/decisions/{decision_id}")

    def list(self, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        return self._client._request("GET", "/decisions", params=params)

    def approve(self, decision_id: str) -> Dict[str, Any]:
        return self._client._request("POST", f"/decisions/{decision_id}/approve")

    def reject(self, decision_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
        params = {"reason": reason} if reason else None
        return self._client._request("POST", f"/decisions/{decision_id}/reject", params=params)


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
        self.collaboration = CollaborationResource(self)
        self.agents = AgentsResource(self)
        self.agent_teams = AgentTeamsResource(self)
        self.simulations = SimulationsResource(self)
        self.scenarios = ScenariosResource(self)
        self.suites = SuitesResource(self)
        self.objectives = ObjectivesResource(self)
        self.outcomes = OutcomesResource(self)
        self.decisions = DecisionsResource(self)


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
