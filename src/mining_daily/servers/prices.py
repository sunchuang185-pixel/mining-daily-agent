from typing import Any

from mcp.server.fastmcp import FastMCP

from ..prices import get_price as price
from ..prices import get_trend as trend

mcp = FastMCP("lme-price-mcp")


@mcp.tool()
async def get_price(commodity: str, date: str) -> dict[str, Any]:
    """Get an exact-date LME quote with contract/unit/source; never forward-fill."""
    return (await price(commodity, date)).model_dump(mode="json")


@mcp.tool()
async def get_trend(commodity: str, days: int = 7) -> dict[str, Any]:
    """Get same-contract price observations and endpoint change over 1–90 days."""
    return (await trend(commodity, days)).model_dump(mode="json")


if __name__ == "__main__":
    mcp.run(transport="stdio")
