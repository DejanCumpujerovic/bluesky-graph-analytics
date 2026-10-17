"""Read-only DB access for Streamlit dashboard (DEO 8.5)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from bluesky_graph_analytics.config import load_settings
from bluesky_graph_analytics.constants import DATA_DIR


def _db_path() -> Path:
    settings = load_settings()
    url = settings.storage.database_url
    if url.startswith("sqlite+aiosqlite:///"):
        return Path(url.removeprefix("sqlite+aiosqlite:///"))
    return Path(DATA_DIR) / "cache.db"


def list_snapshots() -> list[dict[str, Any]]:
    path = _db_path()
    if not path.is_file():
        return []
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, snapshot_id, status, started_at, finished_at, git_commit_hash, stats "
        "FROM runs ORDER BY started_at DESC"
    ).fetchall()
    conn.close()
    out: list[dict[str, Any]] = []
    for row in rows:
        stats_raw = row["stats"]
        stats = json.loads(stats_raw) if stats_raw else {}
        out.append(
            {
                "id": row["id"],
                "snapshot_id": row["snapshot_id"],
                "status": row["status"],
                "started_at": row["started_at"],
                "finished_at": row["finished_at"],
                "git_commit_hash": row["git_commit_hash"],
                "stats": stats,
            }
        )
    return out


def snapshot_run(snapshot_id: str) -> dict[str, Any] | None:
    for row in list_snapshots():
        if row["snapshot_id"] == snapshot_id:
            return row
    return None


def seed_follower_histogram(snapshot_id: str) -> list[tuple[int, int]]:
    path = _db_path()
    if not path.is_file():
        return []
    conn = sqlite3.connect(path)
    run = conn.execute("SELECT id FROM runs WHERE snapshot_id = ?", (snapshot_id,)).fetchone()
    if run is None:
        conn.close()
        return []
    rows = conn.execute(
        "SELECT followers_count, COUNT(*) AS n FROM profiles "
        "WHERE run_id = ? AND is_seed = 1 GROUP BY followers_count",
        (run[0],),
    ).fetchall()
    conn.close()
    return [(int(r[0]), int(r[1])) for r in rows]


def language_distribution(snapshot_id: str) -> dict[str, int]:
    path = _db_path()
    if not path.is_file():
        return {}
    conn = sqlite3.connect(path)
    run = conn.execute("SELECT id FROM runs WHERE snapshot_id = ?", (snapshot_id,)).fetchone()
    if run is None:
        conn.close()
        return {}
    rows = conn.execute(
        "SELECT COALESCE(detected_language, 'unknown') AS lang, COUNT(*) "
        "FROM profiles WHERE run_id = ? GROUP BY lang",
        (run[0],),
    ).fetchall()
    conn.close()
    return {str(r[0]): int(r[1]) for r in rows}


def seed_profiles(snapshot_id: str) -> list[dict[str, Any]]:
    path = _db_path()
    if not path.is_file():
        return []
    conn = sqlite3.connect(path)
    rows = conn.execute(
        "SELECT p.did, p.handle, p.followers_count FROM profiles p "
        "JOIN runs r ON r.id = p.run_id WHERE r.snapshot_id = ? AND p.is_seed = 1",
        (snapshot_id,),
    ).fetchall()
    conn.close()
    return [{"did": r[0], "handle": r[1], "followers_count": int(r[2] or 0)} for r in rows]


def followers_by_seed(snapshot_id: str) -> dict[str, set[str]]:
    path = _db_path()
    if not path.is_file():
        return {}
    conn = sqlite3.connect(path)
    rows = conn.execute(
        "SELECT followee_did, follower_did FROM follows WHERE snapshot_id = ?",
        (snapshot_id,),
    ).fetchall()
    conn.close()
    out: dict[str, set[str]] = {}
    for seed, follower in rows:
        out.setdefault(str(seed), set()).add(str(follower))
    return out
