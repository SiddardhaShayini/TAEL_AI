from typing import Any, Dict, Optional

from tael.policy.permissions import PermissionLevel
from tael.research.models import SearchResultItem
from tael.research.reader_connector import PageReader
from tael.research.search_connector import DuckDuckGoSearchProvider, SearchProvider
from tael.tools.base import BaseTool, ToolResult


class SearchWebTool(BaseTool):
    name = "search_web"
    description = (
        "Search the internet for technical documentation, research papers, error messages, and libraries. "
        "Returns top search results with titles, source URLs, and summary snippets."
    )
    permission = PermissionLevel.INTERNET_ACCESS
    parameters_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query keywords."},
            "max_results": {"type": "integer", "description": "Maximum results to return (default 5, max 10)."},
        },
        "required": ["query"],
    }

    def __init__(self, provider: Optional[SearchProvider] = None):
        self.provider = provider or DuckDuckGoSearchProvider()

    def run(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        query = arguments["query"]
        max_results = min(10, max(1, arguments.get("max_results", 5)))

        try:
            results = self.provider.search(query, max_results=max_results)
            if not results:
                return ToolResult(
                    success=True,
                    data={"query": query, "results": [], "message": "No search results found."},
                )

            data = [
                {
                    "title": r.title,
                    "url": r.url,
                    "snippet": r.snippet,
                    "domain": r.source_domain,
                }
                for r in results
            ]
            return ToolResult(
                success=True,
                data={"query": query, "count": len(data), "results": data},
            )
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Search failed: {str(e)}")


class FetchPageTool(BaseTool):
    name = "fetch_web_page"
    description = (
        "Fetch and read the full text content of a web page URL. "
        "Strips ads, styles, and scripts; tags content as untrusted external reference data."
    )
    permission = PermissionLevel.INTERNET_ACCESS
    parameters_schema = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "Web URL to fetch (http:// or https://)."},
        },
        "required": ["url"],
    }

    def __init__(self, reader: Optional[PageReader] = None):
        self.reader = reader or PageReader()

    def run(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        url = arguments["url"].strip()
        try:
            text = self.reader.fetch_text(url)
            return ToolResult(
                success=True,
                data={"url": url, "content": text, "char_count": len(text)},
            )
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Failed to fetch page: {str(e)}")
