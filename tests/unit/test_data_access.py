"""Streamlit data access helpers."""

import sqlite3
from pathlib import Path

import pytest

from bluesky_graph_analytics.interfaces.streamlit import data_access as da


def test_list_snapshots_empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db = tmp_path / "t.db"
    monkeypatch.setattr(da, "_db_path", lambda: db)
    assert da.list_snapshots() == []


def test_list_snapshots_with_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db = tmp_path / "t.db"
    conn = sqlite3.connect(db)
    conn.execute(
        "CREATE TABLE runs (id INTEGER PRIMARY KEY, snapshot_id TEXT, status TEXT, "
        "started_at TEXT, finished_at TEXT, git_commit_hash TEXT, stats TEXT)"
    )
    conn.execute("INSERT INTO runs VALUES (1,'snap1','completed','2025-01-01',NULL,'abc','{}')")
    conn.commit()
    conn.close()
    monkeypatch.setattr(da, "_db_path", lambda: db)
    rows = da.list_snapshots()
    assert len(rows) == 1
    assert rows[0]["snapshot_id"] == "snap1"
