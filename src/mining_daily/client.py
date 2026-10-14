"""Actual MCP initialize/list_tools/call_tool over three independent stdio processes."""

import json
import os
import sys
import time
from contextlib import AsyncExitStack
from datetime import date, timedelta
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from .contracts import CallTrace, ToolResponse
from .settings import mode

SERVERS = {
    "mining-news-mcp": ("mining_daily.servers.news", {"search", "fetch_article"}),
    "mineral-pdf-mcp": ("mining_daily.servers.pdf", {"extract_resources"}),
    "lme-price-mcp": ("mining_daily.servers.prices", {"get_price", "get_trend"}),
}


def server_env(name: str) -> dict[str, str]:
    common = {"PATH", "PYTHONPATH", "MINING_MODE", "MINING_AS_OF", "SSL_CERT_FILE"}
    extra = {
        "mining-news-mcp": {"NEWS_RSS_URLS"},
        "mineral-pdf-mcp": {
            "EXTRACTOR_MODEL",
            "EXTRACTOR_BASE_URL",
            "EXTRACTOR_API_KEY",
            "MODEL_TIMEOUT_SECONDS",
            "MODEL_MAX_ATTEMPTS",
        },
        "lme-price-mcp": {"LME_PRICE_CSV", "LME_PRICE_JSON_URL"},
    }[name]
    return {k: v for k, v in os.environ.items() if k in common | extra}


class MCPTools:
    def __init__(self, as_of: date | None = None) -> None:
        self.stack = AsyncExitStack()
        self.as_of = as_of
        self.sessions: dict[str, ClientSession] = {}
        self.trace: list[CallTrace] = []
        self.discovered: dict[str, list[str]] = {}

    async def __aenter__(self) -> "MCPTools":
        await self.stack.__aenter__()
        try:
            for name, (module, required) in SERVERS.items():
                environment = server_env(name)
                if self.as_of:
                    environment["MINING_AS_OF"] = self.as_of.isoformat()
                streams = await self.stack.enter_async_context(
                    stdio_client(
                        StdioServerParameters(
                            command=sys.executable,
                            args=["-m", module],
                            env=environment,
                        )
                    )
                )
                session = await self.stack.enter_async_context(
                    ClientSession(
                        streams[0],
                        streams[1],
                        read_timeout_seconds=timedelta(seconds=210),
                    )
                )
                await session.initialize()
                tools = await session.list_tools()
                self.discovered[name] = sorted(tool.name for tool in tools.tools)
                if not required.issubset(self.discovered[name]):
                    raise RuntimeError(f"{name} is missing required tools")
                self.sessions[name] = session
            return self
        except BaseException:
            await self.stack.aclose()
            raise

    async def __aexit__(self, *args: Any) -> None:
        await self.stack.aclose()

    async def call(self, server: str, tool: str, arguments: dict[str, Any]) -> ToolResponse:
        if server not in SERVERS or tool not in SERVERS[server][1]:
            raise ValueError("Tool is outside the fixed task plan")
        started = time.monotonic()
        try:
            result = await self.sessions[server].call_tool(tool, arguments)
            if result.isError:
                response = ToolResponse(
                    status="error", mode=mode(), warnings=["MCP tool execution failed"]
                )
            else:
                raw = result.structuredContent
                if raw is None:
                    text = next(item.text for item in result.content if item.type == "text")
                    raw = json.loads(text)
                response = ToolResponse.model_validate(raw)
                if response.mode != mode():
                    response = ToolResponse(
                        status="error",
                        mode=mode(),
                        warnings=["Tool mode mismatch; result discarded"],
                    )
        except Exception as exc:
            response = ToolResponse(
                status="error", mode=mode(), warnings=[f"MCP call failed: {type(exc).__name__}"]
            )
        self.trace.append(
            CallTrace(
                server=server,
                tool=tool,
                arguments=arguments,
                response=response,
                elapsed_seconds=round(time.monotonic() - started, 3),
            )
        )
        return response
