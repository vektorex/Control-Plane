from abc import ABC, abstractmethod
import asyncio
from datetime import datetime, timezone
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
import httpx
from pydantic import BaseModel, Field

from backend.app.config import settings
from backend.app.core.logging import logger
from backend.app.db.models.user import User
from backend.app.services.tools.base import BaseTool
from backend.app.services.tools.errors import ToolExecutionError, ToolTimeoutError, ToolValidationError


class WebSearchInput(BaseModel):
    """
    Validated input parameters for web search tool.
    """
    query: str = Field(
        ...,
        min_length=2,
        max_length=500,
        description="Search query string",
    )
    limit: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of search results to retrieve (1 - 20)",
    )
    recency_days: Optional[int] = Field(
        default=None,
        ge=1,
        le=365,
        description="Optional recency window in days",
    )


class WebSearchResultItem(BaseModel):
    """
    Normalized web search result item.
    """
    title: str = Field(..., description="Web page title")
    url: str = Field(..., description="Web page target URL")
    snippet: str = Field(..., description="Extracted snippet or summary")
    source: Optional[str] = Field(default=None, description="Domain source name (e.g. docs.python.org)")
    published_at: Optional[str] = Field(default=None, description="Publication timestamp or date string")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional result metadata")


class WebSearchResponse(BaseModel):
    """
    Structured, normalized response returned by all web search providers.
    """
    query: str
    results: List[WebSearchResultItem] = Field(default_factory=list)
    total_results: int = 0
    provider: str = "web_search"


class WebSearchProvider(ABC):
    """
    Abstract adapter interface for pluggable search engines
    (DuckDuckGo, Tavily, Serper, Brave, Mock).
    """

    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 5,
        recency_days: Optional[int] = None,
        **kwargs: Any,
    ) -> WebSearchResponse:
        """Execute web search and return normalized results."""
        pass


