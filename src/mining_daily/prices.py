"""LME-labelled data adapters with explicit contract, source and calendar semantics."""

import csv
import io
import json
import os
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlparse

from .contracts import PricePoint, ToolResponse
from .network import FetchError, fetch
from .settings import fixture, mode, today


def validate_series(points: list[PricePoint], live: bool) -> list[PricePoint]:
    seen: dict[tuple[str, date, str], PricePoint] = {}
    for point in points:
        if live and point.synthetic:
            raise ValueError("合成报价不能用于 live 模式")
        if live and urlparse(point.source_url).scheme != "https":
            raise ValueError("真实报价记录必须提供 HTTPS 来源引用")
        expected = "kg" if point.commodity == "lithium" else "t"
        if point.unit != expected:
            raise ValueError("矿种价格单位与支持的合约口径不一致")
        key = (point.commodity, point.date, point.contract)
        if key in seen and point != seen[key]:
            raise ValueError("重复报价记录存在冲突")
        seen[key] = point
    return sorted(seen.values(), key=lambda p: p.date)


async def load_prices() -> list[PricePoint]:
    if mode() == "demo":
        data = fixture("prices.json")
    elif os.getenv("LME_PRICE_CSV"):
        path = Path(os.environ["LME_PRICE_CSV"])
        if path.stat().st_size > 4_000_000:
            raise ValueError("报价 CSV 超过大小限制")
        data = list(csv.DictReader(io.StringIO(path.read_text())))
    elif os.getenv("LME_PRICE_JSON_URL"):
        blob, _ = await fetch(os.environ["LME_PRICE_JSON_URL"])
        data = json.loads(blob)
    else:
        raise ValueError("未配置真实 LME 数据源：请设置 LME_PRICE_CSV 或 LME_PRICE_JSON_URL")
    if not isinstance(data, list):
        raise ValueError("报价数据源必须为 JSON 数组或 CSV 行记录")
    return validate_series([PricePoint.model_validate(row) for row in data], live=mode() == "live")


async def price_result(commodity: str, as_of: date, days: int, exact: bool) -> ToolResponse:
    if commodity not in {"copper", "zinc", "nickel", "lithium"} or not 1 <= days <= 90:
        raise ValueError("不支持该矿种，或 days 不在 1–90 范围内")
    warnings = ["SYNTHETIC_DEMO：价格均为虚构，并非真实 LME 报价"] if mode() == "demo" else []
    if commodity == "lithium":
        warnings.append("氢氧化锂合约、锂辉石精矿报价及矿石中的 Li2O 含量口径不同，不可直接替代。")
    try:
        points = [p for p in await load_prices() if p.commodity == commodity]
        start = as_of if exact else as_of - timedelta(days=days - 1)
        points = [p for p in points if start <= p.date <= as_of]
        signatures = {(p.contract, p.currency, p.unit) for p in points}
        if len(signatures) > 1:
            raise ValueError("不同合约不能合并计算同一价格走势")
        if not points:
            return ToolResponse(
                status="unavailable",
                mode=mode(),
                warnings=[
                    *warnings,
                    "请求的日期窗口内无报价；未沿用上一交易日报价，也未编造价格",
                ],
            )
        if points[-1].date != as_of:
            warnings.append(f"最近观测日期为 {points[-1].date}；报告日期为 {as_of}")
        change = (points[-1].price / points[0].price - 1) * 100 if len(points) >= 2 else None
        if not exact and change is None:
            warnings.append("至少需要两个观测值才能计算走势")
        return ToolResponse(
            status="ok" if exact or len(points) >= 2 else "partial",
            mode=mode(),
            data={
                "points": [p.model_dump(mode="json") for p in points],
                "change_pct": change,
                "window_start": start.isoformat(),
                "as_of": as_of.isoformat(),
                "observations": len(points),
            },
            warnings=warnings,
            sources=list(dict.fromkeys(p.source_url for p in points)),
        )
    except (ValueError, OSError, FetchError) as exc:
        return ToolResponse(status="unavailable", mode=mode(), warnings=[*warnings, str(exc)])


async def get_price(commodity: str, requested_date: str) -> ToolResponse:
    return await price_result(commodity, date.fromisoformat(requested_date), 1, exact=True)


async def get_trend(commodity: str, days: int) -> ToolResponse:
    return await price_result(commodity, today(), days, exact=False)
