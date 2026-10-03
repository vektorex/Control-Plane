"""
Graceful Degradation Engine for Step 35: AI Reliability, Resilience & Chaos Engineering Layer.
Allows subsystems to operate in explicitly degraded modes when auxiliary dependencies are unhealthy.
Never silently degrades when the core task strictly requires the unavailable capability.
"""
from typing import Any, Dict, List, Optional
from backend.app.services.reliability.schemas import DegradationDecisionResult


class DegradationPolicy:
    """Configures explicit allowances for operating in degraded mode."""
    def __init__(
        self,
        allow_cache_bypass: bool = True,
        allow_retrieval_without_reranker: bool = True,
        allow_execution_without_graph: bool = True,
        allow_execution_without_memory: bool = True,
        allow_deterministic_only_mode: bool = False,
        require_all_capabilities: bool = False,
    ):
        self.allow_cache_bypass = allow_cache_bypass
        self.allow_retrieval_without_reranker = allow_retrieval_without_reranker
        self.allow_execution_without_graph = allow_execution_without_graph
        self.allow_execution_without_memory = allow_execution_without_memory
        self.allow_deterministic_only_mode = allow_deterministic_only_mode
        self.require_all_capabilities = require_all_capabilities


class DegradationResolver:
    """Evaluates whether execution can proceed in degraded mode given unhealthy components."""

    @classmethod
    def evaluate_degradation(
        cls,
        unhealthy_components: List[str],
        policy: DegradationPolicy,
        task_requires: Optional[List[str]] = None,
    ) -> DegradationDecisionResult:
        required = set(task_requires or [])
        unhealthy = set(unhealthy_components)
        reasons: List[str] = []

        # Rule 1: Strict task requirements must not be degraded
        conflicts = required.intersection(unhealthy)
        if conflicts or policy.require_all_capabilities:
            return DegradationDecisionResult(
                degraded=False,
                degraded_components=list(unhealthy),
                mode="fail_fast",
                allowed_by_policy=False,
                reasons=[f"Task strictly requires unavailable component(s): {', '.join(conflicts or unhealthy)}"],
            )

        allowed_degradations: List[str] = []

        # Check semantic cache outage
        if "cache" in unhealthy or "semantic_cache" in unhealthy:
            if policy.allow_cache_bypass:
                allowed_degradations.append("cache_bypass")
                reasons.append("Semantic cache unavailable; proceeding with direct execution and cache bypass")
            else:
                return DegradationDecisionResult(
                    degraded=False,
                    degraded_components=["cache"],
                    mode="fail_fast",
                    allowed_by_policy=False,
                    reasons=["Cache bypass not permitted by policy"],
                )

        # Check reranker outage
        if "reranker" in unhealthy:
            if policy.allow_retrieval_without_reranker:
                allowed_degradations.append("retrieval_without_reranking")
                reasons.append("Reranker model unavailable; falling back to hybrid retrieval without reranking score")
            else:
                return DegradationDecisionResult(
                    degraded=False,
                    degraded_components=["reranker"],
                    mode="fail_fast",
                    allowed_by_policy=False,
                    reasons=["Retrieval requires reranker; degradation forbidden by policy"],
                )

        # Check knowledge graph outage
        if "knowledge_graph" in unhealthy:
            if policy.allow_execution_without_graph:
                allowed_degradations.append("execution_without_graph")
                reasons.append("Knowledge Graph unavailable; proceeding without relational graph context")
            else:
                return DegradationDecisionResult(
                    degraded=False,
                    degraded_components=["knowledge_graph"],
                    mode="fail_fast",
                    allowed_by_policy=False,
                    reasons=["Knowledge Graph context required by policy"],
                )

        # Check memory outage
        if "memory" in unhealthy:
            if policy.allow_execution_without_memory:
                allowed_degradations.append("execution_without_memory")
                reasons.append("Memory service unavailable; proceeding with ephemeral prompt context only")

        if allowed_degradations:
            return DegradationDecisionResult(
                degraded=True,
                degraded_components=list(unhealthy),
                mode="+".join(allowed_degradations),
                allowed_by_policy=True,
                reasons=reasons,
            )

        return DegradationDecisionResult(
            degraded=False,
            degraded_components=[],
            mode="full_capability",
            allowed_by_policy=True,
            reasons=["All required components are healthy"],
        )
