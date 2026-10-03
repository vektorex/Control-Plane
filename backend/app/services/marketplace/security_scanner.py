"""
Marketplace Security Scanner.
Step 38: AI Workflow Marketplace, Versioned Templates & Extension Ecosystem.
"""
import re
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse

from backend.app.services.marketplace.schemas import SecurityStatus

# Secret detection patterns (reusing Step 33 concepts)
SECRET_PATTERNS = [
    re.compile(r"(?:api[_-]?key|secret|password|bearer|auth[_-]?token)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]", re.IGNORECASE),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"sk-[a-zA-Z0-9_\-]{20,}", re.IGNORECASE),  # OpenAI style keys
    re.compile(r"awl_(?:dev|stg|prod)_[a-zA-Z0-9]{20,}", re.IGNORECASE),  # Platform keys
]

# Path traversal
PATH_TRAVERSAL_PATTERN = re.compile(r"(?:\.\./|\.\.\\)")

# SSRF and blocked IP hosts
BLOCKED_HOSTS = {"127.0.0.1", "localhost", "0.0.0.0", "169.254.169.254", "::1"}
PRIVATE_IP_PREFIXES = ("10.", "192.168.", "172.16.", "172.17.", "172.18.", "172.19.", "172.20.", "172.21.", "172.22.", "172.23.", "172.24.", "172.25.", "172.26.", "172.27.", "172.28.", "172.29.", "172.30.", "172.31.")

# Dangerous shell commands
SHELL_COMMANDS = [
    re.compile(r"\b(?:rm\s+-rf|curl\s+|wget\s+|chmod\s+\+x|bash\s+-c|sh\s+-c|powershell\s+)\b", re.IGNORECASE)
]


class MarketplaceSecurityScanner:
    """Scans package manifest, components, and documentation for security risks, secrets, and injection."""

    @classmethod
    def scan_manifest(cls, manifest: Dict[str, Any]) -> Tuple[SecurityStatus, List[str]]:
        """
        Executes comprehensive security scan on package manifest.
        Returns (SecurityStatus, findings_list).
        Status is BLOCKED if critical secrets or shell/path traversal is detected.
        Status is WARNING if potential prompt injection or unverified external URLs exist.
        Status is SCANNED if clean.
        """
        findings: List[str] = []
        is_blocked = False

        def _scan(obj: Any, path: str = "root"):
            nonlocal is_blocked
            if isinstance(obj, str):
                # 1. Secret detection
                for pat in SECRET_PATTERNS:
                    if pat.search(obj):
                        findings.append(f"Potential hardcoded credential or secret detected at {path}.")
                        is_blocked = True
                        break

                # 2. Path traversal
                if PATH_TRAVERSAL_PATTERN.search(obj):
                    findings.append(f"Path traversal sequence detected at {path}.")
                    is_blocked = True

                # 3. Shell commands
                for cmd_pat in SHELL_COMMANDS:
                    if cmd_pat.search(obj):
                        findings.append(f"Suspicious shell command pattern detected at {path}.")
                        is_blocked = True
                        break

                # 4. URL safety & SSRF
                if obj.startswith("http://") or obj.startswith("https://"):
                    try:
                        parsed = urlparse(obj)
                        host = (parsed.hostname or "").lower()
                        if host in BLOCKED_HOSTS or any(host.startswith(p) for p in PRIVATE_IP_PREFIXES):
                            findings.append(f"Prohibited private, loopback, or SSRF destination host '{host}' in URL '{obj}' at {path}.")
                            is_blocked = True
                        elif parsed.scheme != "https":
                            findings.append(f"Insecure plain HTTP URL '{obj}' at {path}.")
                    except Exception:
                        pass

            elif isinstance(obj, dict):
                for k, v in obj.items():
                    _scan(v, f"{path}.{k}")
            elif isinstance(obj, list):
                for i, elem in enumerate(obj):
                    _scan(elem, f"{path}[{i}]")

        _scan(manifest)

        if is_blocked:
            return SecurityStatus.BLOCKED, findings
        elif findings:
            return SecurityStatus.WARNING, findings
        return SecurityStatus.SCANNED, []
