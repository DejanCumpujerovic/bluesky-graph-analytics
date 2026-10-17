"""Atproto client retry and status mapping."""

from types import SimpleNamespace

import pytest
from returns.result import Success

from bluesky_graph_analytics.domain.value_objects import DID, SnapshotId
from bluesky_graph_analytics.infrastructure.bluesky.atproto_client import (
    AtprotoBlueskyClient,
    RateLimitError,
    ServerError,
    _extract_status_code,
    _optional_int,
)


def test_optional_int_missing_attr() -> None:
    assert _optional_int(SimpleNamespace(), "followers_count") == 0


def test_optional_int_present() -> None:
    assert _optional_int(SimpleNamespace(followers_count=42), "followers_count") == 42


@pytest.mark.asyncio
async def test_fetch_followers_page_accepts_profile_view_without_counts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Bluesky getFollowers returns ProfileView without followers_count."""
    client = AtprotoBlueskyClient("https://bsky.social")
    follower = SimpleNamespace(
        did="did:plc:follower1",
        handle="fan.bsky.social",
        display_name="Fan",
        description="hello",
    )
    resp = SimpleNamespace(followers=[follower], cursor=None)

    async def fake_call(fn: object, *args: object, **kwargs: object) -> object:
        return resp

    graph = SimpleNamespace(get_followers=object())
    sdk = SimpleNamespace(app=SimpleNamespace(bsky=SimpleNamespace(graph=graph)))
    monkeypatch.setattr(client, "_call", fake_call)
    monkeypatch.setattr(client, "_get_client", lambda: sdk)

    result = await client.fetch_followers_page(
        DID("did:plc:seed"),
        snapshot_id=SnapshotId("snap"),
        limit=50,
        cursor=None,
    )
    assert isinstance(result, Success)
    relations, profiles, cursor = result.unwrap()
    assert cursor is None
    assert len(relations) == 1
    assert profiles[0].followers_count == 0
    assert profiles[0].handle == "fan.bsky.social"


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
