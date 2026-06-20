"""Incremental run stats merging (DEO 7.7)."""

from __future__ import annotations

from typing import Any


def merge_stat(stats: dict[str, Any], key: str, value: Any) -> dict[str, Any]:
    """Set nested key using dot notation, e.g. collection.seeds_total."""
    root = dict(stats)
    parts = key.split(".")
    cursor: dict[str, Any] = root
    for part in parts[:-1]:
        nxt = cursor.get(part)
        if not isinstance(nxt, dict):
            nxt = {}
            cursor[part] = nxt
        cursor = nxt
    cursor[parts[-1]] = value
    return root


def merge_section(stats: dict[str, Any], section: str, patch: dict[str, Any]) -> dict[str, Any]:
    root = dict(stats)
    current = root.get(section)
    if not isinstance(current, dict):
        current = {}
    root[section] = {**current, **patch}
    return root


def increment_stat(stats: dict[str, Any], key: str, delta: int = 1) -> dict[str, Any]:
    parts = key.split(".")
    root = dict(stats)
    cursor: dict[str, Any] = root
    for part in parts[:-1]:
        nxt = cursor.get(part)
        if not isinstance(nxt, dict):
            nxt = {}
            cursor[part] = nxt
        cursor = nxt
    leaf = parts[-1]
    current = cursor.get(leaf, 0)
    if not isinstance(current, (int, float)):
        current = 0
    cursor[leaf] = int(current) + delta
    return root


def increment_nested_counter(
    stats: dict[str, Any],
    key: str,
    counter_key: str,
    delta: int = 1,
) -> dict[str, Any]:
    """Increment counter_key inside dict at dot-path key."""
    parts = key.split(".")
    root = dict(stats)
    cursor: dict[str, Any] = root
    for part in parts:
        nxt = cursor.get(part)
        if not isinstance(nxt, dict):
            nxt = {}
            cursor[part] = nxt
        cursor = nxt
    current = cursor.get(counter_key, 0)
    if not isinstance(current, (int, float)):
        current = 0
    cursor[counter_key] = int(current) + delta
    return root
