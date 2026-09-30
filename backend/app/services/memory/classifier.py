"""
Deterministic and LLM-assisted classification of candidate memories.
Enforces security, prevents credential leaks, and detects toxic prompt injections.
"""
import re
from typing import List, Optional
from pydantic import BaseModel, Field

from backend.app.services.memory.policies import MemoryPolicy
from backend.app.services.memory.sanitizer import SecretDetector


class ClassificationResult(BaseModel):
    status: str = Field(..., description="'allowed', 'candidate', 'rejected', 'requires_confirmation'")
    reason: str
    detected_flags: List[str] = Field(default_factory=list)
    confidence: float = 1.0


# Regexes for highly sensitive personal data and malicious prompt injection commands
SENSITIVE_PII_PATTERNS = [
    ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("credit_card", re.compile(r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12})\b")),
]

MALICIOUS_INJECTION_PATTERNS = [
    ("system_prompt_override", re.compile(r"(?i)\bignore (?:all )?(?:previous|prior) (?:instructions|rules|prompts)\b")),
    ("jailbreak_marker", re.compile(r"(?i)\byou are now (?:dan|unrestricted|godmode|jailbroken)\b")),
    ("exfiltration_command", re.compile(r"(?i)\b(?:curl|wget|fetch)\s+https?:\/\/[^\s]+\s+-(?:d|F|X POST)\b")),
]


class MemoryClassifier:
    """
    Evaluates memory candidates deterministically before considering persistence.
    """

    @classmethod
    def classify(
        cls,
        title: str,
        content: str,
        source_type: str = "explicit_user",
    ) -> ClassificationResult:
        combined_text = f"{title}\n{content}"
        detected_flags: List[str] = []

        # 1. Deterministic Credential / Secret Detection
        secrets = SecretDetector.detect_secrets(combined_text)
        if secrets:
            return ClassificationResult(
                status="rejected",
                reason=f"Rejected due to sensitive credentials or secrets detected: {', '.join(secrets)}",
                detected_flags=secrets,
                confidence=1.0,
            )

        # 2. Sensitive PII Detection (SSN, Payment Cards)
        for pii_name, pattern in SENSITIVE_PII_PATTERNS:
            if pattern.search(combined_text):
                detected_flags.append(pii_name)

        if detected_flags:
            return ClassificationResult(
                status="rejected",
                reason=f"Rejected due to sensitive personal or financial information: {', '.join(detected_flags)}",
                detected_flags=detected_flags,
                confidence=1.0,
            )

        # 3. Prompt Injection / Malicious System Override Detection
        for inj_name, pattern in MALICIOUS_INJECTION_PATTERNS:
            if pattern.search(combined_text):
                return ClassificationResult(
                    status="rejected",
                    reason=f"Rejected due to prohibited prompt override directive: {inj_name}",
                    detected_flags=[inj_name],
                    confidence=1.0,
                )

        # 4. Source-based Trust and Confirmation Policy
        requires_conf = MemoryPolicy.requires_confirmation(source_type)

        if source_type in ("document", "connector"):
            # External sources cannot persist without explicit confirmation
            return ClassificationResult(
                status="requires_confirmation",
                reason="External content must be explicitly reviewed and confirmed before persisting.",
                detected_flags=["external_untrusted"],
                confidence=0.9,
            )

        if requires_conf:
            return ClassificationResult(
                status="candidate",
                reason="Candidate identified from task execution awaiting user approval.",
                detected_flags=[],
                confidence=0.85,
            )

        return ClassificationResult(
            status="allowed",
            reason="Validated explicit user memory allowed for persistence.",
            detected_flags=[],
            confidence=1.0,
        )
