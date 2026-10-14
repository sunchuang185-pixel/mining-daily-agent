from typing import Any

from mcp.server.fastmcp import FastMCP

from ..news import fetch_article as fetch
from ..news import search_news

mcp = FastMCP("mining-news-mcp")


@mcp.tool()
async def search(query: str, days: int = 7) -> dict[str, Any]:
    """Find dated mining news matching a project within the last 1–90 calendar days."""
    return (await search_news(query, days)).model_dump(mode="json")


@mcp.tool()
async def fetch_article(url: str) -> dict[str, Any]:
    """Fetch readable article body and source PDF links; never bypass paywalls."""
    return (await fetch(url)).model_dump(mode="json")


if __name__ == "__main__":
    mcp.run(transport="stdio")
