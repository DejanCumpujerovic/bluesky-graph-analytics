"""Append seed skip events to data/raw/seed_skipped.csv (DEO 8.13)."""

from __future__ import annotations

import csv
from datetime import UTC, datetime
from pathlib import Path

from bluesky_graph_analytics.constants import DATA_DIR
from bluesky_graph_analytics.domain.value_objects import DID, Handle

_SEED_SKIPPED_PATH = Path(DATA_DIR) / "raw" / "seed_skipped.csv"
_COLUMNS = ("handle", "did", "reason", "detail", "timestamp")


def append_seed_skipped(
    *,
    handle: Handle,
    did: DID | None,
    reason: str,
    detail: str = "",
) -> None:
    path = _SEED_SKIPPED_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists() or path.stat().st_size == 0
    with path.open("a", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=_COLUMNS)
        if write_header:
            writer.writeheader()
        writer.writerow(
            {
                "handle": str(handle),
                "did": str(did) if did else "",
                "reason": reason,
                "detail": detail,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
