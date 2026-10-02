"""
Trigger Registry managing supported event types and their schemas.
"""
from typing import Any, Dict, List, Optional


class TriggerRegistry:
    """
    In-memory registry of supported event types, their sources, and payload descriptors.
    """

    def __init__(self):
        self._events: Dict[str, Dict[str, Any]] = {}
        self._register_default_events()

    def _register_default_events(self) -> None:
        defaults = [
            {
                "event_type": "manual.workflow.run",
                "source": "manual",
                "name": "Manual Workflow Trigger",
                "description": "Triggered explicitly via API or User Interface.",
                "sample_payload": {"user_id": "...", "note": "Manual execution"},
            },
            {
                "event_type": "schedule.workflow.run",
                "source": "schedule",
                "name": "Scheduled Workflow Run",
                "description": "Triggered on a recurring cron or interval schedule.",
                "sample_payload": {"schedule": "0 * * * *", "timezone": "UTC"},
            },
            {
                "event_type": "webhook.workflow.run",
                "source": "webhook",
                "name": "Generic Webhook Ingestion",
                "description": "Triggered by incoming HTTP POST webhook requests.",
                "sample_payload": {"event": "custom_event", "data": {}},
            },
            {
                "event_type": "github.issue.created",
                "source": "github",
                "name": "GitHub Issue Created",
                "description": "Triggered when a new GitHub issue is opened.",
                "sample_payload": {
                    "action": "opened",
                    "issue": {
                        "number": 42,
                        "title": "Bug in auth module",
                        "body": "Detailed description...",
                        "labels": ["bug"],
                        "state": "open",
                    },
                    "repository": {
                        "full_name": "octocat/Hello-World",
                        "name": "Hello-World",
                        "owner": {"login": "octocat"},
                    },
                },
            },
            {
                "event_type": "github.issue.updated",
                "source": "github",
                "name": "GitHub Issue Updated",
                "description": "Triggered when a GitHub issue is edited, labeled, or commented.",
                "sample_payload": {
                    "action": "labeled",
                    "issue": {
                        "number": 42,
                        "title": "Bug in auth module",
                        "labels": ["bug", "priority-high"],
                        "state": "open",
                    },
                    "repository": {
                        "full_name": "octocat/Hello-World",
                    },
                },
            },
            {
                "event_type": "github.pull_request.opened",
                "source": "github",
                "name": "GitHub Pull Request Opened",
                "description": "Triggered when a pull request is opened in the repository.",
                "sample_payload": {
                    "action": "opened",
                    "pull_request": {
                        "number": 101,
                        "title": "Add feature X",
                        "body": "PR description...",
                        "head": {"ref": "feature-x"},
                        "base": {"ref": "main"},
                    },
                    "repository": {
                        "full_name": "octocat/Hello-World",
                    },
                },
            },
            {
                "event_type": "github.pull_request.updated",
                "source": "github",
                "name": "GitHub Pull Request Updated",
                "description": "Triggered when a pull request has new commits, review comments, or status changes.",
                "sample_payload": {
                    "action": "synchronize",
                    "pull_request": {
                        "number": 101,
                        "title": "Add feature X",
                        "state": "open",
                    },
                    "repository": {
                        "full_name": "octocat/Hello-World",
                    },
                },
            },
        ]
        for item in defaults:
            self.register(item["event_type"], item)

    def register(self, event_type: str, metadata: Dict[str, Any]) -> None:
        self._events[event_type] = metadata

    def get(self, event_type: str) -> Optional[Dict[str, Any]]:
        return self._events.get(event_type)

    def list(self) -> List[Dict[str, Any]]:
        return list(self._events.values())

    def exists(self, event_type: str) -> bool:
        return event_type in self._events


# Global registry singleton
trigger_registry = TriggerRegistry()
