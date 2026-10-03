"""
Sanitizer for Step 31: Production-Grade Semantic Cache and Intelligent Reuse Layer.
Redacts API keys, credentials, tokens, hidden prompts, and chain-of-thought before cache admission.
Never mutates original run or task outputs.
"""
import copy
import re
from typing import Any, Dict, List, Optional


class CacheSanitizer:
    """
    Sanitizes responses and metadata before admission into the persistent cache.
    Guarantees no sensitive secrets, private credentials, or internal reasoning leak across lookups.
    """

    SECRET_PATTERNS = [
        # OpenAI / Anthropic / Common LLM API keys
        re.compile(r"sk-[a-zA-Z0-9_-]{20,}", re.IGNORECASE),
        re.compile(r"ant-[a-zA-Z0-9_-]{20,}", re.IGNORECASE),
        re.compile(r"AIza[0-9A-Za-z-_]{35}", re.IGNORECASE),
        # GitHub / GitLab / Slack tokens
        re.compile(r"gh[pousr]-[a-zA-Z0-9]{36,}", re.IGNORECASE),
        re.compile(r"xox[baprs]-[0-9a-zA-Z-]{10,}", re.IGNORECASE),
        # Bearer tokens & generic authorization
        re.compile(r"(Bearer\s+)[a-zA-Z0-9_\-\.]{20,}", re.IGNORECASE),
        re.compile(r"(password[\"':\s=]+)[\"'][^\"'\s]{4,}[\"']", re.IGNORECASE),
        re.compile(r"(secret[\"':\s=]+)[\"'][^\"'\s]{4,}[\"']", re.IGNORECASE),
        re.compile(r"(private_key[\"':\s=]+)[\"'][^\"'\s]{10,}[\"']", re.IGNORECASE),
    ]

    COT_PATTERNS = [
        # Chain of thought tags and markers
        re.compile(r"<thought>.*?</thought>", re.DOTALL | re.IGNORECASE),
        re.compile(r"<thinking>.*?</thinking>", re.DOTALL | re.IGNORECASE),
        re.compile(r"<internal_reasoning>.*?</internal_reasoning>", re.DOTALL | re.IGNORECASE),
        re.compile(r"^Thinking Process:.*?(?=\n\n|\Z)", re.DOTALL | re.MULTILINE),
    ]

    SENSITIVE_METADATA_KEYS = {
        "api_key",
        "authorization",
        "cookie",
        "secret",
        "password",
        "token",
        "access_token",
        "refresh_token",
        "client_secret",
        "private_key",
        "raw_credentials",
        "webhook_secret",
        "hidden_prompt",
        "system_secret",
    }

    @classmethod
    def sanitize_text(cls, text: str) -> str:
        """
        Strips secrets and chain-of-thought from string content.
        """
        if not text:
            return ""

        cleaned = str(text)

        # 1. Strip chain of thought
        for pat in cls.COT_PATTERNS:
            cleaned = pat.sub("", cleaned).strip()

        # 2. Redact credentials and keys
        for pat in cls.SECRET_PATTERNS:
            cleaned = pat.sub("[REDACTED_SECRET]", cleaned)

        return cleaned

    @classmethod
    def sanitize_metadata(cls, meta: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Recursively scrubs sensitive keys and values from metadata dictionaries.
        """
        if not meta:
            return {}

        clean_dict = copy.deepcopy(meta)
        return cls._scrub_dict(clean_dict)

    @classmethod
    def _scrub_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        result = {}
        for k, v in data.items():
            k_lower = str(k).lower()
            if any(s in k_lower for s in cls.SENSITIVE_METADATA_KEYS):
                result[k] = "[REDACTED_SECRET]"
            elif isinstance(v, dict):
                result[k] = cls._scrub_dict(v)
            elif isinstance(v, list):
                result[k] = cls._scrub_list(v)
            elif isinstance(v, str):
                result[k] = cls.sanitize_text(v)
            else:
                result[k] = v
        return result

    @classmethod
    def _scrub_list(cls, items: List[Any]) -> List[Any]:
        result = []
        for item in items:
            if isinstance(item, dict):
                result.append(cls._scrub_dict(item))
            elif isinstance(item, list):
                result.append(cls._scrub_list(item))
            elif isinstance(item, str):
                result.append(cls.sanitize_text(item))
            else:
                result.append(item)
        return result
