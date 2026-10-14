import json
import os
from datetime import date, datetime
from importlib.resources import files
from typing import Any, Literal
from zoneinfo import ZoneInfo

DEMO_DATE = date(2026, 10, 14)


def mode() -> Literal["demo", "live"]:
    value = os.getenv("MINING_MODE", "demo")
    if value not in {"demo", "live"}:
        raise ValueError("MINING_MODE must be demo or live")
    return value  # type: ignore[return-value]


def today() -> date:
    configured = os.getenv("MINING_AS_OF")
    if configured:
        return date.fromisoformat(configured)
    return DEMO_DATE if mode() == "demo" else datetime.now(ZoneInfo("Asia/Shanghai")).date()


def fixture(name: str) -> Any:
    return json.loads(files("mining_daily").joinpath("fixtures", name).read_text())
