import asyncio
from datetime import date

import pytest

from mining_daily.contracts import PricePoint
from mining_daily.prices import get_price, get_trend, validate_series
from mining_daily.settings import fixture


def test_exact_date_does_not_forward_fill():
    response = asyncio.run(get_price("lithium", "2026-10-10"))
    assert response.status == "unavailable"
    assert "points" not in response.data


def test_trend_uses_observation_endpoints():
    response = asyncio.run(get_trend("lithium", 7))
    assert response.status == "ok"
    assert response.data["observations"] == 5
    assert response.data["change_pct"] == pytest.approx((12.5 / 12 - 1) * 100)
    assert response.data["points"][-1]["date"] == "2026-10-14"


def test_no_trend_with_one_observation():
    response = asyncio.run(get_trend("lithium", 1))
    assert response.status == "partial"
    assert response.data["change_pct"] is None


def test_mixed_contracts_rejected(monkeypatch):
    points = [PricePoint.model_validate(x) for x in fixture("prices.json")]
    points[-1].contract = "Another expiry"

    async def load():
        return points

    monkeypatch.setattr("mining_daily.prices.load_prices", load)
    assert asyncio.run(get_trend("lithium", 7)).status == "unavailable"


def test_live_cannot_use_synthetic_prices():
    points = [PricePoint.model_validate(x) for x in fixture("prices.json")]
    with pytest.raises(ValueError, match="Synthetic"):
        validate_series(points, live=True)


def test_conflicting_duplicate_price_rejected():
    point = PricePoint.model_validate(fixture("prices.json")[0])
    altered = point.model_copy(update={"price": point.price + 1})
    with pytest.raises(ValueError, match="Conflicting"):
        validate_series([point, altered], live=False)


def test_no_future_observations(monkeypatch):
    monkeypatch.setenv("MINING_AS_OF", "2026-10-12")
    response = asyncio.run(get_trend("lithium", 7))
    assert all(date.fromisoformat(p["date"]) <= date(2026, 10, 12) for p in response.data["points"])


def test_missing_live_feed_is_explicit(monkeypatch):
    monkeypatch.setenv("MINING_MODE", "live")
    response = asyncio.run(get_trend("lithium", 7))
    assert response.status == "unavailable"
    assert "No live LME feed" in " ".join(response.warnings)


def test_live_csv_path(tmp_path, monkeypatch):
    monkeypatch.setenv("MINING_MODE", "live")
    path = tmp_path / "prices.csv"
    path.write_text(
        "commodity,date,price,currency,unit,exchange,contract,source_url,synthetic\n"
        "copper,2026-10-14,9000,USD,t,LME,Test fixture contract,https://example.org/fixture,false\n"
    )
    monkeypatch.setenv("LME_PRICE_CSV", str(path))
    response = asyncio.run(get_price("copper", "2026-10-14"))
    assert response.status == "ok"
    assert response.data["points"][0]["price"] == 9000
