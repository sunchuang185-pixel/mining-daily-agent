"""Bounded public HTTPS fetches. No cookies, credentials, local files or private hosts."""

import ipaddress
import socket
from urllib.parse import urljoin, urlparse

import httpx


class FetchError(ValueError):
    pass


def validate_public_url(url: str) -> None:
    parsed = urlparse(url)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.port not in {None, 443}
    ):
        raise FetchError("Only public HTTPS URLs without credentials are supported")
    try:
        addresses = socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise FetchError("Source DNS lookup failed") from exc
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise FetchError("Private, loopback and reserved network addresses are blocked")


async def fetch(url: str, max_bytes: int = 4_000_000) -> tuple[bytes, str]:
    current = url
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(25, connect=10),
        follow_redirects=False,
        headers={"User-Agent": "MiningDailyAgent/0.1 (public research; bounded requests)"},
    ) as client:
        for _ in range(4):
            validate_public_url(current)
            try:
                async with client.stream("GET", current) as response:
                    if response.status_code in {301, 302, 303, 307, 308}:
                        if "location" not in response.headers:
                            raise FetchError("Redirect has no location")
                        current = urljoin(current, response.headers["location"])
                        continue
                    if response.is_error:
                        raise FetchError(f"Source returned HTTP {response.status_code}")
                    chunks = bytearray()
                    async for chunk in response.aiter_bytes():
                        chunks.extend(chunk)
                        if len(chunks) > max_bytes:
                            raise FetchError("Source exceeds size limit")
                    return bytes(chunks), current
            except httpx.HTTPError as exc:
                raise FetchError("Source request failed or timed out") from exc
    raise FetchError("Source exceeded redirect limit")
