"""Seed skipped CSV writer."""

from pathlib import Path

import pytest

from bluesky_graph_analytics.application import seed_skipped as mod
from bluesky_graph_analytics.domain.value_objects import DID, Handle


def test_append_seed_skipped(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mod, "_SEED_SKIPPED_PATH", tmp_path / "seed_skipped.csv")
    mod.append_seed_skipped(handle=Handle("x.bsky.social"), did=DID("did:plc:x"), reason="blocked")
    text = (tmp_path / "seed_skipped.csv").read_text(encoding="utf-8")
    assert "blocked" in text
    assert "x.bsky.social" in text
