import asyncio
import json

import pytest
from typer.testing import CliRunner

from mining_daily.agent import make_plan, run_agent
from mining_daily.cli import app
from mining_daily.client import MCPTools, server_env
from mining_daily.report import render_report


@pytest.fixture(scope="module")
def demo_result():
    import os

    os.environ["MINING_MODE"] = "demo"
    return asyncio.run(run_agent(make_plan("给我生成一份关于 Pilbara 锂矿的今日简报")))


def test_end_to_end_real_mcp_processes(demo_result):
    assert demo_result["discovered_tools"] == {
        "mining-news-mcp": ["fetch_article", "search"],
        "mineral-pdf-mcp": ["extract_resources"],
        "lme-price-mcp": ["get_price", "get_trend"],
    }
    assert len(demo_result["trace"]) == 6
    assert all(t["response"]["status"] == "ok" for t in demo_result["trace"])
    assert len(demo_result["resources"]["data"]["records"]) == 2


def test_report_labels_synthetic_and_contract_basis(demo_result):
    report = render_report(demo_result)
    assert "合成样例" in report
    assert "+4.17%" in report
    assert "JORC" in report
    assert "不能称为 NI 43-101" in report
    assert "锂辉石精矿" in report
    assert "[S1]" in report


def test_other_project_pdf_not_used(demo_result):
    data = json.loads(json.dumps(demo_result))
    data["plan"]["project"] = "Other Mine"
    report = render_report(data)
    assert "已隐藏资源数值" in report
    assert "| Synthetic Deposit" not in report


def test_source_markup_cannot_inject_html(demo_result):
    data = json.loads(json.dumps(demo_result))
    data["articles"][0]["item"]["title"] = "<script>alert(1)</script> [click](javascript:evil)"
    report = render_report(data)
    assert "<script>" not in report
    assert "\\[click\\]" in report


def test_unknown_project_requires_explicit_scope():
    with pytest.raises(ValueError, match="Unknown project"):
        make_plan("随便写一些矿业新闻")


def test_credentials_are_scoped_to_pdf_server(monkeypatch):
    monkeypatch.setenv("EXTRACTOR_API_KEY", "test-secret")
    monkeypatch.setenv("UNRELATED_SECRET", "not-for-child")
    assert "EXTRACTOR_API_KEY" not in server_env("mining-news-mcp")
    assert "EXTRACTOR_API_KEY" in server_env("mineral-pdf-mcp")
    assert "UNRELATED_SECRET" not in server_env("mineral-pdf-mcp")


def test_cli_writes_both_outputs(tmp_path):
    result = CliRunner().invoke(app, ["brief", "--output", str(tmp_path / "brief.md")])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "brief.md").is_file()
    assert json.loads((tmp_path / "brief.json").read_text())["mode"] == "demo"


def test_config_generation_uses_absolute_interpreter(tmp_path):
    path = tmp_path / "mcp.json"
    result = CliRunner().invoke(app, ["mcp-config", "--output", str(path)])
    assert result.exit_code == 0
    for server in json.loads(path.read_text())["mcpServers"].values():
        assert server["command"].startswith("/")


def test_invalid_mcp_input_returns_error_without_killing_session():
    async def check():
        async with MCPTools() as client:
            bad = await client.call(
                "lme-price-mcp", "get_trend", {"commodity": "lithium", "days": -2}
            )
            good = await client.call(
                "lme-price-mcp", "get_trend", {"commodity": "lithium", "days": 7}
            )
            assert bad.status == "error"
            assert good.status == "ok"

    asyncio.run(check())
