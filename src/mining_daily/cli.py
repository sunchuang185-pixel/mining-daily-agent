import asyncio
import json
import os
import sys
from datetime import date
from pathlib import Path

import typer

from .agent import make_plan, run_agent
from .client import SERVERS, MCPTools
from .report import render_report
from .settings import DEMO_DATE

app = typer.Typer(help="矿权日报 Agent：3 个 MCP Server、可追溯证据与明确降级。")


@app.command()
def brief(
    prompt: str = typer.Argument("给我生成一份关于 Pilbara 锂矿的今日简报"),
    mode: str = typer.Option("demo", help="demo：离线演示；live：真实数据"),
    project: str | None = None,
    commodity: str | None = None,
    days: int = 7,
    as_of: str | None = None,
    pdf_url: str | None = None,
    output: Path = Path("runs/brief.md"),
) -> None:
    """生成 Markdown 日报，以及包含证据和 MCP 调用记录的 JSON 文件。"""
    if mode not in {"demo", "live"}:
        raise typer.BadParameter("mode 须为 demo 或 live")
    os.environ["MINING_MODE"] = mode
    if as_of:
        try:
            date.fromisoformat(as_of)
        except ValueError as exc:
            raise typer.BadParameter("as-of 日期格式须为 YYYY-MM-DD") from exc
        os.environ["MINING_AS_OF"] = as_of
    elif mode == "demo":
        os.environ["MINING_AS_OF"] = DEMO_DATE.isoformat()
    else:
        os.environ.pop("MINING_AS_OF", None)
    try:
        plan = make_plan(prompt, project, commodity, days, pdf_url=pdf_url)
        result = asyncio.run(run_agent(plan))
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_report(result), encoding="utf-8")
    output.with_suffix(".json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    typer.echo(f"日报：{output}\n证据：{output.with_suffix('.json')}\n运行模式：{mode}")


@app.command()
def doctor() -> None:
    """初始化三个服务并列出实际可用的 MCP 工具（不访问外部数据源）。"""

    async def inspect() -> dict[str, list[str]]:
        async with MCPTools() as tools:
            return tools.discovered

    typer.echo(json.dumps(asyncio.run(inspect()), ensure_ascii=False, indent=2))


@app.command("mcp-config")
def mcp_config(output: Path = Path("mcp-config.json"), mode: str = "demo") -> None:
    """生成 Claude Desktop / Cursor stdio 配置，使用当前 Python 解释器的绝对路径。"""
    if mode not in {"demo", "live"}:
        raise typer.BadParameter("mode 须为 demo 或 live")
    data = {
        "mcpServers": {
            name: {"command": sys.executable, "args": ["-m", module], "env": {"MINING_MODE": mode}}
            for name, (module, _) in SERVERS.items()
        }
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2), encoding="utf-8")
    typer.echo(str(output))


if __name__ == "__main__":
    app()
