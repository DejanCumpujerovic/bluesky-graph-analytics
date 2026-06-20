"""Shared pytest fixtures."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from bluesky_graph_analytics.application.records import AnalysisRun, RunStatus
from bluesky_graph_analytics.config import AppSettings
from bluesky_graph_analytics.domain.models import FollowRelation, Profile
from bluesky_graph_analytics.domain.value_objects import DID, Handle, SnapshotId
from tests.fixtures.db import create_test_schema


@pytest.fixture
def test_settings(tmp_path: Path) -> AppSettings:
    from pathlib import Path as P

    salt = "a" * 32
    os.environ["PSEUDONYM_SALT"] = salt
    os.environ["BLUESKY_AUTH_TOKEN"] = "test-token"
    db_path = P(tmp_path) / "test.db"
    settings = AppSettings(
        pseudonym_salt=salt,
        bluesky_auth_token="test-token",
    )
    settings.storage.database_url = f"sqlite+aiosqlite:///{db_path}"
    return settings


@pytest.fixture
async def db_engine(test_settings: AppSettings) -> AsyncIterator[AsyncEngine]:
    engine = await create_test_schema(test_settings.storage.database_url)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session_factory(db_engine: AsyncEngine) -> async_sessionmaker:
    return async_sessionmaker(db_engine, expire_on_commit=False)


@pytest.fixture
async def seeded_run(
    session_factory: async_sessionmaker,
) -> tuple[SnapshotId, int]:
    from bluesky_graph_analytics.infrastructure.persistence.repositories import (
        SqlAlchemyFollowRepository,
        SqlAlchemyProfileRepository,
        SqlAlchemyRunRepository,
    )

    snap = SnapshotId("snap_test")
    runs = SqlAlchemyRunRepository(session_factory)
    profiles = SqlAlchemyProfileRepository(session_factory)
    follows = SqlAlchemyFollowRepository(session_factory)

    run = (
        await runs.create(
            AnalysisRun(
                started_at=datetime.now(UTC),
                snapshot_id=snap,
                status=RunStatus.COMPLETED,
                git_commit_hash="abc123",
                stats={"collection": {"duration_seconds": 10.0, "seeds_valid": 2}},
            )
        )
    ).unwrap()
    assert run.id is not None

    s1 = Profile(
        did=DID("did:plc:s1"), handle=Handle("s1.bsky.social"), is_seed=True, followers_count=100
    )
    s2 = Profile(
        did=DID("did:plc:s2"), handle=Handle("s2.bsky.social"), is_seed=True, followers_count=200
    )
    f1 = Profile(did=DID("did:plc:f1"), handle=Handle("f1.bsky.social"), followers_count=10)
    for p in (s1, s2, f1):
        await profiles.upsert(p, run_id=run.id)

    rels = [
        FollowRelation(follower_did=f1.did, followee_did=s1.did, snapshot_id=snap),
        FollowRelation(follower_did=f1.did, followee_did=s2.did, snapshot_id=snap),
        FollowRelation(follower_did=DID("did:plc:f2"), followee_did=s1.did, snapshot_id=snap),
        FollowRelation(follower_did=DID("did:plc:f2"), followee_did=s2.did, snapshot_id=snap),
        FollowRelation(follower_did=DID("did:plc:f3"), followee_did=s1.did, snapshot_id=snap),
        FollowRelation(follower_did=DID("did:plc:f3"), followee_did=s2.did, snapshot_id=snap),
    ]
    await follows.save_relations(rels)
    return snap, run.id
