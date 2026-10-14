"""Strict contracts shared by model responses, rules and evaluation."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Evidence(StrictModel):
    page: int = Field(ge=1, strict=True)
    quote: str = Field(min_length=3)


class Quantity(StrictModel):
    value: float = Field(ge=0, strict=True)
    unit: Literal["Mt", "kt", "t", "g/t", "%", "oz", "koz", "Moz"]
    evidence: Evidence
    unit_evidence: Evidence


class ResourceRecord(StrictModel):
    project: str = Field(min_length=1)
    deposit: str = Field(min_length=1)
    effective_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    standard: Literal["NI 43-101", "JORC", "other"]
    category: Literal["Indicated", "Inferred"]
    commodity: Literal["Au", "Cu", "Li2O"]
    basis: Literal["inclusive_of_reserves", "exclusive_of_reserves", "not_stated"]
    cutoff: str = Field(min_length=1)
    identity_evidence: list[Evidence] = Field(min_length=1)
    category_evidence: Evidence
    ore: Quantity
    grade: Quantity
    contained_metal: Quantity

    def key(self) -> tuple[str, ...]:
        return (
            self.project,
            self.deposit,
            self.effective_date,
            self.standard,
            self.category,
            self.commodity,
            self.basis,
            self.cutoff,
        )


class Candidate(StrictModel):
    records: list[ResourceRecord]
    missing_reason: str = ""


class Issue(StrictModel):
    code: str
    message: str
    record_index: int | None = None
    field: str | None = None


class Page(StrictModel):
    number: int
    text: str


class Document(StrictModel):
    document_id: str
    filename: str
    page_count: int
    pages: list[Page]
    selection: str
