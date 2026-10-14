from typing import Any

from mcp.server.fastmcp import FastMCP

from ..news import fetch_article as fetch
from ..news import search_news

mcp = FastMCP("mining-news-mcp")


@mcp.tool()
async def search(query: str, days: int = 7) -> dict[str, Any]:
    """检索近 1–90 个自然日内带日期且匹配指定项目的矿业新闻。"""
    return (await search_news(query, days)).model_dump(mode="json")


@mcp.tool()
async def fetch_article(url: str) -> dict[str, Any]:
    """获取可读的新闻正文及来源 PDF 链接，不绕过付费墙。"""
    return (await fetch(url)).model_dump(mode="json")


if __name__ == "__main__":
    mcp.run(transport="stdio")
