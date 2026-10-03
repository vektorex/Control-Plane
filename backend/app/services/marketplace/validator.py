"""
Marketplace Package Validator.
Step 38: AI Workflow Marketplace, Versioned Templates & Extension Ecosystem.
"""
import re
from typing import Any, Dict, List, Tuple
from backend.app.services.marketplace.exceptions import PackageValidationError

# Semantic version regex
SEMVER_REGEX = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$")

# Disallowed executable expressions
CODE_PATTERNS = [
    re.compile(r"__import__", re.IGNORECASE),
    re.compile(r"subprocess", re.IGNORECASE),
    re.compile(r"eval\s*\(", re.IGNORECASE),
    re.compile(r"exec\s*\(", re.IGNORECASE),
    re.compile(r"os\.system", re.IGNORECASE),
    re.compile(r"child_process", re.IGNORECASE),
    re.compile(r"<script[\s>]", re.IGNORECASE),
    re.compile(r"\{\{.*__.*\}\}", re.IGNORECASE),
]

ALLOWED_COMPONENT_TYPES = {
    "workflow",
    "workflow_step",
    "prompt",
    "prompt_version",
    "evaluation_dataset",
    "evaluation_case",
    "task_template",
    "tool_definition",
    "connector_template",
    "policy_template",
    "ui_metadata",
}

ALLOWED_VARIABLE_TYPES = {"string", "integer", "number", "boolean", "enum", "object"}


class PackageValidator:
    """Validates structural correctness, semantic versioning, schema constraints, and anti-code safety."""

    @classmethod
    def validate_version(cls, version: str) -> None:
        """Enforces Semantic Versioning (MAJOR.MINOR.PATCH)."""
        if not version or not SEMVER_REGEX.match(version):
            raise PackageValidationError(
                f"Version '{version}' is not a valid Semantic Version (MAJOR.MINOR.PATCH format required)."
            )

    @classmethod
    def validate_manifest(cls, manifest: Dict[str, Any]) -> List[str]:
        """
        Validates the complete manifest dictionary.
        Returns a list of warnings or raises PackageValidationError if invalid.
        """
        errors: List[str] = []
        warnings: List[str] = []

        if not isinstance(manifest, dict):
            raise PackageValidationError("Package manifest must be a JSON dictionary.")

        # 1. Package block
        pkg = manifest.get("package")
        if not pkg or not isinstance(pkg, dict):
            errors.append("Manifest missing required 'package' identity object.")
        else:
            if not pkg.get("name"):
                errors.append("Package missing 'name'.")
            if not pkg.get("version"):
                errors.append("Package missing 'version'.")
            else:
                try:
                    cls.validate_version(pkg["version"])
                except PackageValidationError as e:
                    errors.append(str(e))
            if not pkg.get("type"):
                errors.append("Package missing 'type'.")

        # 2. Components validation
        components = manifest.get("components", [])
        if not isinstance(components, list):
            errors.append("'components' must be a list.")
        else:
            component_ids = set()
            for idx, comp in enumerate(components):
                if not isinstance(comp, dict):
                    errors.append(f"Component at index {idx} must be an object.")
                    continue
                cid = comp.get("id") or comp.get("identifier") or comp.get("name")
                ctype = comp.get("type")
                if not cid:
                    errors.append(f"Component at index {idx} is missing an 'id' or 'identifier'.")
                elif cid in component_ids:
                    errors.append(f"Duplicate component ID '{cid}' found.")
                else:
                    component_ids.add(cid)

                if not ctype or ctype not in ALLOWED_COMPONENT_TYPES:
                    errors.append(
                        f"Component '{cid or idx}' has invalid type '{ctype}'. Allowed: {sorted(ALLOWED_COMPONENT_TYPES)}"
                    )

                # Check component definition for code execution attempts
                cls._scan_for_prohibited_content(comp.get("definition", {}), errors, prefix=f"component[{cid}].definition")

        # 3. Permissions validation
        permissions = manifest.get("permissions", [])
        if not isinstance(permissions, list):
            errors.append("'permissions' must be a list.")

        # 4. Dependencies validation
        dependencies = manifest.get("dependencies", [])
        if not isinstance(dependencies, list):
            errors.append("'dependencies' must be a list.")
        else:
            for idx, dep in enumerate(dependencies):
                if not isinstance(dep, dict) or not dep.get("identifier"):
                    errors.append(f"Dependency at index {idx} is missing an 'identifier'.")

        # 5. Configuration variables validation
        config = manifest.get("configuration", {})
        if not isinstance(config, dict):
            errors.append("'configuration' must be an object.")
        else:
            variables = config.get("variables", {})
            if isinstance(variables, dict):
                for var_name, var_def in variables.items():
                    if not isinstance(var_def, dict):
                        errors.append(f"Variable '{var_name}' definition must be an object.")
                        continue
                    vtype = var_def.get("type")
                    if vtype not in ALLOWED_VARIABLE_TYPES:
                        errors.append(
                            f"Variable '{var_name}' type '{vtype}' is unsupported. Allowed: {sorted(ALLOWED_VARIABLE_TYPES)}"
                        )

        # 6. Global anti-code scan
        cls._scan_for_prohibited_content(manifest, errors, prefix="manifest")

        if errors:
            raise PackageValidationError(
                f"Package manifest validation failed with {len(errors)} error(s).",
                validation_errors=errors,
            )

        return warnings

    @classmethod
    def _scan_for_prohibited_content(cls, obj: Any, errors: List[str], prefix: str = "") -> None:
        """Deep scan for arbitrary code or executable injection patterns."""
        if isinstance(obj, str):
            for pat in CODE_PATTERNS:
                if pat.search(obj):
                    errors.append(f"Prohibited executable expression or code pattern found at {prefix}.")
                    break
        elif isinstance(obj, dict):
            for k, v in obj.items():
                if any(pat.search(str(k)) for pat in CODE_PATTERNS):
                    errors.append(f"Prohibited code pattern in key name at {prefix}.{k}.")
                cls._scan_for_prohibited_content(v, errors, prefix=f"{prefix}.{k}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                cls._scan_for_prohibited_content(item, errors, prefix=f"{prefix}[{i}]")
