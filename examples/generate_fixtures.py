"""Build reproducible synthetic fixtures. These are NOT company or market data."""

import json
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1] / "src/mining_daily/fixtures"
ROOT.mkdir(parents=True, exist_ok=True)


def save(name, data):
    (ROOT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def evidence(page, quote):
    return {"page": page, "quote": quote}


context = [
    "Project: Pilbara Demo; Deposit: Synthetic Deposit",
    "Effective date: 2026-06-30; Reporting standard: JORC",
    "Resource basis: inclusive of reserves; Cutoff: 0.2% Li2O",
]
header = "Category | Ore (Mt) | Li2O grade (%) | Contained Li2O (t)"
rows = ["Indicated 100.0 1.2 1200000", "Inferred 50.0 0.9 450000"]
pdf = canvas.Canvas(str(ROOT / "resources.pdf"), pagesize=(595, 842), invariant=1)
pdf.setTitle("Synthetic resource fixture - not a company report")
pdf.setAuthor("Mining Daily Agent test fixtures")
pdf.setFillColor(HexColor("#14263D"))
pdf.setFont("Helvetica-Bold", 20)
pdf.drawString(48, 775, "Synthetic resource report")
pdf.setFont("Helvetica-Bold", 11)
pdf.drawString(48, 740, "FOR SOFTWARE TESTING ONLY - ALL DATA IS INVENTED")
pdf.setFillColor(HexColor("#334155"))
pdf.setFont("Helvetica", 11)
for i, line in enumerate(context):
    pdf.drawString(48, 685 - 30 * i, line)
pdf.drawString(
    48, 540, "This fixture exercises physical page citations and resource classifications."
)
pdf.drawString(48, 515, "It is not a disclosure by Pilbara Minerals, PLS or any other company.")
pdf.drawString(48, 70, "Physical PDF page 1 of 2")
pdf.showPage()
pdf.setFillColor(HexColor("#14263D"))
pdf.setFont("Helvetica-Bold", 18)
pdf.drawString(48, 775, "Mineral Resources - synthetic example")
pdf.setFont("Helvetica-Bold", 10)
pdf.drawString(48, 730, header)
pdf.setFont("Helvetica", 12)
for i, row in enumerate(rows):
    pdf.drawString(48, 685 - 45 * i, row)
pdf.setFont("Helvetica", 10)
pdf.drawString(48, 530, "Resources are not Reserves. Li2O is lithium oxide, not elemental lithium.")
pdf.drawString(
    48, 505, "Numbers are intentionally simple to test units, evidence and mass balance."
)
pdf.drawString(48, 70, "Physical PDF page 2 of 2")
pdf.save()
records = []
for category, ore, grade, metal, row in [
    ("Indicated", 100.0, 1.2, 1200000.0, rows[0]),
    ("Inferred", 50.0, 0.9, 450000.0, rows[1]),
]:
    record = {
        "project": "Pilbara Demo",
        "deposit": "Synthetic Deposit",
        "effective_date": "2026-06-30",
        "standard": "JORC",
        "category": category,
        "commodity": "Li2O",
        "basis": "inclusive_of_reserves",
        "cutoff": "0.2% Li2O",
        "identity_evidence": [evidence(1, line) for line in context],
        "category_evidence": evidence(2, row),
    }
    for key, value, unit in [
        ("ore", ore, "Mt"),
        ("grade", grade, "%"),
        ("contained_metal", metal, "t"),
    ]:
        record[key] = {
            "value": value,
            "unit": unit,
            "evidence": evidence(2, row),
            "unit_evidence": evidence(2, header),
        }
    records.append(record)
save("resources.json", {"records": records, "missing_reason": ""})
save(
    "news.json",
    [
        {
            "title": "Pilbara Demo announces a synthetic operating update",
            "url": "demo://news/operations",
            "published_at": "2026-10-13T08:00:00Z",
            "publisher": "Synthetic fixture",
            "summary": "Synthetic maintenance review. Invented news for testing.",
        },
        {
            "title": "Pilbara Demo reviews synthetic expansion timetable",
            "url": "demo://news/expansion",
            "published_at": "2026-10-12T08:00:00Z",
            "publisher": "Synthetic fixture",
            "summary": "Synthetic expansion review. Not a real announcement.",
        },
    ],
)
prices = []
for day, value in [
    ("2026-10-08", 12.0),
    ("2026-10-09", 12.2),
    ("2026-10-12", 12.1),
    ("2026-10-13", 12.4),
    ("2026-10-14", 12.5),
]:
    prices.append(
        {
            "commodity": "lithium",
            "date": day,
            "price": value,
            "currency": "USD",
            "unit": "kg",
            "exchange": "LME",
            "contract": "SYNTHETIC lithium hydroxide contract fixture",
            "source_url": "demo://prices/lithium",
            "synthetic": True,
        }
    )
save("prices.json", prices)
print(f"Generated synthetic fixtures in {ROOT}")
