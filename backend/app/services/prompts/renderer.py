"""
Deterministic Prompt Renderer for Step 28 Prompt Management.
Renders prompt templates with safe, single-pass data substitution.
Never interprets variable values recursively as template code.
"""
import hashlib
import json
import re
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.services.prompts.errors import VariableValidationError
from backend.app.services.prompts.validator import PromptValidator, VARIABLE_TAG_PATTERN


class RenderedPrompt(BaseModel):
    """
    Contract returned by deterministic prompt rendering.
    """
    prompt_id: Optional[uuid.UUID] = None
    version_id: Optional[uuid.UUID] = None
    rendered_content: str
    variables_used: List[str] = Field(default_factory=list)
    content_hash: str
    estimated_tokens: int


class PromptRenderer:
    """
    Safe deterministic template renderer.
    """

    @classmethod
    def render(
        cls,
        content: str,
        variables: Optional[Dict[str, Any]] = None,
        schema: Optional[Dict[str, Any]] = None,
        prompt_id: Optional[uuid.UUID] = None,
        version_id: Optional[uuid.UUID] = None,
    ) -> RenderedPrompt:
        """
        Renders the prompt template safely.
        Validates variables against schema if schema is provided.
        Ensures strict single-pass replacement so that variable values containing
        '{{...}}' remain literal strings and are never evaluated.
        """
        variables = variables or {}
        schema = schema or {}

        # 1. Validate variables against schema if schema is defined
        if schema:
            is_valid, errors = PromptValidator.validate_variables_against_schema(schema, variables)
            if not is_valid:
                raise VariableValidationError(f"Variable validation failed: {'; '.join(errors)}")

        # 2. Extract needed variables and validate template syntax
        PromptValidator.extract_variables_from_content(content)

        # 3. Flatten variables dictionary for hierarchical dotted lookups
        flattened_vars = PromptValidator._flatten_dict(variables)

        # Also support direct lookups for nested dicts if not flattened
        variables_used: List[str] = []

        def _resolve_variable(match: re.Match) -> str:
            var_name = match.group(1).strip()
            variables_used.append(var_name)

            if var_name in flattened_vars:
                val = flattened_vars[var_name]
            elif var_name in variables:
                val = variables[var_name]
            else:
                # Missing optional variable: check if in schema with default or leave empty/token
                if schema and schema.get(var_name, {}).get("required", False):
                    raise VariableValidationError(f"Missing required variable: '{var_name}'")
                # Return empty string for missing non-required variable
                return ""

            # Format value as data string
            if isinstance(val, (dict, list)):
                return json.dumps(val, indent=2 if isinstance(val, dict) and len(val) > 2 else None)
            elif isinstance(val, bool):
                return "true" if val else "false"
            elif val is None:
                return ""
            else:
                return str(val)

        # Single-pass substitution (treats inserted strings purely as literal data)
        rendered_content = VARIABLE_TAG_PATTERN.sub(_resolve_variable, content)

        # Generate deterministic sha256 hash of the rendered result
        content_hash = hashlib.sha256(rendered_content.encode("utf-8")).hexdigest()

        # Token estimate: approx 4 characters per token
        estimated_tokens = max(1, len(rendered_content) // 4) if rendered_content else 0

        return RenderedPrompt(
            prompt_id=prompt_id,
            version_id=version_id,
            rendered_content=rendered_content,
            variables_used=list(dict.fromkeys(variables_used)),
            content_hash=content_hash,
            estimated_tokens=estimated_tokens,
        )


default_prompt_renderer = PromptRenderer

