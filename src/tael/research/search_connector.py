import re
from abc import ABC, abstractmethod
from typing import List, Optional
from urllib.parse import urlparse, unquote
import httpx

from tael.research.models import SearchResultItem


class SearchProvider(ABC):
    @abstractmethod
    def search(self, query: str, max_results: int = 5) -> List[SearchResultItem]:
        pass


class DuckDuckGoSearchProvider(SearchProvider):
    """DuckDuckGo search provider using standard web endpoint."""

    def __init__(self, timeout_seconds: float = 10.0):
        self.timeout_seconds = timeout_seconds

    def search(self, query: str, max_results: int = 5) -> List[SearchResultItem]:
        url = "https://html.duckduckgo.com/html/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
        data = {"q": query}

        try:
            with httpx.Client(timeout=self.timeout_seconds, follow_redirects=True) as client:
                res = client.post(url, data=data, headers=headers)
                if res.status_code != 200:
                    return []

                html = res.text
                return self._parse_html_results(html, max_results)
        except Exception:
            return []

    def _parse_html_results(self, html: str, max_results: int) -> List[SearchResultItem]:
        items: List[SearchResultItem] = []
        # Extract result blocks using regex
        # Pattern looks for <a class="result__url" href="..."> and result__snippet
        result_pattern = re.compile(
            r'<a[^>]+class="result__url"[^>]+href="([^"]+)"[^>]*>(.*?)</a>.*?'
            r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>',
            re.DOTALL | re.IGNORECASE,
        )

        for match in result_pattern.finditer(html):
            raw_url, title_raw, snippet_raw = match.groups()
            
            # Clean DuckDuckGo redirect URL
            actual_url = raw_url.strip()
            if "uddg=" in actual_url:
                m = re.search(r'uddg=([^&]+)', actual_url)
                if m:
                    actual_url = unquote(m.group(1))

            title = re.sub(r'<[^>]+>', '', title_raw).strip()
            snippet = re.sub(r'<[^>]+>', '', snippet_raw).strip()
            domain = urlparse(actual_url).netloc

            if actual_url and (title or snippet):
                items.append(
                    SearchResultItem(
                        title=title or domain,
                        url=actual_url,
                        snippet=snippet,
                        source_domain=domain,
                    )
                )

            if len(items) >= max_results:
                break

        return items


class MockSearchProvider(SearchProvider):
    """Deterministic search provider for testing without internet access."""

    def __init__(self, predefined_results: Optional[List[SearchResultItem]] = None):
        self.results = predefined_results or []

    def add_result(self, title: str, url: str, snippet: str, domain: str = "example.com") -> None:
        self.results.append(
            SearchResultItem(
                title=title,
                url=url,
                snippet=snippet,
                source_domain=domain,
            )
        )

    def search(self, query: str, max_results: int = 5) -> List[SearchResultItem]:
        if self.results:
            return self.results[:max_results]
        return [
            SearchResultItem(
                title=f"Documentation for {query}",
                url=f"https://docs.example.org/{query.lower().replace(' ', '-')}",
                snippet=f"Authoritative technical reference and guide explaining {query} in detail.",
                source_domain="docs.example.org",
            ),
            SearchResultItem(
                title=f"Best Practices and Pitfalls: {query}",
                url=f"https://engineering.example.com/{query.lower().replace(' ', '-')}",
                snippet=f"Production architectural patterns, benchmark comparisons, and lessons learned for {query}.",
                source_domain="engineering.example.com",
            ),
        ][:max_results]
