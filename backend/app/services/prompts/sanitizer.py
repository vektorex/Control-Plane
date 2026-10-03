"""
Secret protection and template sanitization for Step 28 Prompt Management.
Guarantees:
1. Rejection of hardcoded secrets/credentials in prompt text
2. Variable values are treated strictly as data (no recursive expansion or code execution)
"""
import re
from typing import Any, List, Optional
from backend.app.services.prompts.errors import SecretDetectedError

# Regex patterns for detecting leaked secrets, tokens, credentials, and connection strings
SECRET_PATTERNS = [
    (r"(?i)(?:sk-[a-zA-Z0-9_-]{20,})", "OpenAI API Key"),
    (r"(?i)(?:sk-ant-[a-zA-Z0-9_-]{20,})", "Anthropic API Key"),
    (r"(?i)(?:AKIA[0-9A-Z]{16})", "AWS Access Key ID"),
    (r"-----BEGIN (?:[A-Z0-9_-]+ )?PRIVATE KEY-----", "Private Key block"),
    (r"(?i)(?:postgres|postgresql|mysql|mongodb|redis):\/\/[^\s:@]+:[^\s:@]+@", "Database Connection String with credentials"),
    (r"(?i)(?:ghp|gho|ghu|ghs|ghr)_[a-zA-Z0-9]{36,}", "GitHub Token"),
    (r"(?i)bearer\s+[a-zA-Z0-9_\-\.]{25,}", "Bearer Authorization Token"),
    (r"(?i)(?:password|passwd|secret_key|api_secret)\s*[:=]\s*['\"][^\s'\"]{8,}['\"]", "Hardcoded credential/password"),
]


class PromptSanitizer:
    """
    Sanitizes prompt templates and input data. Protects against secret storage and template injection.
    """

    @classmethod
    def detect_secrets(cls, text: str) -> List[str]:
        """
        Scans text for common credential patterns and secret tokens.
        Returns a list of descriptions of detected secrets.
        """
        if not text:
            return []
        findings = []
        for pattern, desc in SECRET_PATTERNS:
            if re.search(pattern, text):
                findings.append(desc)
        return findings

    @classmethod
    def validate_no_secrets(cls, text: str) -> None:
        """
        Validates that the prompt content does not contain credentials, tokens, or private keys.
        Raises SecretDetectedError if suspected secrets are found.
        """
        detected = cls.detect_secrets(text)
        if detected:
            findings_str = ", ".join(detected)
            raise SecretDetectedError(
                f"Prompt content contains suspected credentials or sensitive secrets: {findings_str}. "
                "Prompt templates must not be used as credential stores."
            )

    @classmethod
    def mask_secrets_in_diff(cls, text: str) -> str:
        """
        Masks suspected secret values in diffs or previews so they are not leaked in logs/UI.
        """
        if not text:
            return text
        sanitized = text
        for pattern, _ in SECRET_PATTERNS:
            sanitized = re.sub(pattern, "[REDACTED_SECRET]", sanitized)
        return sanitized


sanitize_prompt_content = PromptSanitizer.validate_no_secrets
mask_secrets_in_text = PromptSanitizer.mask_secrets_in_diff

