"""
Prompt Release and Environment Management for Step 28 Prompt Management.
Enforces promotion lifecycles (development -> staging -> production),
transactional rollback, immutable history tracking, HITL approval hooks, and event publishing.
"""
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.services.events.constants import ActorType, AggregateType, SystemEventType
from backend.app.services.events.publisher import EventPublisher
from backend.app.services.events.schemas import EventPublishRequest
from backend.app.services.notifications.dispatcher import NotificationEventBus
from backend.app.services.prompts.constants import (
    ENVIRONMENT_PROMOTION_ORDER,
    PromptEnvironment,
    PromptVersionStatus,
)
from backend.app.services.prompts.errors import (
    ImmutableVersionError,
    PromotionNotAllowedError,
    PromptNotFoundError,
    PromptVersionNotFoundError,
)
from backend.app.services.prompts.models import PromptRelease
from backend.app.services.prompts.repository import PromptRepository


class PromptReleaseService:
    """
    Manages release bindings, promotions, rollbacks, and release transitions across environments.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = PromptRepository(session)
        self.event_publisher = EventPublisher(session)

    async def release_version(
        self,
        prompt_id: uuid.UUID,
        environment: str,
        version_id: uuid.UUID,
        released_by: uuid.UUID,
        is_automated_actor: bool = False,
    ) -> PromptRelease:
        """
        Binds a prompt version to an environment.
        Strictly forbids autonomous AI models from releasing or promoting prompts.
        """
        if is_automated_actor:
            raise PromotionNotAllowedError(
                "Autonomous AI agents and LLMs are strictly forbidden from publishing or promoting prompt releases."
            )

        prompt = await self.repo.get_prompt_by_id(prompt_id, include_relations=False)
        if not prompt:
            raise PromptNotFoundError(f"Prompt {prompt_id} not found.")

        version = await self.repo.get_version_by_id(version_id)
        if not version or version.prompt_id != prompt_id:
            raise PromptVersionNotFoundError(f"Version {version_id} does not belong to prompt {prompt_id}.")

        if version.status != PromptVersionStatus.PUBLISHED.value:
            raise ImmutableVersionError(
                f"Version v{version.version_number} must be published before it can be released to an environment."
            )

        # Validate environment value
        valid_envs = [e.value for e in PromptEnvironment]
        if environment not in valid_envs:
            raise PromotionNotAllowedError(
                f"Invalid environment '{environment}'. Valid environments: {valid_envs}"
            )

        # Perform transactional release creation (supersedes previous active)
        release = await self.repo.create_release(
            prompt_id=prompt_id,
            environment=environment,
            version_id=version_id,
            released_by=released_by,
        )

        # Invalidate resolver cache
        from backend.app.services.prompts.resolver import PromptResolver
        PromptResolver.invalidate_cache(prompt_id)

        # Publish release event via Step 26 EventPublisher
        try:
            await self.event_publisher.publish(
                EventPublishRequest(
                    workspace_id=prompt.workspace_id,
                    project_id=prompt.project_id,
                    event_type=SystemEventType.PROMPT_RELEASE_CHANGED.value,
                    aggregate_type=AggregateType.PROMPT.value,
                    aggregate_id=str(prompt.id),
                    actor_type=ActorType.USER.value,
                    actor_id=str(released_by),
                    payload={
                        "prompt_id": str(prompt.id),
                        "prompt_key": prompt.key,
                        "environment": environment,
                        "version_id": str(version.id),
                        "version_number": version.version_number,
                        "previous_version_id": str(release.previous_version_id) if release.previous_version_id else None,
                    },
                    metadata={"environment": environment},
                )
            )
        except Exception as e:
            logger.warning(f"[PromptReleaseService] Failed to publish release event: {e}")

        # Send notification via Step 25 NotificationEventBus
        try:
            await NotificationEventBus.publish(
                {
                    "workspace_id": prompt.workspace_id,
                    "event_type": "prompt.released",
                    "title": f"Prompt Released: {prompt.name} ({environment.upper()})",
                    "body": f"Version v{version.version_number} was released to {environment} by user {released_by}.",
                    "metadata": {
                        "prompt_id": str(prompt.id),
                        "prompt_key": prompt.key,
                        "environment": environment,
                        "version_number": version.version_number,
                    },
                },
                session=self.session,
            )
        except Exception as e:
            logger.warning(f"[PromptReleaseService] Failed to publish notification: {e}")

        return release

    async def rollback(
        self,
        prompt_id: uuid.UUID,
        environment: str,
        released_by: uuid.UUID,
        target_version_id: Optional[uuid.UUID] = None,
    ) -> PromptRelease:
        """
        Rolls back an environment to a previous version.
        Creates a new release transition record to preserve immutable history.
        """
        prompt = await self.repo.get_prompt_by_id(prompt_id, include_relations=False)
        if not prompt:
            raise PromptNotFoundError(f"Prompt {prompt_id} not found.")

        rollback_record = await self.repo.rollback_release(
            prompt_id=prompt_id,
            environment=environment,
            released_by=released_by,
            target_version_id=target_version_id,
        )

        # Invalidate resolver cache
        from backend.app.services.prompts.resolver import PromptResolver
        PromptResolver.invalidate_cache(prompt_id)

        # Publish rollback event via Step 26 EventPublisher
        try:
            await self.event_publisher.publish(
                EventPublishRequest(
                    workspace_id=prompt.workspace_id,
                    project_id=prompt.project_id,
                    event_type=SystemEventType.PROMPT_ROLLED_BACK.value,
                    aggregate_type=AggregateType.PROMPT.value,
                    aggregate_id=str(prompt.id),
                    actor_type=ActorType.USER.value,
                    actor_id=str(released_by),
                    payload={
                        "prompt_id": str(prompt.id),
                        "prompt_key": prompt.key,
                        "environment": environment,
                        "version_id": str(rollback_record.version_id),
                        "previous_version_id": str(rollback_record.previous_version_id),
                    },
                    metadata={"environment": environment, "action": "rollback"},
                )
            )
        except Exception as e:
            logger.warning(f"[PromptReleaseService] Failed to publish rollback event: {e}")

        # Send notification via Step 25 NotificationEventBus
        try:
            await NotificationEventBus.publish(
                {
                    "workspace_id": prompt.workspace_id,
                    "event_type": "prompt.rolled_back",
                    "title": f"Prompt Rolled Back: {prompt.name} ({environment.upper()})",
                    "body": f"Prompt '{prompt.key}' was rolled back in {environment}.",
                    "metadata": {
                        "prompt_id": str(prompt.id),
                        "prompt_key": prompt.key,
                        "environment": environment,
                    },
                },
                session=self.session,
            )
        except Exception as e:
            logger.warning(f"[PromptReleaseService] Failed to publish rollback notification: {e}")

        return rollback_record
