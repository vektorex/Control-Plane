"""
Version management service for Step 28: Prompt Management.
Handles version creation, immutability enforcement, publishing, deprecation, and diff comparisons.
"""
import difflib
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.prompts.constants import PromptVersionStatus
from backend.app.services.prompts.errors import (
    ImmutableVersionError,
    PromptNotFoundError,
    PromptVersionNotFoundError,
)
from backend.app.services.prompts.models import PromptVersion
from backend.app.services.prompts.repository import PromptRepository
from backend.app.services.prompts.sanitizer import PromptSanitizer
from backend.app.services.prompts.schemas import PromptDiffResponse
from backend.app.services.prompts.validator import PromptValidator


class PromptVersionService:
    """
    Manages immutable prompt versions, safe diff computation, and publishing lifecycles.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = PromptRepository(session)

    async def create_version(
        self,
        prompt_id: uuid.UUID,
        content: str,
        created_by: uuid.UUID,
        variable_schema: Optional[Dict[str, Any]] = None,
        model_requirements: Optional[Dict[str, Any]] = None,
        execution_config: Optional[Dict[str, Any]] = None,
        change_summary: Optional[str] = None,
    ) -> PromptVersion:
        """
        Creates a new draft version.
        Validates content for secrets, validates variable schema and execution config.
        """
        prompt = await self.repo.get_prompt_by_id(prompt_id, include_relations=False)
        if not prompt:
            raise PromptNotFoundError(f"Prompt {prompt_id} not found.")

        # 1. Guard against storing secrets
        PromptSanitizer.validate_no_secrets(content)

        # 2. Validate template syntax and variables
        PromptValidator.extract_variables_from_content(content)

        # 3. Validate variable schema if supplied
        if variable_schema:
            PromptValidator.validate_variable_schema(variable_schema)

        # 4. Validate execution config if supplied
        if execution_config:
            PromptValidator.validate_execution_config(execution_config)

        # 5. Persist draft version
        return await self.repo.create_version(
            prompt_id=prompt_id,
            content=content,
            created_by=created_by,
            variable_schema=variable_schema or {},
            model_requirements=model_requirements,
            execution_config=execution_config,
            change_summary=change_summary,
        )

    async def publish_version(self, version_id: uuid.UUID) -> PromptVersion:
        """
        Publishes a version making it permanently immutable.
        """
        version = await self.repo.get_version_by_id(version_id)
        if not version:
            raise PromptVersionNotFoundError(f"Version {version_id} not found.")

        # Re-verify no secrets exist before publication
        PromptSanitizer.validate_no_secrets(version.content)

        return await self.repo.publish_version(version_id)

    async def deprecate_version(self, version_id: uuid.UUID) -> PromptVersion:
        """
        Marks a published version as deprecated.
        """
        version = await self.repo.get_version_by_id(version_id)
        if not version:
            raise PromptVersionNotFoundError(f"Version {version_id} not found.")

        version.status = PromptVersionStatus.DEPRECATED.value
        await self.session.flush()
        return version

    async def compare_versions(
        self,
        prompt_id: uuid.UUID,
        from_version_number: int,
        to_version_number: int,
    ) -> PromptDiffResponse:
        """
        Computes a safe diff between two versions of a prompt.
        Masks any potential secrets and reports text diffs, schema changes, and config differences.
        """
        v_from = await self.repo.get_version_by_number(prompt_id, from_version_number)
        if not v_from:
            raise PromptVersionNotFoundError(f"Version {from_version_number} not found for prompt {prompt_id}.")

        v_to = await self.repo.get_version_by_number(prompt_id, to_version_number)
        if not v_to:
            raise PromptVersionNotFoundError(f"Version {to_version_number} not found for prompt {prompt_id}.")

        content_from = PromptSanitizer.mask_secrets_in_diff(v_from.content)
        content_to = PromptSanitizer.mask_secrets_in_diff(v_to.content)

        from_lines = [line + "\n" for line in content_from.splitlines()]
        to_lines = [line + "\n" for line in content_to.splitlines()]

        diff_gen = list(difflib.unified_diff(
            from_lines,
            to_lines,
            fromfile=f"v{v_from.version_number}",
            tofile=f"v{v_to.version_number}",
        ))
        diff_unified = "".join(diff_gen)
        diff_lines = [line.rstrip("\r\n") for line in diff_gen]

        added_lines = [
            line[1:].rstrip("\r\n")
            for line in diff_lines
            if line.startswith("+") and not line.startswith("+++")
        ]
        removed_lines = [
            line[1:].rstrip("\r\n")
            for line in diff_lines
            if line.startswith("-") and not line.startswith("---")
        ]

        # Schema changes
        schema_changes = {
            "from": v_from.variable_schema or {},
            "to": v_to.variable_schema or {},
        }

        # Config changes
        config_changes = {
            "from": v_from.execution_config or {},
            "to": v_to.execution_config or {},
        }

        # Model reqs changes
        model_req_changes = {
            "from": v_from.model_requirements or {},
            "to": v_to.model_requirements or {},
        }

        return PromptDiffResponse(
            prompt_id=prompt_id,
            from_version_number=v_from.version_number,
            to_version_number=v_to.version_number,
            diff_unified=diff_unified,
            diff_lines=diff_lines,
            added_lines=added_lines,
            removed_lines=removed_lines,
            variable_schema_changes=schema_changes,
            execution_config_changes=config_changes,
            model_requirements_changes=model_req_changes,
        )
