"""Deterministic checks are necessary gates, not proof of table semantics."""

import math
import re
from datetime import date

from .resource_schemas import Candidate, Document, Evidence, Issue, Quantity, ResourceRecord

ORE_FACTORS = {"Mt": 1_000_000.0, "kt": 1_000.0, "t": 1.0}
METAL_FACTORS = {
    "t": 1.0,
    "kt": 1_000.0,
    "Mt": 1_000_000.0,
    "oz": 1.0,
    "koz": 1_000.0,
    "Moz": 1_000_000.0,
}
UNIT_PATTERNS = {
    "Mt": r"\bMt\b|million\s+tonnes",
    "kt": r"\bkt\b|thousand\s+tonnes",
    "t": r"\bt\b|\btonnes\b",
    "g/t": r"g\s*/\s*t|grams\s+per\s+tonne",
    "%": r"%|percent",
    "oz": r"\boz\b|\bounces\b",
    "koz": r"\bkoz\b|thousand\s+ounces",
    "Moz": r"\bMoz\b|million\s+ounces",
}


def normalize(text: str) -> str:
    return " ".join(text.split())


def evidence_exists(evidence: Evidence, doc: Document) -> bool:
    return any(
        p.number == evidence.page and normalize(evidence.quote) in normalize(p.text)
        for p in doc.pages
    )


def number_exists(value: float, quote: str) -> bool:
    tokens = re.findall(r"(?<![\w.])-?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?![\w.])", quote)
    return any(
        math.isclose(float(t.replace(",", "")), value, rel_tol=1e-9, abs_tol=1e-9) for t in tokens
    )


def normalized_values(record: ResourceRecord) -> dict[str, float]:
    """Canonical ore Mt; grade as reported; Au oz, Cu/Li2O tonnes."""
    expected_grade = "g/t" if record.commodity == "Au" else "%"
    permitted_metal = {"oz", "koz", "Moz"} if record.commodity == "Au" else {"t", "kt", "Mt"}
    if record.grade.unit != expected_grade or record.contained_metal.unit not in permitted_metal:
        raise ValueError("Commodity and quantity units disagree")
    if record.ore.unit not in ORE_FACTORS:
        raise ValueError("Unsupported ore unit")
    return {
        "ore": record.ore.value * ORE_FACTORS[record.ore.unit] / 1_000_000,
        "grade": record.grade.value,
        "contained_metal": record.contained_metal.value
        * METAL_FACTORS[record.contained_metal.unit],
    }


def validate(
    candidate: Candidate, doc: Document, consistency_tolerance: float = 0.05
) -> list[Issue]:
    issues: list[Issue] = []

    def add(code: str, message: str, index: int | None = None, field: str | None = None) -> None:
        issues.append(Issue(code=code, message=message, record_index=index, field=field))

    if not candidate.records:
        add("empty", candidate.missing_reason or "No resource records extracted")
    if candidate.missing_reason:
        add("incomplete", candidate.missing_reason)
    seen: set[tuple[str, ...]] = set()
    for i, record in enumerate(candidate.records):
        if record.key() in seen:
            add("duplicate", "Duplicate record identity", i)
        seen.add(record.key())
        try:
            date.fromisoformat(record.effective_date)
        except ValueError:
            add("date", "Effective date is invalid", i)
        for evidence in [*record.identity_evidence, record.category_evidence]:
            if not evidence_exists(evidence, doc):
                add("evidence", "Identity/category quotation is absent from cited page", i)
        if not re.search(rf"\b{record.category}\b", record.category_evidence.quote, re.I):
            add("category", "Category is not supported by category quotation", i)
        if re.search(r"\b(proven|probable)\b", record.category_evidence.quote, re.I):
            add("reserves", "Reserve category cannot substitute for resource category", i)
        for field in ("ore", "grade", "contained_metal"):
            q: Quantity = getattr(record, field)
            if not evidence_exists(q.evidence, doc) or not evidence_exists(q.unit_evidence, doc):
                add("evidence", "Value/unit quotation is absent from cited page", i, field)
            if not number_exists(q.value, q.evidence.quote):
                add("value_evidence", "Reported value is absent from quotation", i, field)
            if not re.search(UNIT_PATTERNS[q.unit], q.unit_evidence.quote):
                add("unit_evidence", "Unit is absent from unit quotation", i, field)
        try:
            values = normalized_values(record)
        except ValueError as exc:
            add("units", str(exc), i)
            continue
        if record.grade.unit == "%" and record.grade.value > 100:
            add("grade", "Percentage exceeds 100", i, "grade")
        if values["ore"] <= 0:
            add("ore", "Resource tonnage must be positive", i, "ore")
        expected = values["ore"] * 1_000_000 * values["grade"]
        expected /= 31.1034768 if record.commodity == "Au" else 100
        if not math.isclose(
            values["contained_metal"], expected, rel_tol=consistency_tolerance, abs_tol=1e-8
        ):
            add(
                "mass_balance",
                "Contained quantity disagrees with tonnage × grade",
                i,
                "contained_metal",
            )
    return issues
