"""
Deterministic PII, sensitive data detection, and redaction engine for Step 33.
Never stores raw secrets; computes fingerprints and safe previews only.
"""
import hashlib
import re
from typing import Any, Dict, List, Tuple


PATTERNS = {
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"),
    "phone": re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "ip_address": re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"),
    "credit_card": re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "api_key_openai": re.compile(r"sk-[a-zA-Z0-9]{20,}"),
    "api_key_anthropic": re.compile(r"sk-ant-[a-zA-Z0-9_-]{20,}"),
    "api_key_aws": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "api_key_github": re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{36,}\b"),
    "jwt_token": re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    "bearer_token": re.compile(r"Bearer\s+([a-zA-Z0-9_\-\.]{20,})", re.IGNORECASE),
    "private_key": re.compile(r"-----BEGIN [A-Z ]+ PRIVATE KEY-----"),
}


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def mask_preview(finding_type: str, raw_value: str) -> str:
    """
    Creates a safe, non-reversible preview for UI/audit logs.
    Never exposes complete secret tokens or credentials.
    """
    if "api_key" in finding_type or "token" in finding_type or "private_key" in finding_type:
        prefix = raw_value[:4] if len(raw_value) > 4 else "***"
        return f"{prefix}***[REDACTED]"
    if finding_type == "email":
        parts = raw_value.split("@")
        if len(parts) == 2:
            name, domain = parts
            masked_name = name[:2] + "***" if len(name) > 2 else "***"
            return f"{masked_name}@{domain}"
    if finding_type == "phone":
        return f"***-***-{raw_value[-4:]}"
    if finding_type == "credit_card":
        clean = re.sub(r"\D", "", raw_value)
        return f"****-****-****-{clean[-4:]}"
    if finding_type == "ssn":
        return f"***-**-{raw_value[-4:]}"
    if finding_type == "ip_address":
        parts = raw_value.split(".")
        return f"{parts[0]}.{parts[1]}.***.***"
    return "***[REDACTED]***"


def detect_findings(text: str) -> List[Dict[str, Any]]:
    """
    Scans a text payload and returns deterministic privacy findings.
    Never returns raw secret contents.
    """
    if not text or not isinstance(text, str):
        return []

    findings = []
    seen_fingerprints = set()

    for f_type, pattern in PATTERNS.items():
        for match in pattern.finditer(text):
            raw_match = match.group(0)
            fp = _sha256(raw_match)
            if fp in seen_fingerprints:
                continue
            seen_fingerprints.add(fp)

            preview = mask_preview(f_type, raw_match)
            is_secret = any(k in f_type for k in ("api_key", "jwt", "bearer", "private_key"))
            strategy = "remove" if is_secret else "tokenize_placeholder"

            findings.append({
                "finding_type": f_type,
                "location": f"char:{match.start()}-{match.end()}",
                "redaction_strategy": strategy,
                "confidence": 0.95 if is_secret else 0.85,
                "fingerprint": fp,
                "preview": preview,
                "is_secret": is_secret,
                "is_personal_data": f_type in ("email", "phone", "ssn", "credit_card", "ip_address"),
            })

    return findings


def sanitize_text(text: str, strategy: str = "tokenize_placeholder") -> str:
    """
    Deterministically redacts sensitive tokens and PII from a text string.
    """
    if not text or not isinstance(text, str):
        return text

    sanitized = text

    # Redact secrets first
    for f_type, pattern in PATTERNS.items():
        if "api_key" in f_type or "jwt" in f_type or "bearer" in f_type or "private_key" in f_type:
            sanitized = pattern.sub("[SECRET_REDACTED]", sanitized)
        elif f_type == "email":
            sanitized = pattern.sub("[EMAIL_REDACTED]", sanitized)
        elif f_type == "phone":
            sanitized = pattern.sub("[PHONE_REDACTED]", sanitized)
        elif f_type == "credit_card":
            sanitized = pattern.sub("[CARD_REDACTED]", sanitized)
        elif f_type == "ssn":
            sanitized = pattern.sub("[GOV_ID_REDACTED]", sanitized)
        elif f_type == "ip_address":
            sanitized = pattern.sub("[IP_REDACTED]", sanitized)

    return sanitized


def sanitize_payload(payload: Any) -> Any:
    """
    Recursively scrubs dictionary or list payloads before logging, exporting, or snapshotting.
    """
    if isinstance(payload, dict):
        scrubbed = {}
        for k, v in payload.items():
            k_lower = str(k).lower()
            if any(secret_term in k_lower for secret_term in ("secret", "password", "token", "api_key", "credential", "private_key")):
                scrubbed[k] = "[REDACTED]"
            else:
                scrubbed[k] = sanitize_payload(v)
        return scrubbed
    elif isinstance(payload, list):
        return [sanitize_payload(item) for item in payload]
    elif isinstance(payload, str):
        return sanitize_text(payload)
    return payload
