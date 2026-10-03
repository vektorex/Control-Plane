"""
Payload, SSRF, and Workflow Input Validators for Developer Platform.
Step 37: Public API, Developer Platform & SDK Layer.
"""
import ipaddress
import re
import socket
from urllib.parse import urlparse
from typing import Any, Dict, List
from backend.app.services.developer_platform.errors import PublicAPIException, PublicAPIErrorType, SSRFBlockedError

# Dangerous script / template injection patterns
DANGEROUS_PATTERNS = [
    re.compile(r"__import__", re.IGNORECASE),
    re.compile(r"subprocess", re.IGNORECASE),
    re.compile(r"eval\s*\(", re.IGNORECASE),
    re.compile(r"exec\s*\(", re.IGNORECASE),
    re.compile(r"os\.system", re.IGNORECASE),
    re.compile(r"<script[\s>]", re.IGNORECASE),
    re.compile(r"\{\{.*__.*\}\}", re.IGNORECASE),  # Jinja template execution attempts
]


class InputValidator:
    """Validates public API inputs, protects against code injection and SSRF."""

    @classmethod
    def validate_workflow_inputs(cls, inputs: Dict[str, Any], max_depth: int = 5) -> None:
        """
        Validates workflow inputs to reject executable code, dangerous templates,
        and deeply nested or oversized objects.
        """
        if not isinstance(inputs, dict):
            raise PublicAPIException(
                "Workflow inputs must be a JSON object (dictionary).",
                status_code=400,
                error_type=PublicAPIErrorType.VALIDATION_ERROR,
                code="invalid_workflow_inputs",
            )

        def _scan(value: Any, current_depth: int):
            if current_depth > max_depth:
                raise PublicAPIException(
                    f"Workflow input nesting exceeds maximum depth of {max_depth}.",
                    status_code=400,
                    error_type=PublicAPIErrorType.VALIDATION_ERROR,
                    code="input_depth_exceeded",
                )

            if isinstance(value, str):
                if len(value) > 100000:  # 100KB per string field
                    raise PublicAPIException(
                        "Individual input string exceeds maximum size limit (100KB).",
                        status_code=400,
                        error_type=PublicAPIErrorType.VALIDATION_ERROR,
                        code="input_field_oversized",
                    )
                for pattern in DANGEROUS_PATTERNS:
                    if pattern.search(value):
                        raise PublicAPIException(
                            "Workflow input contains disallowed expressions or injection patterns.",
                            status_code=400,
                            error_type=PublicAPIErrorType.VALIDATION_ERROR,
                            code="disallowed_input_pattern",
                        )
            elif isinstance(value, dict):
                for k, v in value.items():
                    if len(str(k)) > 128:
                        raise PublicAPIException("Input key name is too long.", status_code=400)
                    _scan(v, current_depth + 1)
            elif isinstance(value, list):
                if len(value) > 500:
                    raise PublicAPIException("Input list exceeds maximum length (500 items).", status_code=400)
                for item in value:
                    _scan(item, current_depth + 1)

        _scan(inputs, 1)

    @classmethod
    def validate_webhook_url(cls, url: str, allow_local_for_testing: bool = False) -> None:
        """
        Validates webhook destination URL.
        Enforces HTTPS and protects against Server-Side Request Forgery (SSRF)
        by blocking RFC 1918 private ranges, AWS metadata IPs, and loopbacks (unless in local test).
        """
        if not url:
            raise SSRFBlockedError("Webhook URL cannot be empty.")

        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        hostname = parsed.hostname

        if not hostname:
            raise SSRFBlockedError("Invalid webhook URL: missing hostname.")

        # In production/staging, HTTPS is strictly mandatory
        if scheme != "https":
            if not (allow_local_for_testing and scheme == "http" and hostname in ("localhost", "127.0.0.1")):
                raise SSRFBlockedError("Webhook URL must use the HTTPS scheme.")

        # Check for loopback / private IP
        try:
            # Check if hostname is an IP literal
            ip = ipaddress.ip_address(hostname)
            if not allow_local_for_testing:
                if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                    raise SSRFBlockedError(f"Webhook destination IP '{hostname}' is not permitted.")
            # Block AWS/cloud metadata address 169.254.169.254 unconditionally
            if str(ip) == "169.254.169.254":
                raise SSRFBlockedError("Access to metadata service is strictly blocked.")
        except ValueError:
            # Hostname is a domain name, not an IP literal
            if hostname.lower() in ("localhost", "127.0.0.1", "0.0.0.0") and not allow_local_for_testing:
                raise SSRFBlockedError(f"Webhook destination hostname '{hostname}' is prohibited.")
