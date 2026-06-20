"""Atproto client success paths with mocked SDK."""

from unittest.mock import MagicMock, patch

import pytest

from bluesky_graph_analytics.domain.value_objects import DID, Handle, SnapshotId
from bluesky_graph_analytics.infrastructure.bluesky.atproto_client import AtprotoBlueskyClient


@pytest.mark.asyncio
async def test_resolve_and_fetch_profile() -> None:
    client = AtprotoBlueskyClient("https://bsky.social", auth_token="t")
    mock_client = MagicMock()
    mock_client.resolve_handle.return_value = MagicMock(did="did:plc:abc")
    mock_client.app.bsky.actor.get_profile.return_value = MagicMock(
        did="did:plc:abc",
        handle="u.bsky.social",
        display_name="U",
        description="bio",
        followers_count=1,
        follows_count=2,
        posts_count=3,
    )

    with (
        patch.object(client, "_get_client", return_value=mock_client),
        patch(
            "bluesky_graph_analytics.infrastructure.bluesky.atproto_client.asyncio.to_thread",
            side_effect=lambda fn, *a, **k: fn(*a, **k),
        ),
    ):
        did = (await client.resolve_handle(Handle("u.bsky.social"))).unwrap()
        assert str(did) == "did:plc:abc"
        prof = (await client.fetch_profile(DID("did:plc:abc"))).unwrap()
        assert prof.followers_count == 1


@pytest.mark.asyncio
async def test_fetch_followers_page() -> None:
    client = AtprotoBlueskyClient("https://bsky.social", auth_token="t")
    mock_client = MagicMock()
    follower = MagicMock(
        did="did:plc:f",
        handle="f.bsky.social",
        display_name=None,
        followers_count=1,
        follows_count=0,
        posts_count=0,
    )
    mock_client.app.bsky.graph.get_followers.return_value = MagicMock(
        followers=[follower], cursor=None
    )

    with (
        patch.object(client, "_get_client", return_value=mock_client),
        patch(
            "bluesky_graph_analytics.infrastructure.bluesky.atproto_client.asyncio.to_thread",
            side_effect=lambda fn, *a, **k: fn(*a, **k),
        ),
    ):
        result = await client.fetch_followers_page(
            DID("did:plc:seed"),
            snapshot_id=SnapshotId("snap"),
            limit=10,
            cursor=None,
        )
        rels, _profs, cursor = result.unwrap()
        assert len(rels) == 1
        assert cursor is None
