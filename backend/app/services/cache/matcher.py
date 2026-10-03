"""
Cache Matcher for Step 31: Production-Grade Semantic Cache and Intelligent Reuse Layer.

Validates exact and semantic compatibility across authorized scopes, prompt versions,
model configurations, context/artifact/graph/memory fingerprints, and policy constraints.
Semantic similarity alone is NEVER sufficient for reuse.
"""
from typing import Optional, Tuple
import logging

from backend.app.services.cache.constants import (
    CacheNamespace,
    CacheStatus,
)
from backend.app.services.cache.models import CacheEntry
from backend.app.services.cache.schemas import (
    CacheLookupRequest,
    CachePolicyConfig,
)

logger = logging.getLogger(__name__)


class CacheMatcher:
    """
    Deterministic compatibility verification engine for candidate cache entries.
    """

    @staticmethod
    def is_scope_compatible(
        candidate: CacheEntry,
        request: CacheLookupRequest,
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify tenant, workspace, project, and user isolation boundaries.
        """
        if candidate.organization_id != request.organization_id:
            return False, "Organization scope mismatch"

        if candidate.workspace_id != request.workspace_id:
            return False, "Workspace scope mismatch"

        if candidate.namespace == CacheNamespace.PROJECT.value:
            if not request.project_id or candidate.project_id != request.project_id:
                return False, "Project scope mismatch"

        if candidate.namespace == CacheNamespace.USER.value:
            if not request.user_id or candidate.user_id != request.user_id:
                return False, "User scope mismatch"

        return True, None

    @staticmethod
    def is_prompt_compatible(
        candidate: CacheEntry,
        request: CacheLookupRequest,
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify prompt version compatibility (STEP 28 integration).
        Published prompt changes must not reuse stale prompt outputs.
        """
        if request.prompt_version_id is not None:
            if candidate.prompt_version_id != request.prompt_version_id:
                return False, f"Prompt version mismatch: {candidate.prompt_version_id} != {request.prompt_version_id}"
        elif candidate.prompt_version_id is not None:
            # Candidate was generated under a specific prompt version, but lookup did not specify it
            return False, "Candidate has pinned prompt version but request has none"

        if request.prompt_id is not None and candidate.prompt_id != request.prompt_id:
            return False, f"Prompt ID mismatch: {candidate.prompt_id} != {request.prompt_id}"

        return True, None

    @staticmethod
    def is_model_compatible(
        candidate: CacheEntry,
        request: CacheLookupRequest,
        policy: CachePolicyConfig,
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify model requirements. By default, requires identical model/provider.
        """
        if not request.model_id:
            return True, None

        if not policy.allow_cross_model_cache:
            if candidate.model_id and candidate.model_id != request.model_id:
                return False, f"Model mismatch: {candidate.model_id} != {request.model_id}"
            if (
                request.model_provider
                and candidate.model_provider
                and candidate.model_provider != request.model_provider
            ):
                return False, f"Model provider mismatch: {candidate.model_provider} != {request.model_provider}"
        else:
            # Cross-model allowed only if candidate model is defined
            if not candidate.model_id:
                return False, "Candidate model undefined for cross-model reuse"

        return True, None

    @staticmethod
    def is_execution_config_compatible(
        candidate: CacheEntry,
        expected_config_hash: Optional[str],
    ) -> Tuple[bool, Optional[str]]:
        """Verify execution parameters (temperature, max_tokens, response_format, tools)."""
        if candidate.execution_config_hash != expected_config_hash:
            return False, "Execution configuration mismatch"
        return True, None

    @staticmethod
    def is_context_compatible(
        candidate: CacheEntry,
        expected_context_hash: Optional[str],
    ) -> Tuple[bool, Optional[str]]:
        """Verify context items, versions, and retrieval strategy (STEP 10/18 integration)."""
        if candidate.context_hash != expected_context_hash:
            return False, "Context fingerprint mismatch"
        return True, None

    @staticmethod
    def is_artifact_compatible(
        candidate: CacheEntry,
        expected_artifact_hash: Optional[str],
    ) -> Tuple[bool, Optional[str]]:
        """Verify multimodal artifact hashes (STEP 30 integration)."""
        if candidate.artifact_hash != expected_artifact_hash:
            return False, "Multimodal artifact fingerprint mismatch"
        return True, None

    @staticmethod
    def is_graph_compatible(
        candidate: CacheEntry,
        expected_graph_hash: Optional[str],
    ) -> Tuple[bool, Optional[str]]:
        """Verify knowledge graph entities and relationship states (STEP 29 integration)."""
        if candidate.graph_snapshot_hash != expected_graph_hash:
            return False, "Knowledge graph snapshot mismatch"
        return True, None

    @staticmethod
    def is_memory_compatible(
        candidate: CacheEntry,
        expected_memory_hash: Optional[str],
    ) -> Tuple[bool, Optional[str]]:
        """Verify user/workspace memory state (STEP 19 integration)."""
        if candidate.memory_snapshot_hash != expected_memory_hash:
            return False, "Memory snapshot mismatch"
        return True, None

    @classmethod
    def validate_compatibility(
        cls,
        candidate: CacheEntry,
        request: CacheLookupRequest,
        policy: CachePolicyConfig,
        execution_config_hash: Optional[str],
        context_hash: Optional[str],
        artifact_hash: Optional[str],
        graph_hash: Optional[str],
        memory_hash: Optional[str],
    ) -> Tuple[bool, Optional[str]]:
        """
        Comprehensive evaluation of all compatibility dimensions.
        Returns (True, None) if completely compatible, or (False, reason) on failure.
        """
        if candidate.status != CacheStatus.ACTIVE.value:
            return False, f"Entry status is {candidate.status}"

        # 1. Authorized Scope
        scope_ok, reason = cls.is_scope_compatible(candidate, request)
        if not scope_ok:
            return False, reason

        # 2. Prompt Version
        prompt_ok, reason = cls.is_prompt_compatible(candidate, request)
        if not prompt_ok:
            return False, reason

        # 3. Model Requirements
        model_ok, reason = cls.is_model_compatible(candidate, request, policy)
        if not model_ok:
            return False, reason

        # 4. Execution Config
        exec_ok, reason = cls.is_execution_config_compatible(candidate, execution_config_hash)
        if not exec_ok:
            return False, reason

        # 5. Context Hash
        ctx_ok, reason = cls.is_context_compatible(candidate, context_hash)
        if not ctx_ok:
            return False, reason

        # 6. Artifact Hash
        art_ok, reason = cls.is_artifact_compatible(candidate, artifact_hash)
        if not art_ok:
            return False, reason

        # 7. Knowledge Graph Hash
        graph_ok, reason = cls.is_graph_compatible(candidate, graph_hash)
        if not graph_ok:
            return False, reason

        # 8. Memory Hash
        mem_ok, reason = cls.is_memory_compatible(candidate, memory_hash)
        if not mem_ok:
            return False, reason

        return True, None
