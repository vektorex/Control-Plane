"""
Prompt Resolver for Step 28 Prompt Management.
Resolves runtime prompt references by:
1. Exact Version ID (PINNED)
2. Prompt Key + Environment (TRACK_RELEASE)
3. Active A/B Experiment with deterministic hashing and sticky variant assignment
Includes bounded caching of immutable published versions with invalidation hooks,
and safe fail-closed behavior for production operations.
"""
import hashlib
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.services.prompts.constants import (
    ExperimentStatus,
    PromptEnvironment,
    PromptVersionStatus,
    ReleaseStatus,
)
from backend.app.services.prompts.errors import PromptResolutionError
from backend.app.services.prompts.models import Prompt, PromptExperiment, PromptVersion
from backend.app.services.prompts.repository import PromptRepository


class ResolvedPromptTarget:
    """
    Result of resolving a logical prompt reference.
    Contains the immutable PromptVersion and resolution metadata.
    """

    def __init__(
        self,
        prompt: Optional[Prompt],
        version: PromptVersion,
        environment: Optional[str] = None,
        resolution_mode: str = "track_release",  # "pinned", "track_release", "experiment"
        experiment_id: Optional[uuid.UUID] = None,
        variant_id: Optional[uuid.UUID] = None,
        variant_label: Optional[str] = None,
        is_fallback: bool = False,
    ):
        self.prompt = prompt
        self.version = version
        self.environment = environment
        self.resolution_mode = resolution_mode
        self.experiment_id = experiment_id
        self.variant_id = variant_id
        self.variant_label = variant_label
        self.is_fallback = is_fallback

    @property
    def prompt_id(self) -> Optional[uuid.UUID]:
        return self.prompt.id if self.prompt else self.version.prompt_id

    @property
    def prompt_key(self) -> Optional[str]:
        return self.prompt.key if self.prompt else None

    @property
    def version_id(self) -> uuid.UUID:
        return self.version.id

    @property
    def version_number(self) -> int:
        return self.version.version_number

    @property
    def content(self) -> str:
        return self.version.content

    @property
    def content_hash(self) -> Optional[str]:
        return self.version.content_hash

    @property
    def execution_config(self) -> Optional[Dict[str, Any]]:
        return self.version.execution_config

    @property
    def model_requirements(self) -> Optional[Dict[str, Any]]:
        return self.version.model_requirements

    @property
    def variable_schema(self) -> Dict[str, Any]:
        return self.version.variable_schema or {}


