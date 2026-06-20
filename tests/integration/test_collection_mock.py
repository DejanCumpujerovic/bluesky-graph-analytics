"""Collection with fake Atproto client."""

import pytest
from returns.result import Failure, Success
from sqlalchemy.ext.asyncio import async_sessionmaker

from bluesky_graph_analytics.application.dto import CollectRequestDTO
from bluesky_graph_analytics.application.services.collection_service import CollectionService
from bluesky_graph_analytics.domain.models import FollowRelation, Profile
from bluesky_graph_analytics.domain.value_objects import DID, Handle, SnapshotId
from bluesky_graph_analytics.infrastructure.bluesky.atproto_client import (
    AtprotoBlueskyClient,
    FollowerPageResult,
    TerminationReason,
)
from bluesky_graph_analytics.infrastructure.persistence.repositories import (
    SqlAlchemyDeletionRepository,
    SqlAlchemyFollowRepository,
    SqlAlchemyProfileRepository,
    SqlAlchemyRunRepository,
)


class FakeAtproto(AtprotoBlueskyClient):
    def __init__(self) -> None:
        super().__init__("https://bsky.social", auth_token="x")

    async def resolve_handle(self, handle: Handle):
        return Success(DID(f"did:plc:{handle}".replace(".", "_")))

    async def fetch_profile(self, did: DID):
        return Success(
            Profile(
                did=did,
                handle=Handle("seed.bsky.social"),
                followers_count=100,
                is_seed=True,
            )
        )

    async def fetch_followers_paginated(
        self,
        did: DID,
        *,
        snapshot_id: SnapshotId,
        max_followers: int,
        max_pages: int,
        page_size: int,
    ):
        _ = (max_followers, max_pages, page_size)
        follower = DID("did:plc:follower1")
        return Success(
            FollowerPageResult(
                relations=[
                    FollowRelation(
                        follower_did=follower,
                        followee_did=did,
                        snapshot_id=snapshot_id,
                    )
                ],
                profiles=[Profile(did=follower, followers_count=5)],
                reason=TerminationReason.CURSOR_EXHAUSTED,
                pages_fetched=1,
            )
        )


@pytest.mark.asyncio
async def test_collect_one_valid_seed(
    session_factory: async_sessionmaker,
    test_settings,
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "bluesky_graph_analytics.application.services.collection_service.load_seed_file",
        lambda _s: Success(_minimal_seed_file()),
    )
    svc = CollectionService(
        FakeAtproto(),
        SqlAlchemyProfileRepository(session_factory),
        SqlAlchemyFollowRepository(session_factory),
        SqlAlchemyDeletionRepository(session_factory),
        SqlAlchemyRunRepository(session_factory),
        test_settings,
    )
    result = await svc.collect(
        CollectRequestDTO(
            seed_handles=[Handle("seed.bsky.social")],
            snapshot_id=SnapshotId("snap_collect"),
        )
    )
    assert not isinstance(result, Failure)
    data = result.unwrap()
    assert data["seeds_collected"] == 1


def _minimal_seed_file():
    from bluesky_graph_analytics.domain.seeds.seed_file import SeedEntry, SeedFile

    return SeedFile(seeds=[SeedEntry(handle=Handle("seed.bsky.social"), topic="t")])
