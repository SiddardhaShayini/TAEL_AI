from tael.research.models import SearchResultItem
from tael.research.reader_connector import PageReader
from tael.research.search_connector import MockSearchProvider
from tael.research.tools import SearchWebTool, FetchPageTool


def test_mock_search_provider():
    provider = MockSearchProvider()
    provider.add_result(
        title="SQLite FTS5 Documentation",
        url="https://sqlite.org/fts5.html",
        snippet="SQLite FTS5 is an SQLite virtual table module that provides full-text search capability.",
        domain="sqlite.org",
    )

    tool = SearchWebTool(provider=provider)
    res = tool.run({"query": "sqlite fts5", "max_results": 5}, {})
    assert res.success is True
    assert res.data["count"] == 1
    assert res.data["results"][0]["domain"] == "sqlite.org"
    assert "full-text search" in res.data["results"][0]["snippet"]


def test_page_reader_sanitization():
    reader = PageReader()
    raw_html = """
    <html>
        <head><title>Test Page</title><style>.hidden { display: none; }</style></head>
        <body>
            <script>alert('malicious script execution');</script>
            <h1>Technical Overview</h1>
            <p>Granite Code is an open enterprise code intelligence model.</p>
            <footer>Copyright 2026</footer>
        </body>
    </html>
    """
    clean = reader._extract_clean_text(raw_html, "https://example.org/doc")
    
    # Must contain untrusted content banner
    assert "=== [UNTRUSTED EXTERNAL WEB CONTENT: https://example.org/doc] ===" in clean
    # Must contain content
    assert "Technical Overview" in clean
    assert "Granite Code is an open enterprise code intelligence model." in clean
    # Must strip scripts and styles
    assert "malicious script" not in clean
    assert "display: none" not in clean


def test_fetch_page_tool_invalid_url():
    tool = FetchPageTool()
    res = tool.run({"url": "invalid://path"}, {})
    assert res.success is False
    assert "Unsupported URL scheme" in res.error
