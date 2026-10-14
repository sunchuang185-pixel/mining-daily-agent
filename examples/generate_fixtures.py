"""生成可复现的合成测试样例，所有内容均非真实公司披露或市场行情。"""

import json
from io import BytesIO
from pathlib import Path

import pymupdf
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1] / "src/mining_daily/fixtures"
ROOT.mkdir(parents=True, exist_ok=True)


def save(name, data):
    (ROOT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def evidence(page, quote):
    return {"page": page, "quote": quote}


# 使用 PyMuPDF 内置的 Droid Sans Fallback 字体，PDF 嵌入字形子集。
pdfmetrics.registerFont(TTFont("DemoChinese", BytesIO(pymupdf.Font("china-s").buffer)))

context = [
    "项目：Pilbara 演示项目；矿区：合成测试矿区",
    "生效日期：2026-06-30；披露标准：JORC",
    "资源口径：包含储量；边界品位：0.2% Li2O",
]
header = "分类 | 矿石量 (Mt) | Li2O 品位 (%) | 所含 Li2O (t)"
rows = ["Indicated 100.0 1.2 1200000", "Inferred 50.0 0.9 450000"]
pdf = canvas.Canvas(str(ROOT / "resources.pdf"), pagesize=(595, 842), invariant=1)
pdf.setTitle("合成资源量样例 - 非公司报告")
pdf.setAuthor("矿权日报 Agent 测试样例")
pdf.setFillColor(HexColor("#14263D"))
pdf.setFont("DemoChinese", 20)
pdf.drawString(48, 775, "矿产资源量合成测试报告")
pdf.setFont("DemoChinese", 11)
pdf.drawString(48, 740, "仅用于软件测试 - 所有数据均为虚构")
pdf.setFillColor(HexColor("#334155"))
pdf.setFont("DemoChinese", 11)
for i, line in enumerate(context):
    pdf.drawString(48, 685 - 30 * i, line)
pdf.drawString(48, 540, "本样例用于验证 PDF 物理页码引用、资源分类和证据校验。")
pdf.drawString(48, 515, "本文件不属于 Pilbara Minerals、PLS 或任何公司的正式披露。")
pdf.drawString(48, 70, "PDF 物理页码：第 1 页，共 2 页")
pdf.showPage()
pdf.setFillColor(HexColor("#14263D"))
pdf.setFont("DemoChinese", 18)
pdf.drawString(48, 775, "矿产资源量 - 合成样例")
pdf.setFont("DemoChinese", 10)
pdf.drawString(48, 730, header)
pdf.setFont("DemoChinese", 12)
for i, row in enumerate(rows):
    pdf.drawString(48, 685 - 45 * i, row)
pdf.setFont("DemoChinese", 10)
pdf.drawString(48, 530, "资源量不等于储量。Li2O 表示氧化锂，不代表元素锂。")
pdf.drawString(48, 505, "数值经过简化，用于验证单位、引用证据和质量平衡。")
pdf.drawString(48, 70, "PDF 物理页码：第 2 页，共 2 页")
pdf.save()
records = []
for category, ore, grade, metal, row in [
    ("Indicated", 100.0, 1.2, 1200000.0, rows[0]),
    ("Inferred", 50.0, 0.9, 450000.0, rows[1]),
]:
    record = {
        "project": "Pilbara 演示项目",
        "deposit": "合成测试矿区",
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
            "title": "Pilbara 演示项目发布运营维护进展（合成新闻）",
            "url": "demo://news/operations",
            "published_at": "2026-10-13T08:00:00Z",
            "publisher": "合成测试数据",
            "summary": (
                "演示项目正在评估选矿设备的维护安排。此内容为软件测试虚构，不代表真实运营情况。"
            ),
        },
        {
            "title": "Pilbara 演示项目评估扩建时间表（合成新闻）",
            "url": "demo://news/expansion",
            "published_at": "2026-10-12T08:00:00Z",
            "publisher": "合成测试数据",
            "summary": "演示项目正在复核扩建阶段的施工计划。此内容为软件测试虚构，不属于公司公告。",
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
            "contract": "氢氧化锂合约（合成测试报价）",
            "source_url": "demo://prices/lithium",
            "synthetic": True,
        }
    )
save("prices.json", prices)
print(f"已生成合成测试样例，目录： {ROOT}")
