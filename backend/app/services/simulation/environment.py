"""
Simulation Environment Manager for Step 41: AI Agent Simulation.
Manages isolated, snapshot, and synthetic environments ensuring zero production state leaks.
"""
from typing import Any, Dict, List, Optional
from backend.app.services.simulation.safety import SimulationSafetyEnforcer
from backend.app.services.simulation.schemas import EnvironmentMode


class SimulationEnvironmentManager:
    """
    Constructs and verifies isolated sandbox environments.
    """

    @classmethod
    def prepare_environment(
        cls,
        mode: EnvironmentMode = EnvironmentMode.ISOLATED,
        raw_config: Optional[Dict[str, Any]] = None,
        production_snapshot: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Builds the environment payload for a simulation run.
        Sanitizes all production snapshot data.
        """
        config = raw_config or {}

        if mode == EnvironmentMode.ISOLATED:
            return {
                "mode": EnvironmentMode.ISOLATED.value,
                "database_state": "isolated_ephemeral",
                "synthetic_documents": config.get("synthetic_documents", []),
                "synthetic_artifacts": config.get("synthetic_artifacts", []),
                "synthetic_connector_responses": config.get("synthetic_connector_responses", {}),
                "synthetic_tool_responses": config.get("synthetic_tool_responses", {}),
                "synthetic_memory": config.get("synthetic_memory", []),
                "synthetic_knowledge_graph": config.get("synthetic_knowledge_graph", {"entities": [], "relationships": []}),
                "synthetic_user_inputs": config.get("synthetic_user_inputs", []),
                "synthetic_events": config.get("synthetic_events", []),
            }

        elif mode == EnvironmentMode.SNAPSHOT:
            # Must sanitize production snapshot thoroughly
            sanitized_snap = SimulationSafetyEnforcer.sanitize_snapshot_data(production_snapshot or {})
            return {
                "mode": EnvironmentMode.SNAPSHOT.value,
                "database_state": "snapshot_read_only",
                "snapshot_data": sanitized_snap,
                "synthetic_documents": sanitized_snap.get("documents", []),
                "synthetic_artifacts": sanitized_snap.get("artifacts", []),
                "synthetic_connector_responses": sanitized_snap.get("connector_responses", {}),
                "synthetic_tool_responses": sanitized_snap.get("tool_responses", {}),
                "synthetic_memory": sanitized_snap.get("memory", []),
                "synthetic_knowledge_graph": sanitized_snap.get("knowledge_graph", {"entities": [], "relationships": []}),
                "synthetic_user_inputs": [],
                "synthetic_events": [],
            }

        elif mode == EnvironmentMode.SYNTHETIC:
            return {
                "mode": EnvironmentMode.SYNTHETIC.value,
                "database_state": "synthetic_mock",
                "synthetic_documents": config.get("synthetic_documents", [
                    {"id": "doc_synth_1", "title": "Synthetic Company Policy", "content": "All requests must be verified."}
                ]),
                "synthetic_artifacts": config.get("synthetic_artifacts", []),
                "synthetic_connector_responses": config.get("synthetic_connector_responses", {
                    "github:search": {"items": [{"id": 1, "title": "Synthetic issue #1"}]}
                }),
                "synthetic_tool_responses": config.get("synthetic_tool_responses", {}),
                "synthetic_memory": config.get("synthetic_memory", [
                    {"id": "mem_synth_1", "content": "Previous user preference: verbose output", "scope": "agent"}
                ]),
                "synthetic_knowledge_graph": config.get("synthetic_knowledge_graph", {
                    "entities": [{"name": "System", "type": "Platform"}],
                    "relationships": []
                }),
                "synthetic_user_inputs": config.get("synthetic_user_inputs", []),
                "synthetic_events": config.get("synthetic_events", []),
            }

        return {"mode": EnvironmentMode.ISOLATED.value, "database_state": "isolated_ephemeral"}
