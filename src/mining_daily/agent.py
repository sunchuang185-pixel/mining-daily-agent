import asyncio
import re
from datetime import date
from typing import Any

from .client import MCPTools
from .contracts import BriefPlan, ToolResponse
from .settings import mode, today


def make_plan(
    prompt: str,
    project: str | None = None,
    commodity: str | None = None,
    days: int = 7,
    as_of: date | None = None,
    pdf_url: str | None = None,
) -> BriefPlan:
    if project is None:
        if re.search(r"pilbara|pilgangoora|皮尔巴拉", prompt, re.I):
            project = "Pilbara"
        else:
            raise ValueError("Unknown project: supply --project and --commodity explicitly")
    if commodity is None:
        for value, pattern in (
            ("lithium", r"lithium|锂|pilbara|pilgangoora"),
            ("copper", r"copper|铜"),
            ("zinc", r"zinc|锌"),
            ("nickel", r"nickel|镍"),
        ):
            if re.search(pattern, prompt + " " + project, re.I):
                commodity = value
                break
    if commodity is None:
        raise ValueError("Cannot identify commodity; supply --commodity")
    if pdf_url is None and mode() == "demo" and project.lower() == "pilbara":
        pdf_url = "demo://pilbara-resources.pdf"
    return BriefPlan.model_validate(
        {
            "project": project,
            "commodity": commodity,
            "days": days,
            "as_of": as_of or today(),
            "pdf_url": pdf_url,
        }
    )


async def run_agent(plan: BriefPlan) -> dict[str, Any]:
    async with MCPTools(as_of=plan.as_of) as tools:
        news, quote, trend = await asyncio.gather(
            tools.call("mining-news-mcp", "search", {"query": plan.project, "days": plan.days}),
            tools.call(
                "lme-price-mcp",
                "get_price",
                {"commodity": plan.commodity, "date": plan.as_of.isoformat()},
            ),
            tools.call(
                "lme-price-mcp", "get_trend", {"commodity": plan.commodity, "days": plan.days}
            ),
        )
        articles = []
        # Bounded plan; arbitrary instructions in article text cannot schedule extra tool calls.
        for item in news.data.get("items", [])[:3]:
            article = await tools.call("mining-news-mcp", "fetch_article", {"url": item["url"]})
            articles.append({"item": item, "article": article.model_dump(mode="json")})
        pdf_url = plan.pdf_url
        if pdf_url is None:
            for item in articles:
                links = item["article"]["data"].get("pdf_urls", [])
                if links:
                    pdf_url = links[0]
                    break
        resources = (
            await tools.call("mineral-pdf-mcp", "extract_resources", {"pdf_url": pdf_url})
            if pdf_url
            else ToolResponse(
                status="unavailable",
                mode=mode(),
                warnings=[
                    "No resource PDF located; supply --pdf-url with a verified technical report",
                ],
            )
        )
        return {
            "schema_version": "1.0",
            "mode": mode(),
            "plan": plan.model_dump(mode="json"),
            "news": news.model_dump(mode="json"),
            "articles": articles,
            "resources": resources.model_dump(mode="json"),
            "price": quote.model_dump(mode="json"),
            "trend": trend.model_dump(mode="json"),
            "discovered_tools": tools.discovered,
            "trace": [t.model_dump(mode="json") for t in tools.trace],
        }
