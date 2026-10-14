import asyncio
import socket

import pytest

from mining_daily.network import FetchError, validate_public_url
from mining_daily.news import canonical_url, parse_feed, search_news


def rss(entries):
    return (
        "<rss version='2.0'><channel><title>Fixture</title>"
        + "".join(
            f"<item><title>{title}</title><link>https://example.org/{i}</link>"
            f"<pubDate>{stamp}</pubDate><description>Fixture summary</description></item>"
            for i, (title, stamp) in enumerate(entries)
        )
        + "</channel></rss>"
    ).encode()


def test_news_filters_dates_and_project():
    data = rss(
        [
            ("Pilbara operating update", "Tue, 13 Oct 2026 08:00:00 GMT"),
            ("Pilbara old update", "Tue, 01 Sep 2026 08:00:00 GMT"),
            ("Another miner lithium update", "Tue, 13 Oct 2026 08:00:00 GMT"),
            ("Pilbara future update", "Thu, 15 Oct 2026 08:00:00 GMT"),
        ]
    )
    assert [x.title for x in parse_feed(data, "Pilbara", 7)] == ["Pilbara operating update"]


def test_news_window_uses_shanghai_midnight():
    data = rss(
        [
            ("Pilbara before midnight", "Wed, 14 Oct 2026 15:59:59 GMT"),
            ("Pilbara next day", "Wed, 14 Oct 2026 16:00:00 GMT"),
        ]
    )
    assert len(parse_feed(data, "Pilbara", 1)) == 1


def test_demo_no_matching_news_is_not_a_false_claim():
    response = asyncio.run(search_news("unrelated-project", 7))
    assert response.status == "partial"
    assert not response.data["items"]


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "http://example.org",
        "https://user:secret@example.org",
        "https://example.org:8080",
        "demo://private",
    ],
)
def test_unsafe_url_rejected(url):
    with pytest.raises(FetchError):
        validate_public_url(url)


def test_private_dns_rejected(monkeypatch):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))],
    )
    with pytest.raises(FetchError, match="Private"):
        validate_public_url("https://public-looking.example")


def test_tracking_parameters_are_deduplicated():
    assert (
        canonical_url("https://EXAMPLE.org/article/?utm_source=a#x")
        == "https://example.org/article"
    )


def test_query_identifiers_are_not_deduplicated():
    assert canonical_url("https://example.org/news?id=1") != canonical_url(
        "https://example.org/news?id=2"
    )


def test_project_alias_matches_new_company_name():
    data = rss([("PLS announces Pilgangoora update", "Tue, 13 Oct 2026 08:00:00 GMT")])
    assert len(parse_feed(data, "Pilbara", 7)) == 1
