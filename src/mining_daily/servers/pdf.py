from typing import Any

from mcp.server.fastmcp import FastMCP

from ..resources import extract_resources as extract

mcp = FastMCP("mineral-pdf-mcp")


@mcp.tool()
async def extract_resources(pdf_url: str) -> dict[str, Any]:
    """提取带证据引用的 Indicated／Inferred 资源量，保留披露标准、日期和原始单位。"""
    return (await extract(pdf_url)).model_dump(mode="json")


if __name__ == "__main__":
    mcp.run(transport="stdio")
