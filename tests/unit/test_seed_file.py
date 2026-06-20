from pathlib import Path

import pytest

from bluesky_graph_analytics.domain.seeds.seed_file import (
    SeedFileLoader,
    SeedFileValidationError,
)
from bluesky_graph_analytics.domain.value_objects import DID, Handle


def test_seed_file_rejects_duplicate_handles(tmp_path: Path) -> None:
    path = tmp_path / "seeds.yaml"
    path.write_text(
        """
seeds:
  - handle: "a.bsky.social"
    topic: "t1"
  - handle: "a.bsky.social"
    topic: "t2"
""",
        encoding="utf-8",
    )
    with pytest.raises(SeedFileValidationError, match="Duplicate handle"):
        SeedFileLoader(enforce_mvp_bounds=False).load(path)


def test_seed_file_mvp_bounds(tmp_path: Path) -> None:
    path = tmp_path / "seeds.yaml"
    path.write_text(
        """
seeds:
  - handle: "only.one"
    topic: "t"
""",
        encoding="utf-8",
    )
    with pytest.raises(SeedFileValidationError, match="MVP requires"):
        SeedFileLoader(enforce_mvp_bounds=True).load(path)


def test_seed_file_loads_known_did(tmp_path: Path) -> None:
    path = tmp_path / "seeds.yaml"
    path.write_text(
        """
seeds:
  - handle: "user.bsky.social"
    did: "did:plc:abc"
    topic: "platform"
""",
        encoding="utf-8",
    )
    loaded = SeedFileLoader(enforce_mvp_bounds=False).load(path)
    known = SeedFileLoader.known_dids(loaded)
    assert known[Handle("user.bsky.social")] == DID("did:plc:abc")
