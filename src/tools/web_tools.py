from __future__ import annotations
import os
from langchain_core.tools import tool
from tavily import TavilyClient
from firecrawl import FirecrawlApp


def make_web_tools() -> list:
    @tool
    def search_internet(query: str) -> str:
        """Search the internet using Tavily. Returns top results as text."""
        try:
            client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
            response = client.search(query, max_results=5)
            results = response.get("results", [])
            return "\n\n".join(
                f"**{r['title']}**\n{r.get('content', '')}\nURL: {r['url']}"
                for r in results
            )
        except Exception as e:
            return f"Search error: {e}"

    @tool
    def web_scrape(url: str) -> str:
        """Scrape a webpage using Firecrawl and return its markdown content."""
        try:
            app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))
            result = app.scrape_url(url, params={"formats": ["markdown"]})
            return result.get("markdown", "No content extracted")
        except Exception as e:
            return f"Scrape error: {e}"

    return [search_internet, web_scrape]
