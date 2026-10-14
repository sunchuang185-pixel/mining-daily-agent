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
            raise ValueError("Synthetic prices cannot enter live mode")
        if live and urlparse(point.source_url).scheme != "https":
            raise ValueError("Live price rows require HTTPS source citations")
        expected = "kg" if point.commodity == "lithium" else "t"
        if point.unit != expected:
            raise ValueError("Commodity price unit is inconsistent with supported contract")
        key = (point.commodity, point.date, point.contract)
        if key in seen and point != seen[key]:
            raise ValueError("Conflicting duplicate price records")
        seen[key] = point
    return sorted(seen.values(), key=lambda p: p.date)


async def load_prices() -> list[PricePoint]:
    if mode() == "demo":
        data = fixture("prices.json")
    elif os.getenv("LME_PRICE_CSV"):
        path = Path(os.environ["LME_PRICE_CSV"])
        if path.stat().st_size > 4_000_000:
            raise ValueError("Price CSV exceeds size limit")
        data = list(csv.DictReader(io.StringIO(path.read_text())))
    elif os.getenv("LME_PRICE_JSON_URL"):
        blob, _ = await fetch(os.environ["LME_PRICE_JSON_URL"])
        data = json.loads(blob)
    else:
        raise ValueError("No live LME feed configured: set LME_PRICE_CSV or LME_PRICE_JSON_URL")
    if not isinstance(data, list):
        raise ValueError("Price feed must be a JSON array or CSV rows")
    return validate_series([PricePoint.model_validate(row) for row in data], live=mode() == "live")


async def price_result(commodity: str, as_of: date, days: int, exact: bool) -> ToolResponse:
    if commodity not in {"copper", "zinc", "nickel", "lithium"} or not 1 <= days <= 90:
        raise ValueError("Unsupported commodity or days outside 1–90")
    warnings = (
        ["SYNTHETIC_DEMO: invented prices, not actual LME quotes"] if mode() == "demo" else []
    )
    if commodity == "lithium":
        warnings.append(
            "Lithium hydroxide contract is not spodumene concentrate or Li2O resource value"
        )
    try:
        points = [p for p in await load_prices() if p.commodity == commodity]
        start = as_of if exact else as_of - timedelta(days=days - 1)
        points = [p for p in points if start <= p.date <= as_of]
        signatures = {(p.contract, p.currency, p.unit) for p in points}
        if len(signatures) > 1:
            raise ValueError("Mixed contracts cannot be combined into one price trend")
        if not points:
            return ToolResponse(
                status="unavailable",
                mode=mode(),
                warnings=[
                    *warnings,
                    "No quote in requested date window; no forward-fill or invented price",
                ],
            )
        if points[-1].date != as_of:
            warnings.append(f"Latest observation is {points[-1].date}; as-of date is {as_of}")
        change = (points[-1].price / points[0].price - 1) * 100 if len(points) >= 2 else None
        if not exact and change is None:
            warnings.append("At least two observations are required to calculate a trend")
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
