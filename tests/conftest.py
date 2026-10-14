from pathlib import Path

import pytest

from mining_daily.pdf_reader import read_pdf
from mining_daily.resource_schemas import Candidate
from mining_daily.settings import fixture

FIXTURES = Path(__file__).resolve().parents[1] / "src/mining_daily/fixtures"


@pytest.fixture(autouse=True)
def isolated_settings(monkeypatch):
    monkeypatch.setenv("MINING_MODE", "demo")
    monkeypatch.setenv("MINING_AS_OF", "2026-10-14")
    for name in ("LME_PRICE_CSV", "LME_PRICE_JSON_URL", "EXTRACTOR_API_KEY"):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def document():
    return read_pdf(FIXTURES / "resources.pdf")


@pytest.fixture
def candidate():
    return Candidate.model_validate(fixture("resources.json"))
