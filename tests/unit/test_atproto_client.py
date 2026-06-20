"""Atproto client retry and status mapping."""

import pytest

from bluesky_graph_analytics.infrastructure.bluesky.atproto_client import (
    AtprotoBlueskyClient,
    RateLimitError,
    ServerError,
    _extract_status_code,
)


def test_extract_status_code_from_attribute() -> None:
    class Err(Exception):
        status_code = 429

    assert _extract_status_code(Err()) == 429


def test_extract_status_code_from_message() -> None:
    assert _extract_status_code(Exception("HTTP 503 Service Unavailable")) == 503


@pytest.mark.asyncio
async def test_call_maps_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    client = AtprotoBlueskyClient("https://bsky.social")

    class Err429(Exception):
        status_code = 429

    async def boom(*args: object, **kwargs: object) -> None:
        raise Err429()

    monkeypatch.setattr(
        "bluesky_graph_analytics.infrastructure.bluesky.atproto_client.asyncio.to_thread",
        boom,
    )
    with pytest.raises(RateLimitError):
        await client._call(lambda: None)


@pytest.mark.asyncio
async def test_call_maps_server_error(monkeypatch: pytest.MonkeyPatch) -> None:
    client = AtprotoBlueskyClient("https://bsky.social")

    async def boom(*args: object, **kwargs: object) -> None:
        raise Exception("error 502 bad gateway")

    monkeypatch.setattr(
        "bluesky_graph_analytics.infrastructure.bluesky.atproto_client.asyncio.to_thread",
        boom,
    )
    with pytest.raises(ServerError):
        await client._call(lambda: None)