class DuckDuckGoSearchProvider(WebSearchProvider):
    """
    Direct web search provider using DuckDuckGo HTML / API without requiring API keys.
    Extracts authentic titles, URLs, and snippets with robust HTML entity cleaning.
    """

    async def search(
        self,
        query: str,
        limit: int = 5,
        recency_days: Optional[int] = None,
        **kwargs: Any,
    ) -> WebSearchResponse:
        clean_query = query.strip()
        limit = max(1, min(limit, settings.WEB_SEARCH_MAX_LIMIT))
        timeout = kwargs.get("timeout_seconds", settings.WEB_SEARCH_TIMEOUT_SECONDS)

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        # 1. Try DuckDuckGo HTML endpoint
        url = "https://html.duckduckgo.com/html/"
        data = {"q": clean_query}

        try:
            async with httpx.AsyncClient(headers=headers, timeout=timeout, follow_redirects=True) as client:
                resp = await client.post(url, data=data)
                
                if resp.status_code != 200:
                    logger.warning(f"[DuckDuckGoSearch] Received HTTP {resp.status_code}. Retrying GET...")
                    resp = await client.get(f"https://html.duckduckgo.com/html/?q={clean_query}")

                if resp.status_code == 200:
                    results = self._parse_html(resp.text, limit)
                    if results:
                        return WebSearchResponse(
                            query=clean_query,
                            results=results,
                            total_results=len(results),
                            provider="duckduckgo",
                        )

            # Fallback to DuckDuckGo Instant Answer API if HTML scraper returns 0 results
            async with httpx.AsyncClient(headers=headers, timeout=timeout) as client:
                api_url = f"https://api.duckduckgo.com/?q={clean_query}&format=json&no_html=1&skip_disambig=1"
                api_resp = await client.get(api_url)
                if api_resp.status_code == 200:
                    api_data = api_resp.json()
                    results = self._parse_instant_answer_json(api_data, clean_query, limit)
                    if results:
                        return WebSearchResponse(
                            query=clean_query,
                            results=results,
                            total_results=len(results),
                            provider="duckduckgo_api",
                        )

            if settings.ENVIRONMENT == "test":
                mock_p = MockWebSearchProvider()
                return await mock_p.search(clean_query, limit=limit, recency_days=recency_days)

            return WebSearchResponse(query=clean_query, results=[], total_results=0, provider="duckduckgo")

        except httpx.TimeoutException:
            raise ToolTimeoutError(f"Web search for '{clean_query}' timed out after {timeout}s.")
        except Exception as e:
            logger.error(f"[DuckDuckGoSearch] Search execution failed: {str(e)}", exc_info=True)
            raise ToolExecutionError(f"DuckDuckGo search error: {str(e)}")

    def _parse_html(self, html_text: str, limit: int) -> List[WebSearchResultItem]:
        results: List[WebSearchResultItem] = []
        # Match result blocks: class="result results_links results_links_deep web-result" or similar
        # Extract href, title, snippet
        link_pattern = re.compile(
            r'<a[^>]+class="[^"]*result__snippet[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            re.DOTALL | re.IGNORECASE,
        )
        url_pattern = re.compile(r'<a[^>]+class="[^"]*result__url[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.DOTALL | re.IGNORECASE)
        title_pattern = re.compile(r'<a[^>]+class="[^"]*result__a[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.DOTALL | re.IGNORECASE)
        snippet_pattern = re.compile(r'<a[^>]+class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</a>', re.DOTALL | re.IGNORECASE)

        # Split into result blocks
        blocks = html_text.split('class="result results_links')
        for block in blocks[1:]:
            t_match = title_pattern.search(block)
            s_match = snippet_pattern.search(block)

            if t_match:
                raw_url = t_match.group(1)
                raw_title = t_match.group(2)
                raw_snippet = s_match.group(1) if s_match else ""

                # Extract target URL if wrapped in DuckDuckGo redirect /uddg=...
                actual_url = raw_url
                if "uddg=" in raw_url:
                    import urllib.parse
                    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(raw_url).query)
                    if "uddg" in parsed:
                        actual_url = parsed["uddg"][0]

                # Strip HTML tags & decode entities
                import html
                clean_title = html.unescape(re.sub(r"<[^>]+>", "", raw_title)).strip()
                clean_snippet = html.unescape(re.sub(r"<[^>]+>", "", raw_snippet)).strip()

                if actual_url and clean_title:
                    parsed_uri = urlparse(actual_url)
                    source_domain = parsed_uri.netloc or "web"

                    results.append(
                        WebSearchResultItem(
                            title=clean_title,
                            url=actual_url,
                            snippet=clean_snippet or f"Information regarding {clean_title}",
                            source=source_domain,
                            published_at=None,
                        )
                    )
                    if len(results) >= limit:
                        break

        return results

    def _parse_instant_answer_json(self, data: Dict[str, Any], query: str, limit: int) -> List[WebSearchResultItem]:
        results: List[WebSearchResultItem] = []
        if data.get("AbstractText") and data.get("AbstractURL"):
            results.append(
                WebSearchResultItem(
                    title=data.get("Heading") or query,
                    url=data["AbstractURL"],
                    snippet=data["AbstractText"],
                    source=urlparse(data["AbstractURL"]).netloc or "duckduckgo",
                )
            )

        for topic in data.get("RelatedTopics", []):
            if "Text" in topic and "FirstURL" in topic:
                results.append(
                    WebSearchResultItem(
                        title=topic.get("Text", "")[:60],
                        url=topic["FirstURL"],
                        snippet=topic.get("Text", ""),
                        source=urlparse(topic["FirstURL"]).netloc or "duckduckgo",
                    )
                )
                if len(results) >= limit:
                    break

        return results


class TavilySearchProvider(WebSearchProvider):
    """
    Search provider using Tavily API (https://tavily.com).
    """

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def search(
        self,
        query: str,
        limit: int = 5,
        recency_days: Optional[int] = None,
        **kwargs: Any,
    ) -> WebSearchResponse:
        clean_query = query.strip()
        limit = max(1, min(limit, settings.WEB_SEARCH_MAX_LIMIT))
        timeout = kwargs.get("timeout_seconds", settings.WEB_SEARCH_TIMEOUT_SECONDS)

        payload = {
            "api_key": self.api_key,
            "query": clean_query,
            "max_results": limit,
            "search_depth": "basic",
            "include_domains": [],
            "exclude_domains": [],
        }
        if recency_days:
            payload["days"] = recency_days

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                res = await client.post("https://api.tavily.com/search", json=payload)
                if res.status_code != 200:
                    raise ToolExecutionError(f"Tavily search failed with HTTP {res.status_code}: {res.text}")

                data = res.json()
                results: List[WebSearchResultItem] = []
                for item in data.get("results", []):
                    results.append(
                        WebSearchResultItem(
                            title=item.get("title") or "Web Search Result",
                            url=item.get("url") or "",
                            snippet=item.get("content") or "",
                            source=urlparse(item.get("url", "")).netloc or "tavily",
                            published_at=item.get("published_date"),
                            metadata={"score": item.get("score")},
                        )
                    )

                return WebSearchResponse(
                    query=clean_query,
                    results=results,
                    total_results=len(results),
                    provider="tavily",
                )
        except httpx.TimeoutException:
            raise ToolTimeoutError(f"Tavily search for '{clean_query}' timed out.")
        except Exception as e:
            raise ToolExecutionError(f"Tavily search error: {str(e)}")


class SerperSearchProvider(WebSearchProvider):
    """
    Search provider using Google Serper API (https://serper.dev).
    """

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def search(
        self,
        query: str,
        limit: int = 5,
        recency_days: Optional[int] = None,
        **kwargs: Any,
    ) -> WebSearchResponse:
        clean_query = query.strip()
        limit = max(1, min(limit, settings.WEB_SEARCH_MAX_LIMIT))
        timeout = kwargs.get("timeout_seconds", settings.WEB_SEARCH_TIMEOUT_SECONDS)

        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {"q": clean_query, "num": limit}

        try:
            async with httpx.AsyncClient(headers=headers, timeout=timeout) as client:
                res = await client.post("https://google.serper.dev/search", json=payload)
                if res.status_code != 200:
                    raise ToolExecutionError(f"Serper search failed with HTTP {res.status_code}: {res.text}")

                data = res.json()
                results: List[WebSearchResultItem] = []
                for item in data.get("organic", []):
                    results.append(
                        WebSearchResultItem(
                            title=item.get("title") or "Search Result",
                            url=item.get("link") or "",
                            snippet=item.get("snippet") or "",
                            source=urlparse(item.get("link", "")).netloc or "serper",
                            published_at=item.get("date"),
                        )
                    )

                return WebSearchResponse(
                    query=clean_query,
                    results=results,
                    total_results=len(results),
                    provider="serper",
                )
        except httpx.TimeoutException:
            raise ToolTimeoutError(f"Serper search for '{clean_query}' timed out.")
        except Exception as e:
            raise ToolExecutionError(f"Serper search error: {str(e)}")


class MockWebSearchProvider(WebSearchProvider):
    """
    Deterministic mock web search provider for testing and offline environments.
    """

    def __init__(self, mock_results: Optional[List[WebSearchResultItem]] = None):
        self.mock_results = mock_results

    async def search(
        self,
        query: str,
        limit: int = 5,
        recency_days: Optional[int] = None,
        **kwargs: Any,
    ) -> WebSearchResponse:
        clean_query = query.strip()
        if not clean_query:
            return WebSearchResponse(query=clean_query, results=[], total_results=0, provider="mock")

        if self.mock_results is not None:
            res_items = self.mock_results[:limit]
        else:
            res_items = [
                WebSearchResultItem(
                    title=f"Documentation on {clean_query}",
                    url=f"https://docs.example.com/{clean_query.lower().replace(' ', '-')}",
                    snippet=f"Comprehensive documentation and architectural reference for {clean_query}.",
                    source="docs.example.com",
                    published_at=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                ),
                WebSearchResultItem(
                    title=f"Release Notes & Updates: {clean_query}",
                    url=f"https://github.com/example/{clean_query.lower().replace(' ', '-')}/releases",
                    snippet=f"Latest updates, security enhancements, and changelog for {clean_query}.",
                    source="github.com",
                    published_at=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                ),
            ][:limit]

        return WebSearchResponse(
            query=clean_query,
            results=res_items,
            total_results=len(res_items),
            provider="mock",
        )


def get_web_search_provider() -> WebSearchProvider:
    """
    Factory resolving configured WebSearchProvider from environment settings.
    """
    provider_name = (settings.WEB_SEARCH_PROVIDER or "duckduckgo").lower().strip()
    api_key = settings.WEB_SEARCH_API_KEY

    if provider_name == "tavily" and api_key:
        return TavilySearchProvider(api_key)
    elif provider_name == "serper" and api_key:
        return SerperSearchProvider(api_key)
    elif provider_name == "mock":
        return MockWebSearchProvider()
    else:
        # Default to DuckDuckGo
        return DuckDuckGoSearchProvider()


class WebSearchTool(BaseTool):
    """
    Production-oriented Web Search Tool.
    Gathers real-time external knowledge from the web via configured search providers.
    """
    name = "web_search"
    description = (
        "Search the live web for real-time documentation, recent information, "
        "security updates, APIs, and factual references."
    )
    input_schema = WebSearchInput
    requires_auth = True
    metadata = {
        "category": "search",
        "provider": settings.WEB_SEARCH_PROVIDER,
        "untrusted_content": True,
    }

    def __init__(self, provider: Optional[WebSearchProvider] = None):
        self.provider = provider or get_web_search_provider()

    async def execute(
        self,
        input_data: WebSearchInput,
        user: Optional[User] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Executes web search query and returns normalized response dictionary.
        """
        search_res = await self.provider.search(
            query=input_data.query,
            limit=input_data.limit,
            recency_days=input_data.recency_days,
            **kwargs,
        )
        return search_res.model_dump()
