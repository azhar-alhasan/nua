# tests/test_web_tools.py
from unittest.mock import patch, MagicMock
from tools.web_tools import make_web_tools

def test_search_internet_returns_results():
    mock_client = MagicMock()
    mock_client.search.return_value = {
        "results": [{"title": "Python", "content": "A language", "url": "https://python.org"}]
    }
    with patch("tools.web_tools.TavilyClient", return_value=mock_client):
        tools = make_web_tools()
        search = next(t for t in tools if t.name == "search_internet")
        result = search.invoke({"query": "Python programming"})
    assert "Python" in result

def test_search_internet_handles_error():
    mock_client = MagicMock()
    mock_client.search.side_effect = Exception("API error")
    with patch("tools.web_tools.TavilyClient", return_value=mock_client):
        tools = make_web_tools()
        search = next(t for t in tools if t.name == "search_internet")
        result = search.invoke({"query": "anything"})
    assert "error" in result.lower()

def test_web_scrape_returns_content():
    mock_app = MagicMock()
    mock_app.scrape_url.return_value = {"markdown": "# Hello World\nSome content"}
    with patch("tools.web_tools.FirecrawlApp", return_value=mock_app):
        tools = make_web_tools()
        scrape = next(t for t in tools if t.name == "web_scrape")
        result = scrape.invoke({"url": "https://example.com"})
    assert "Hello World" in result

def test_web_scrape_handles_error():
    mock_app = MagicMock()
    mock_app.scrape_url.side_effect = Exception("Scrape failed")
    with patch("tools.web_tools.FirecrawlApp", return_value=mock_app):
        tools = make_web_tools()
        scrape = next(t for t in tools if t.name == "web_scrape")
        result = scrape.invoke({"url": "https://bad-url.com"})
    assert "error" in result.lower()
