"""
Dependency topology and check mapping for Step 35: AI Reliability, Resilience & Chaos Engineering Layer.
"""
from typing import Dict, List

# Standard bounded dependency topology mapping components to downstream dependencies
COMPONENT_DEPENDENCIES: Dict[str, List[str]] = {
    "api": ["database"],
    "worker": ["database", "ai_gateway"],
    "ai_gateway": ["model_provider"],
    "model_provider": ["connectivity"],
    "workflow": ["worker", "database", "ai_gateway", "tool", "connector"],
    "trigger": ["database", "event_bus"],
    "connector": ["connectivity", "authentication"],
    "tool": ["worker"],
    "retrieval": ["database", "embedding"],
    "embedding": ["ai_gateway"],
    "reranker": ["ai_gateway"],
    "cache": ["database"],
    "memory": ["database", "embedding"],
    "knowledge_graph": ["database"],
    "event_bus": ["database"],
    "notification": ["database", "connectivity"],
    "evaluation": ["ai_gateway", "database"],
    "replay": ["database"],
    "artifact_processor": ["storage", "database"],
}
