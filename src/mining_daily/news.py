import asyncio
import calendar
import os
import re
from datetime import UTC, datetime, time, timedelta
from typing import Literal
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse
from zoneinfo import ZoneInfo

import feedparser
import trafilatura
from lxml import html

from .contracts import NewsItem, ToolResponse
from .network import FetchError, fetch
from .settings import fixture, mode, today


def canonical_url(url: str) -> str:
    parsed = urlparse(url)
    query = [
        (k, v)
        for k, v in parse_qsl(parsed.query)
        if not k.lower().startswith("utm_") and k.lower() not in {"gclid", "fbclid"}
    ]
    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc.lower(),
            parsed.path.rstrip("/"),
            "",
            urlencode(sorted(query)),
            "",
        )
    )


def relevant(query: str, text: str) -> bool:
    if query.casefold() in {"pilbara", "pilgangoora", "皮尔巴拉"}:
        return bool(re.search(r"\b(pilbara|pilgangoora|pls)\b|皮尔巴拉", text, re.I))
    tokens = [t for t in re.findall(r"[a-zA-Z0-9]+", query.lower()) if len(t) >= 3]
    if not tokens:
        return query.lower() in text.lower()
    # Project token is mandatory. Broader commodity terms alone cannot match another miner.
    return tokens[0] in text.lower()


def parse_feed(blob: bytes, query: str, days: int) -> list[NewsItem]:
    result = []
    end = datetime.combine(today() + timedelta(days=1), time.min, ZoneInfo("Asia/Shanghai"))
    start = end - timedelta(days=days)
    for entry in feedparser.parse(blob).entries:
        stamp = entry.get("published_parsed") or entry.get("updated_parsed")
        if not stamp or not entry.get("link"):
            continue
        published = datetime.fromtimestamp(calendar.timegm(stamp), UTC)
        title = str(entry.get("title", ""))
        summary_html = str(entry.get("summary", ""))
        summary = html.fromstring(f"<div>{summary_html}</div>").text_content()
        if start <= published < end and relevant(query, title + " " + summary):
            result.append(
                NewsItem(
                    title=title,
                    url=str(entry.link),
                    published_at=published,
                    summary=summary[:800],
                    publisher=urlparse(str(entry.link)).hostname or "unknown",
                )
            )
    return result


async def search_news(query: str, days: int) -> ToolResponse:
    if not query.strip() or len(query) > 200 or not 1 <= days <= 90:
        raise ValueError("query must be 1–200 characters and days must be 1–90")
    warnings: list[str] = []
    if mode() == "demo":
        items = [NewsItem.model_validate(x) for x in fixture("news.json")]
        start = today() - timedelta(days=days - 1)
        items = [
            x
            for x in items
            if start <= x.published_at.date() <= today() and relevant(query, x.title)
        ]
        sources = [x.url for x in items]
        warnings.append("SYNTHETIC_DEMO: fixtures are invented, not current market news")
    else:
        feeds = os.getenv("NEWS_RSS_URLS", "https://www.mining.com/feed/").split(",")
        if len(feeds) > 5:
            raise ValueError("At most 5 RSS feeds are supported")
        responses = await asyncio.gather(*(fetch(u.strip()) for u in feeds), return_exceptions=True)
        items, sources = [], []
        for response in responses:
            if isinstance(response, BaseException):
                warnings.append(f"RSS unavailable: {type(response).__name__}")
                continue
            blob, source = response
            sources.append(source)
            items.extend(parse_feed(blob, query, days))
    unique = {canonical_url(x.url): x for x in sorted(items, key=lambda x: x.published_at)}
    selected = sorted(unique.values(), key=lambda x: x.published_at, reverse=True)[:10]
    status: Literal["ok", "partial"] = (
        "ok" if selected and not (mode() == "live" and warnings) else "partial"
    )
    if not selected:
        warnings.append(
            "No dated matching entries in the configured feeds; this is not proof of no news"
        )
    return ToolResponse(
        status=status,
        mode=mode(),
        data={"items": [x.model_dump(mode="json") for x in selected]},
        warnings=warnings,
        sources=sources,
    )


async def fetch_article(url: str) -> ToolResponse:
    if mode() == "demo":
        item = next((x for x in fixture("news.json") if x["url"] == url), None)
        if item is None:
            return ToolResponse(status="unavailable", mode="demo", warnings=["Unknown demo URL"])
        return ToolResponse(
            status="ok",
            mode="demo",
            data={
                "title": item["title"],
                "text": item["summary"],
                "pdf_urls": [],
            },
            warnings=["SYNTHETIC_DEMO"],
            sources=[url],
        )
    try:
        blob, final_url = await fetch(url)
        text = trafilatura.extract(blob, include_comments=False, include_tables=False) or ""
        tree = html.fromstring(blob)
        pdfs = [
            urljoin(final_url, str(link))
            for link in tree.xpath("//a/@href")
            if urlparse(str(link)).path.lower().endswith(".pdf")
        ]
        if len(text.strip()) < 100:
            return ToolResponse(
                status="unavailable",
                mode="live",
                warnings=["Readable article body unavailable; paywalls are not bypassed"],
                sources=[final_url],
            )
        return ToolResponse(
            status="ok",
            mode="live",
            data={"text": text[:20_000], "pdf_urls": pdfs[:5]},
            sources=[final_url],
        )
    except (FetchError, ValueError) as exc:
        return ToolResponse(status="unavailable", mode="live", warnings=[str(exc)], sources=[url])
