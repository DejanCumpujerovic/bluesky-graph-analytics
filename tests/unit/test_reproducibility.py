"""Reproducibility helpers."""

from pathlib import Path

import pytest

from bluesky_graph_analytics.application.reproducibility import (
    git_commit_hash,
    set_global_seeds,
    sha256_directory,
)
from bluesky_graph_analytics.constants import GIT_COMMIT_UNKNOWN


def test_git_commit_hash_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BGA_GIT_COMMIT", "deadbeef")
    assert git_commit_hash() == "deadbeef"


def test_git_commit_hash_unknown(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BGA_GIT_COMMIT", raising=False)
    monkeypatch.delenv("BELESKE_GIT_COMMIT", raising=False)
    monkeypatch.setattr(
        "bluesky_graph_analytics.application.reproducibility.subprocess.check_output",
        lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError()),
    )
    assert git_commit_hash() == GIT_COMMIT_UNKNOWN


def test_sha256_directory_stable(tmp_path: Path) -> None:
    (tmp_path / "a.csv").write_text("x\n", encoding="utf-8")
    h1 = sha256_directory(tmp_path)
    h2 = sha256_directory(tmp_path)
    assert h1 == h2


def test_set_global_seeds() -> None:
    set_global_seeds(42)