class PromptResolver:
    """
    Runtime resolver for prompt assets across tasks, workflows, planners, and evaluators.
    """

    # In-memory bounded cache for immutable published versions: key -> (PromptVersion, timestamp)
    _version_cache: Dict[str, PromptVersion] = {}
    _cache_max_size: int = 500

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = PromptRepository(session)

    @classmethod
    def invalidate_cache(cls, prompt_id: Optional[uuid.UUID] = None) -> None:
        """
        Invalidates cached entries. If prompt_id is specified, removes matching versions.
        """
        if prompt_id is None:
            cls._version_cache.clear()
            return

        to_remove = [
            k for k, v in cls._version_cache.items()
            if getattr(v, "prompt_id", None) == prompt_id
        ]
        for k in to_remove:
            cls._version_cache.pop(k, None)

    async def resolve(
        self,
        workspace_id: uuid.UUID,
        prompt_key: Optional[str] = None,
        prompt_id: Optional[uuid.UUID] = None,
        version_id: Optional[uuid.UUID] = None,
        environment: str = PromptEnvironment.PRODUCTION.value,
        project_id: Optional[uuid.UUID] = None,
        allocation_key_value: Optional[str] = None,
        allow_fallback: bool = False,
        fallback_content: Optional[str] = None,
    ) -> ResolvedPromptTarget:
        """
        Authoritative prompt resolution logic.
        1. If version_id is provided -> PINNED resolution
        2. If prompt_key or prompt_id is provided -> TRACK_RELEASE resolution
           a. Check if an active experiment exists and allocation_key_value is present -> EXPERIMENT
           b. Else look up active PromptRelease in environment
        3. If not resolved -> Fail safe (or apply fallback if explicitly permitted for dev).
        """
        # 1. PINNED RESOLUTION
        if version_id:
            version = await self._get_cached_or_db_version(version_id)
            if not version:
                raise PromptResolutionError(f"Pinned prompt version '{version_id}' could not be resolved.")
            prompt = await self.repo.get_prompt_by_id(version.prompt_id, include_relations=False)
            return ResolvedPromptTarget(
                prompt=prompt,
                version=version,
                environment=environment,
                resolution_mode="pinned",
            )

        # 2. TRACK_RELEASE / EXPERIMENT RESOLUTION
        prompt: Optional[Prompt] = None
        if prompt_id:
            prompt = await self.repo.get_prompt_by_id(prompt_id, include_relations=True)
        elif prompt_key:
            prompt = await self.repo.get_prompt_by_key(workspace_id=workspace_id, key=prompt_key, project_id=project_id)

        if not prompt:
            if allow_fallback and fallback_content:
                logger.info(f"[PromptResolver] Prompt not found for key '{prompt_key}'. Using configured fallback.")
                return self._create_ephemeral_fallback_target(
                    prompt_key=prompt_key or "fallback",
                    fallback_content=fallback_content,
                    environment=environment,
                )
            raise PromptResolutionError(
                f"Prompt could not be resolved for key='{prompt_key}', id='{prompt_id}' in workspace='{workspace_id}'."
            )

        # 2a. Check for active experiment
        if allocation_key_value:
            active_exp = await self.repo.get_active_experiment_for_prompt(prompt.id)
            if active_exp and active_exp.variants:
                assigned_target = await self._resolve_experiment_variant(active_exp, allocation_key_value)
                if assigned_target:
                    return assigned_target

        # 2b. Release Environment Resolution
        release = await self.repo.get_active_release(prompt.id, environment=environment)
        if not release or not release.version:
            # If no active release in requested environment:
            if allow_fallback and fallback_content:
                logger.warning(
                    f"[PromptResolver] No active release for prompt '{prompt.key}' in '{environment}'. Using fallback."
                )
                return self._create_ephemeral_fallback_target(
                    prompt_key=prompt.key,
                    fallback_content=fallback_content,
                    environment=environment,
                )
            raise PromptResolutionError(
                f"No active release found for prompt '{prompt.key}' ({prompt.id}) in environment '{environment}'."
            )

        version = release.version
        return ResolvedPromptTarget(
            prompt=prompt,
            version=version,
            environment=environment,
            resolution_mode="track_release",
        )

    async def _get_cached_or_db_version(self, version_id: uuid.UUID) -> Optional[PromptVersion]:
        """
        Retrieves a version with bounded in-memory caching for published immutable records.
        """
        cache_key = str(version_id)
        if cache_key in self._version_cache:
            return self._version_cache[cache_key]

        version = await self.repo.get_version_by_id(version_id)
        if version and version.status == PromptVersionStatus.PUBLISHED.value:
            if len(self._version_cache) >= self._cache_max_size:
                # Evict oldest
                first_key = next(iter(self._version_cache))
                self._version_cache.pop(first_key, None)
            self._version_cache[cache_key] = version

        return version

    @staticmethod
    def select_variant_for_key(
        experiment_id: Any,
        variants: List[Any],
        allocation_key_value: str,
    ) -> Any:
        """
        Pure, deterministic variant selection using sha256 hash modulo weights.
        """
        if not variants:
            return None
        sorted_variants = sorted(variants, key=lambda v: v.get("label") if isinstance(v, dict) else getattr(v, "label", str(v)))
        hash_input = f"{experiment_id}:{allocation_key_value}".encode("utf-8")
        hash_digest = hashlib.sha256(hash_input).hexdigest()
        hash_int = int(hash_digest[:16], 16)

        total_weight = sum((v.get("allocation_weight") if isinstance(v, dict) else getattr(v, "allocation_weight", 1.0)) for v in sorted_variants)
        if total_weight <= 0:
            total_weight = 1.0

        bucket = (hash_int % 10000) / 10000.0 * total_weight
        cum_weight = 0.0
        selected = sorted_variants[-1]
        for v in sorted_variants:
            w = v.get("allocation_weight") if isinstance(v, dict) else getattr(v, "allocation_weight", 1.0)
            cum_weight += w
            if bucket <= cum_weight:
                selected = v
                break
        return selected

    async def _resolve_experiment_variant(
        self,
        experiment: PromptExperiment,
        allocation_key_value: str,
    ) -> Optional[ResolvedPromptTarget]:
        """
        Deterministically assigns an experiment variant using stable sha256 hashing.
        Persists sticky assignment in PromptExperimentAssignment.
        """
        variants = experiment.variants
        if not variants:
            return None

        selected_variant = self.select_variant_for_key(experiment.id, variants, allocation_key_value)

        # Persist assignment in repository
        assignment = await self.repo.get_or_create_assignment(
            experiment_id=experiment.id,
            allocation_key_value=allocation_key_value,
            variant_id=selected_variant.id,
            version_id=selected_variant.prompt_version_id,
        )

        version = selected_variant.version
        if not version:
            version = await self.repo.get_version_by_id(assignment.assigned_version_id)

        if not version:
            return None

        return ResolvedPromptTarget(
            prompt=experiment.prompt,
            version=version,
            environment="experiment",
            resolution_mode="experiment",
            experiment_id=experiment.id,
            variant_id=selected_variant.id,
            variant_label=selected_variant.label,
        )

    def _create_ephemeral_fallback_target(
        self,
        prompt_key: str,
        fallback_content: str,
        environment: str,
    ) -> ResolvedPromptTarget:
        """
        Creates an in-memory safe fallback target for local development or non-critical tests.
        """
        hash_val = hashlib.sha256(fallback_content.encode("utf-8")).hexdigest()
        ephemeral_version = PromptVersion(
            id=uuid.uuid4(),
            prompt_id=uuid.uuid4(),
            version_number=0,
            status=PromptVersionStatus.PUBLISHED.value,
            content=fallback_content,
            variable_schema={},
            content_hash=hash_val,
            created_by=uuid.uuid4(),
        )
        return ResolvedPromptTarget(
            prompt=None,
            version=ephemeral_version,
            environment=environment,
            resolution_mode="fallback",
            is_fallback=True,
        )
