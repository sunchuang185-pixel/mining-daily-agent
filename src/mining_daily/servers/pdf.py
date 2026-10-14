from typing import Any

from mcp.server.fastmcp import FastMCP

from ..resources import extract_resources as extract

mcp = FastMCP("mineral-pdf-mcp")


@mcp.tool()
async def extract_resources(pdf_url: str) -> dict[str, Any]:
    """Extract cited Indicated/Inferred resources, preserving standard, date and units."""
    return (await extract(pdf_url)).model_dump(mode="json")


if __name__ == "__main__":
    mcp.run(transport="stdio")
