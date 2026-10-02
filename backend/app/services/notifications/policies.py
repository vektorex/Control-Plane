"""
NotificationPolicyEngine: SSRF Protection, Rate Limiting, and Recipient Resolution.
"""
import ipaddress
import socket
import time
import urllib.parse
from collections import defaultdict
from typing import List, Optional
from uuid import UUID

from backend.app.config import settings
from backend.app.services.notifications.constants import DeliveryChannelType
from backend.app.services.notifications.errors import RateLimitExceededError, SSRFSecurityError


class SSRFValidator:
    """
    Validates outbound webhook URLs against SSRF, private network probing,
    cloud metadata theft, and protocol exploitation.
    """

    FORBIDDEN_NETWORKS = [
        ipaddress.ip_network("0.0.0.0/8"),
        ipaddress.ip_network("127.0.0.0/8"),         # IPv4 loopback
        ipaddress.ip_network("10.0.0.0/8"),          # Private RFC1918
        ipaddress.ip_network("172.16.0.0/12"),       # Private RFC1918
        ipaddress.ip_network("192.168.0.0/16"),      # Private RFC1918
        ipaddress.ip_network("169.254.0.0/16"),      # Link-local / AWS/GCP/Azure Metadata (169.254.169.254)
        ipaddress.ip_network("100.64.0.0/10"),       # Carrier-grade NAT
        ipaddress.ip_network("192.0.0.0/24"),        # IETF protocol assignments
        ipaddress.ip_network("198.18.0.0/15"),       # Network benchmark tests
        ipaddress.ip_network("224.0.0.0/4"),         # Multicast
        ipaddress.ip_network("240.0.0.0/4"),         # Reserved
        ipaddress.ip_network("::1/128"),             # IPv6 loopback
        ipaddress.ip_network("fc00::/7"),            # IPv6 unique local
        ipaddress.ip_network("fe80::/10"),           # IPv6 link-local
    ]

    FORBIDDEN_HOSTNAMES = {
        "localhost",
        "loopback",
        "metadata.google.internal",
        "metadata",
        "instance-data",
    }

    @classmethod
    def validate_url(cls, url: str, allow_http: bool = False) -> str:
        """
        Validates URL scheme, hostname, and resolves DNS to confirm the target IP
        does not reside on a private or loopback interface.
        """
        if not url:
            raise SSRFSecurityError("Destination URL cannot be empty.")

        parsed = urllib.parse.urlparse(url)
        scheme = parsed.scheme.lower()

        if scheme not in ("http", "https"):
            raise SSRFSecurityError(f"Unsupported protocol '{scheme}'. Only HTTP/HTTPS allowed.")

        if not allow_http and scheme != "https":
            # For strict production safety, enforce HTTPS
            raise SSRFSecurityError("Only HTTPS webhook destinations are permitted in production.")

        hostname = parsed.hostname
        if not hostname:
            raise SSRFSecurityError("Invalid URL: missing hostname.")

        hostname_lower = hostname.lower()
        if hostname_lower in cls.FORBIDDEN_HOSTNAMES or hostname_lower.endswith(".local") or hostname_lower.endswith(".internal"):
            raise SSRFSecurityError(f"Restricted hostname '{hostname}' is not permitted.")

        # Resolve hostname to all associated IP addresses
        try:
            addr_info = socket.getaddrinfo(hostname, parsed.port or (443 if scheme == "https" else 80), proto=socket.IPPROTO_TCP)
        except socket.gaierror as e:
            raise SSRFSecurityError(f"DNS resolution failed for hostname '{hostname}': {e}")

        if not addr_info:
            raise SSRFSecurityError(f"No IP addresses resolved for hostname '{hostname}'.")

        for entry in addr_info:
            sockaddr = entry[4]
            ip_str = sockaddr[0]
            try:
                ip_obj = ipaddress.ip_address(ip_str)
            except ValueError:
                raise SSRFSecurityError(f"Invalid resolved IP '{ip_str}'.")

            # Check against forbidden networks
            for forbidden_net in cls.FORBIDDEN_NETWORKS:
                if ip_obj in forbidden_net:
                    raise SSRFSecurityError(
                        f"Destination '{hostname}' resolves to private/restricted IP '{ip_str}'."
                    )

        return url


class NotificationRateLimiter:
    """
    Sliding-window in-memory rate limiter enforcing multi-tenant throughput caps.
    """

    def __init__(self):
        # workspace_id -> channel -> list of timestamp floats
        self._deliveries = defaultdict(lambda: defaultdict(list))

    def check_and_record(self, workspace_id: UUID, channel: str) -> None:
        now = time.time()
        window = 60.0  # 1 minute

        max_limit = getattr(settings, "NOTIFICATION_MAX_DELIVERIES_PER_MINUTE", 120)
        if channel == DeliveryChannelType.WEBHOOK.value:
            max_limit = getattr(settings, "WEBHOOK_MAX_DELIVERIES_PER_MINUTE", 60)
        elif channel == DeliveryChannelType.EMAIL.value:
            max_limit = getattr(settings, "EMAIL_MAX_DELIVERIES_PER_MINUTE", 30)

        timestamps = self._deliveries[str(workspace_id)][channel]
        # Prune expired timestamps
        valid_timestamps = [ts for ts in timestamps if now - ts < window]
        self._deliveries[str(workspace_id)][channel] = valid_timestamps

        if len(valid_timestamps) >= max_limit:
            raise RateLimitExceededError(
                f"Workspace has exceeded rate limit of {max_limit} {channel} notifications per minute."
            )

        valid_timestamps.append(now)


class RecipientResolver:
    """
    Resolves trusted system recipients.
    Strictly prohibits model-generated content from injecting arbitrary notification recipients.
    """

    @classmethod
    def resolve_recipients(
        cls,
        workspace_owner_id: Optional[UUID],
        assigned_user_id: Optional[UUID],
        explicit_user_id: Optional[UUID],
    ) -> List[UUID]:
        """
        Determines target user IDs based solely on authoritative system relationships.
        """
        recipients = []
        if explicit_user_id:
            recipients.append(explicit_user_id)
        elif assigned_user_id:
            recipients.append(assigned_user_id)
        elif workspace_owner_id:
            recipients.append(workspace_owner_id)
        return list(dict.fromkeys(recipients))  # Deduplicate preserving order
