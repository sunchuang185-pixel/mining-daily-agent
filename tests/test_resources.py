import asyncio

import pymupdf
import pytest
from pydantic import ValidationError

from mining_daily.pdf_reader import EvidenceError, read_pdf
from mining_daily.resource_schemas import Candidate, Evidence
from mining_daily.resource_validation import normalized_values, number_exists, validate
from mining_daily.resources import extract_resources


def codes(candidate, document):
    return {issue.code for issue in validate(candidate, document)}


def test_real_pdf_parsing_and_citations(document, candidate):
    assert document.page_count == 2
    assert [p.number for p in document.pages] == [1, 2]
    assert not validate(candidate, document)


@pytest.mark.parametrize("field", ["ore", "grade", "contained_metal"])
def test_fabricated_number_rejected(candidate, document, field):
    getattr(candidate.records[0], field).value = 9999
    assert "value_evidence" in codes(candidate, document)


def test_wrong_page_rejected(candidate, document):
    candidate.records[0].ore.evidence.page = 99
    assert "evidence" in codes(candidate, document)


def test_category_swap_rejected(candidate, document):
    candidate.records[0].category = "Inferred"
    assert "category" in codes(candidate, document)


def test_resource_reserve_confusion_rejected(candidate, document):
    candidate.records[0].category_evidence = Evidence(page=2, quote="Proven Indicated")
    assert "reserves" in codes(candidate, document)


def test_unit_scale_error_rejected(candidate, document):
    candidate.records[0].ore.unit = "kt"
    assert {"unit_evidence", "mass_balance"} <= codes(candidate, document)


def test_duplicate_identity_rejected(candidate, document):
    candidate.records.append(candidate.records[0].model_copy(deep=True))
    assert "duplicate" in codes(candidate, document)


def test_missing_data_never_passes(candidate, document):
    candidate.missing_reason = "Could not read one required row"
    assert "incomplete" in codes(candidate, document)
    assert "empty" in codes(Candidate(records=[]), document)


def test_gold_and_copper_conversion(candidate):
    record = candidate.records[0]
    record.commodity = "Au"
    record.grade.unit = "g/t"
    record.contained_metal.unit = "koz"
    record.contained_metal.value = 10
    assert normalized_values(record)["contained_metal"] == 10000
    record.commodity = "Cu"
    with pytest.raises(ValueError):
        normalized_values(record)
    record.grade.unit = "%"
    record.contained_metal.unit = "Mt"
    assert normalized_values(record)["contained_metal"] == 10_000_000


def test_nan_is_rejected(candidate):
    data = candidate.model_dump()
    data["records"][0]["grade"]["value"] = float("nan")
    with pytest.raises(ValidationError):
        Candidate.model_validate(data)


def test_number_matching_has_token_boundaries():
    assert not number_exists(12, "Indicated 120 1.2")
    assert number_exists(1200000, "Indicated 1,200,000")
    assert not number_exists(12, "Indicated -12")


def test_unreadable_pdf_abstains(tmp_path):
    path = tmp_path / "blank.pdf"
    with pymupdf.open() as pdf:
        pdf.new_page()
        pdf.save(path)
    with pytest.raises(EvidenceError, match="No readable"):
        read_pdf(path)


def test_context_budget_never_silently_truncates(document, tmp_path):
    from conftest import FIXTURES

    with pytest.raises(EvidenceError, match="context limit"):
        read_pdf(FIXTURES / "resources.pdf", max_chars=20)


def test_demo_tool_checks_pdf_and_returns_sources():
    response = asyncio.run(extract_resources("demo://pilbara-resources.pdf"))
    assert response.status == "ok"
    assert len(response.data["records"]) == 2
    assert len(response.data["document_id"]) == 64
    assert response.mode == "demo"


def test_live_never_uses_demo_fixture(monkeypatch):
    monkeypatch.setenv("MINING_MODE", "live")
    response = asyncio.run(extract_resources("demo://pilbara-resources.pdf"))
    assert response.status == "unavailable"
    assert not response.data.get("records")
