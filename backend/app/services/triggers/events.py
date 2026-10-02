"""
Normalized TriggerEvent model and EventTriggerService for normalizing external & connector events.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class TriggerEvent(BaseModel):
    """
    Normalized internal event container for all trigger activations.
    External event payloads are treated as untrusted and encapsulated safely.
    """
    model_config = ConfigDict(extra="ignore")

    event_id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:16]}")
    event_type: str = Field(..., description="Canonical event identifier, e.g. github.issue.created")
    source: str = Field(..., description="Source origin, e.g. github, webhook, schedule, manual")
    workspace_id: uuid.UUID = Field(..., description="Target workspace identifier")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: Dict[str, Any] = Field(default_factory=dict, description="Untrusted event data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Operational metadata e.g. headers, delivery_id")


class EventTriggerService:
    """
    Normalizes raw external connector and webhook payloads into standard TriggerEvent instances.
    """

    @staticmethod
    def normalize_github_event(
        raw_payload: Dict[str, Any],
        headers: Dict[str, str],
        workspace_id: uuid.UUID,
    ) -> TriggerEvent:
        """
        Normalizes GitHub webhook payloads into canonical TriggerEvent.
        Handles GitHub events: issues, pull_request, ping.
        """
        gh_event = headers.get("x-github-event") or headers.get("X-GitHub-Event", "generic")
        delivery_id = (
            headers.get("x-github-delivery")
            or headers.get("X-GitHub-Delivery")
            or raw_payload.get("delivery_id")
            or f"gh_{uuid.uuid4().hex[:12]}"
        )

        action = raw_payload.get("action", "")
        event_type = f"github.{gh_event}"

        if gh_event == "issues":
            if action == "opened":
                event_type = "github.issue.created"
            elif action in ("edited", "labeled", "unlabeled", "closed", "reopened", "assigned"):
                event_type = "github.issue.updated"
            else:
                event_type = f"github.issue.{action}" if action else "github.issue.updated"

        elif gh_event == "pull_request":
            if action == "opened":
                event_type = "github.pull_request.opened"
            elif action in ("synchronize", "edited", "labeled", "closed", "reopened"):
                event_type = "github.pull_request.updated"
            else:
                event_type = f"github.pull_request.{action}" if action else "github.pull_request.updated"

        elif gh_event == "ping":
            event_type = "github.ping"

        # Safe extraction without arbitrary code execution
        sanitized_payload = {
            "action": action,
            "repository": {
                "id": raw_payload.get("repository", {}).get("id"),
                "name": raw_payload.get("repository", {}).get("name"),
                "full_name": raw_payload.get("repository", {}).get("full_name"),
                "owner": raw_payload.get("repository", {}).get("owner", {}).get("login"),
                "default_branch": raw_payload.get("repository", {}).get("default_branch"),
            } if isinstance(raw_payload.get("repository"), dict) else {},
            "sender": {
                "login": raw_payload.get("sender", {}).get("login"),
                "id": raw_payload.get("sender", {}).get("id"),
            } if isinstance(raw_payload.get("sender"), dict) else {},
        }

        if "issue" in raw_payload and isinstance(raw_payload["issue"], dict):
            iss = raw_payload["issue"]
            sanitized_payload["issue"] = {
                "number": iss.get("number"),
                "title": iss.get("title"),
                "body": iss.get("body"),
                "state": iss.get("state"),
                "labels": [lbl.get("name") if isinstance(lbl, dict) else str(lbl) for lbl in iss.get("labels", [])],
                "user": iss.get("user", {}).get("login") if isinstance(iss.get("user"), dict) else None,
                "created_at": iss.get("created_at"),
                "updated_at": iss.get("updated_at"),
            }

        if "pull_request" in raw_payload and isinstance(raw_payload["pull_request"], dict):
            pr = raw_payload["pull_request"]
            sanitized_payload["pull_request"] = {
                "number": pr.get("number"),
                "title": pr.get("title"),
                "body": pr.get("body"),
                "state": pr.get("state"),
                "head": {"ref": pr.get("head", {}).get("ref"), "sha": pr.get("head", {}).get("sha")} if isinstance(pr.get("head"), dict) else {},
                "base": {"ref": pr.get("base", {}).get("ref")} if isinstance(pr.get("base"), dict) else {},
                "labels": [lbl.get("name") if isinstance(lbl, dict) else str(lbl) for lbl in pr.get("labels", [])],
                "user": pr.get("user", {}).get("login") if isinstance(pr.get("user"), dict) else None,
            }

        # Retain any extra top-level fields safely
        for k, v in raw_payload.items():
            if k not in sanitized_payload:
                sanitized_payload[k] = v

        return TriggerEvent(
            event_id=str(delivery_id),
            event_type=event_type,
            source="github",
            workspace_id=workspace_id,
            timestamp=datetime.now(timezone.utc),
            payload=sanitized_payload,
            metadata={
                "github_event": gh_event,
                "action": action,
                "delivery_id": delivery_id,
            },
        )

    @staticmethod
    def normalize_generic_webhook(
        raw_payload: Dict[str, Any],
        headers: Dict[str, str],
        workspace_id: uuid.UUID,
        event_type: str = "webhook.workflow.run",
    ) -> TriggerEvent:
        """
        Normalizes generic webhook request payload.
        """
        event_id = headers.get("x-request-id") or f"wh_{uuid.uuid4().hex[:12]}"
        return TriggerEvent(
            event_id=event_id,
            event_type=event_type,
            source="webhook",
            workspace_id=workspace_id,
            timestamp=datetime.now(timezone.utc),
            payload=raw_payload,
            metadata={k.lower(): v for k, v in headers.items() if not k.lower().startswith("authorization")},
        )
