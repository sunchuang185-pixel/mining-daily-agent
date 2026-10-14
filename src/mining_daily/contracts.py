from datetime import UTC, date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class ToolResponse(StrictModel):
    status: Literal["ok", "partial", "unavailable", "error"]
    mode: Literal["demo", "live"]
    data: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    fetched_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class NewsItem(StrictModel):
    title: str
    url: str
    published_at: datetime
    summary: str
    publisher: str


class PricePoint(StrictModel):
    commodity: Literal["copper", "zinc", "nickel", "lithium"]
    date: date
    price: float = Field(gt=0)
    currency: Literal["USD"] = "USD"
    unit: Literal["t", "kg"]
    exchange: Literal["LME"] = "LME"
    contract: str = Field(min_length=3)
    source_url: str
    synthetic: bool = False


class BriefPlan(StrictModel):
    project: str = Field(min_length=1, max_length=160)
    commodity: Literal["copper", "zinc", "nickel", "lithium"]
    days: int = Field(ge=1, le=90)
    as_of: date
    pdf_url: str | None = None


class CallTrace(StrictModel):
    server: str
    tool: str
    arguments: dict[str, Any]
    response: ToolResponse
    elapsed_seconds: float
