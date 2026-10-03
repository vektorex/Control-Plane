"""
Variable and execution configuration validator for Step 28 Prompt Management.
Enforces:
1. Strict, non-executable template syntax (only {{namespace.variable_name}})
2. Rejection of arbitrary language expressions, method calls, eval, and imports
3. Strong typing against variable_schema
4. Safe bounds on execution configuration (temperature, tokens, formats)
"""
import json
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from backend.app.services.prompts.constants import (
    ALLOWED_VARIABLE_NAMESPACES,
    SUPPORTED_VARIABLE_TYPES,
)
from backend.app.services.prompts.errors import (
    ExecutionConfigPolicyError,
    TemplateInjectionError,
    VariableValidationError,
)

# Regex matching clean {{ namespace.var_name }} tags
VARIABLE_TAG_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_\.]+)\s*\}\}")
# Regex matching illegal execution attempts strictly inside double-braces: (), [], ;, =, quotes, etc.
ILLEGAL_EXPRESSION_PATTERN = re.compile(r"\{\{[^}]*[()\[\];='\"`][^}]*\}\}")


class PromptValidator:
    """
    Validates template structure, variable namespaces, variable values against schemas,
    and model execution configurations.
    """

    @classmethod
    def extract_variables_from_content(cls, content: str) -> List[str]:
        """
        Extracts variable reference paths from a prompt template string.
        Guarantees that no illegal expressions or code invocations exist.
        """
        if not content:
            return []

        # Check for illegal syntax attempts
        if ILLEGAL_EXPRESSION_PATTERN.search(content):
            raise TemplateInjectionError(
                "Invalid template syntax: Arbitrary expressions, method calls, array indexers, "
                "or code execution syntax are forbidden in prompt templates. "
                "Only safe {{namespace.variable_name}} syntax is supported."
            )

        found_vars = []
        for match in VARIABLE_TAG_PATTERN.finditer(content):
            var_name = match.group(1).strip()
            parts = var_name.split(".")
            root_namespace = parts[0]

            if root_namespace not in ALLOWED_VARIABLE_NAMESPACES:
                raise TemplateInjectionError(
                    f"Forbidden namespace '{root_namespace}' in variable '{{{{{var_name}}}}}'. "
                    f"Allowed namespaces are: {sorted(list(ALLOWED_VARIABLE_NAMESPACES))}"
                )
            found_vars.append(var_name)

        return list(dict.fromkeys(found_vars))

    @classmethod
    def validate_variable_schema(cls, schema: Dict[str, Any]) -> None:
        """
        Validates the structure of a PromptVersion's variable_schema definition.
        """
        if not isinstance(schema, dict):
            raise VariableValidationError("variable_schema must be a dictionary.")

        for var_name, rules in schema.items():
            if not isinstance(rules, dict):
                raise VariableValidationError(f"Schema definition for variable '{var_name}' must be an object.")

            parts = var_name.split(".")
            root_namespace = parts[0]
            if root_namespace not in ALLOWED_VARIABLE_NAMESPACES:
                raise VariableValidationError(
                    f"Variable '{var_name}' uses disallowed root namespace '{root_namespace}'. "
                    f"Allowed namespaces are: {sorted(list(ALLOWED_VARIABLE_NAMESPACES))}"
                )

            v_type = rules.get("type", "string")
            if v_type not in SUPPORTED_VARIABLE_TYPES:
                raise VariableValidationError(
                    f"Variable '{var_name}' has unsupported type '{v_type}'. "
                    f"Supported types are: {sorted(list(SUPPORTED_VARIABLE_TYPES))}"
                )

    @classmethod
    def validate_variables_against_schema(
        cls,
        schema: Dict[str, Any],
        variables: Dict[str, Any],
    ) -> Tuple[bool, List[str]]:
        """
        Validates supplied runtime variables against the version's schema.
        Returns (is_valid, list_of_error_messages).
        """
        errors = []
        # Flatten input variables if nested or keep as dotted keys
        resolved_dict = cls._flatten_dict(variables)

        for var_name, rule in (schema or {}).items():
            is_required = rule.get("required", False)
            expected_type = rule.get("type", "string")

            if var_name not in resolved_dict:
                if is_required:
                    errors.append(f"Missing required variable: '{var_name}'")
                continue

            val = resolved_dict[var_name]

            # Type checking
            if expected_type == "string":
                if not isinstance(val, str):
                    errors.append(f"Variable '{var_name}' must be a string, got {type(val).__name__}")
            elif expected_type == "number":
                if isinstance(val, bool) or not isinstance(val, (int, float)):
                    errors.append(f"Variable '{var_name}' must be a number, got {type(val).__name__}")
            elif expected_type == "boolean":
                if not isinstance(val, bool):
                    errors.append(f"Variable '{var_name}' must be a boolean, got {type(val).__name__}")
            elif expected_type == "string_array":
                if not isinstance(val, list) or not all(isinstance(x, str) for x in val):
                    errors.append(f"Variable '{var_name}' must be a list of strings")
            elif expected_type == "json":
                if not isinstance(val, (dict, list)):
                    try:
                        json.loads(str(val))
                    except Exception:
                        errors.append(f"Variable '{var_name}' must be a valid JSON object or list")

        return len(errors) == 0, errors

    @classmethod
    def validate_execution_config(cls, config: Optional[Dict[str, Any]]) -> None:
        """
        Validates optional execution parameters.
        Prompt configs cannot override provider boundaries or safety policies.
        """
        if not config:
            return

        if not isinstance(config, dict):
            raise ExecutionConfigPolicyError("execution_config must be an object")

        if "temperature" in config:
            temp = config["temperature"]
            if not isinstance(temp, (int, float)) or temp < 0.0 or temp > 2.0:
                raise ExecutionConfigPolicyError("temperature must be a float between 0.0 and 2.0")

        if "max_output_tokens" in config:
            tokens = config["max_output_tokens"]
            if not isinstance(tokens, int) or tokens <= 0 or tokens > 32768:
                raise ExecutionConfigPolicyError("max_output_tokens must be an integer between 1 and 32768")

        if "response_format" in config:
            rf = config["response_format"]
            if rf is not None and not isinstance(rf, dict):
                raise ExecutionConfigPolicyError("response_format must be an object (e.g. {'type': 'json_object'})")

    @classmethod
    def _flatten_dict(cls, d: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
        """
        Flattens nested dictionaries into dotted keys, while also preserving top-level dotted keys.
        """
        items: Dict[str, Any] = {}
        if not isinstance(d, dict):
            return items

        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            items[new_key] = v
            if isinstance(v, dict):
                items.update(cls._flatten_dict(v, new_key, sep=sep))
        return items


validate_prompt_content = PromptValidator.extract_variables_from_content
validate_variable_schema = PromptValidator.validate_variable_schema

