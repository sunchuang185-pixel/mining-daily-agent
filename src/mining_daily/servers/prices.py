from typing import Any

from mcp.server.fastmcp import FastMCP

from ..prices import get_price as price
from ..prices import get_trend as trend

mcp = FastMCP("lme-price-mcp")


@mcp.tool()
async def get_price(commodity: str, date: str) -> dict[str, Any]:
    """获取指定日期的 LME 报价及合约、单位、来源，不沿用此前日期的报价。"""
    return (await price(commodity, date)).model_dump(mode="json")


@mcp.tool()
async def get_trend(commodity: str, days: int = 7) -> dict[str, Any]:
    """获取近 1–90 日内同一合约的价格观测值，并计算首末观测值涨跌幅。"""
    return (await trend(commodity, days)).model_dump(mode="json")


if __name__ == "__main__":
    mcp.run(transport="stdio")
