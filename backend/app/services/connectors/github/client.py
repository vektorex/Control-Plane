"""
Asynchronous HTTP client for the official GitHub REST API.
"""
import asyncio
from typing import Any, Dict, Optional
import httpx

from backend.app.config import settings
from backend.app.core.logging import logger
from backend.app.services.connectors.errors import (
    ConnectorAuthError,
    ConnectorNotFoundError,
    ConnectorRateLimitError,
    ConnectorTimeoutError,
    ConnectorUnavailableError,
    ConnectorError,
)

GITHUB_API_BASE = "https://api.github.com"


class GitHubClient:
    """
    Client for interacting with GitHub REST API endpoints securely.
    """

    def __init__(
        self,
        token: str,
        base_url: str = GITHUB_API_BASE,
        timeout: Optional[float] = None,
    ) -> None:
        self.token = token.strip() if token else ""
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout or getattr(settings, "CONNECTOR_TIMEOUT_SECONDS", 30.0)

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "AI-Work-Layer-Connector/0.1.0",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Executes a GET request against the GitHub API and handles normalized error status codes.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        clean_params = {k: v for k, v in (params or {}).items() if v is not None}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    headers=self._get_headers(),
                    params=clean_params,
                )

                # Check rate limit headers
                remaining = response.headers.get("x-ratelimit-remaining")
                if remaining == "0" or response.status_code == 429:
                    raise ConnectorRateLimitError(
                        "GitHub API rate limit exceeded. Please wait before retrying or use an authenticated token."
                    )

                if response.status_code == 401:
                    raise ConnectorAuthError(
                        "GitHub authentication failed. Token is invalid or has expired."
                    )

                if response.status_code == 403:
                    body = response.text.lower()
                    if "rate limit" in body:
                        raise ConnectorRateLimitError("GitHub API rate limit exceeded.")
                    raise ConnectorAuthError("GitHub permission denied. Check token scopes.")

                if response.status_code == 404:
                    raise ConnectorNotFoundError(f"GitHub resource at '{endpoint}' not found.")

                if response.status_code >= 500:
                    raise ConnectorUnavailableError(
                        f"GitHub service unavailable (status {response.status_code})."
                    )

                if response.status_code >= 400:
                    raise ConnectorError(
                        f"GitHub API error (status {response.status_code}): {response.text[:200]}",
                        code="GITHUB_API_ERROR",
                    )

                return response.json()

        except httpx.TimeoutException:
            logger.error(f"[GitHubClient] Request to '{endpoint}' timed out after {self.timeout}s")
            raise ConnectorTimeoutError(f"GitHub API request timed out after {self.timeout} seconds.")
        except httpx.RequestError as e:
            logger.error(f"[GitHubClient] Network error reaching GitHub API: {e}")
            raise ConnectorUnavailableError(f"Network error connecting to GitHub: {str(e)}")
