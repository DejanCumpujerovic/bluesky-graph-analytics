"""Reproducibility helpers (DEO 5.9, 8.8)."""

import hashlib
import os
import random
import subprocess
from pathlib import Path

import numpy as np

from bluesky_graph_analytics.constants import GIT_COMMIT_UNKNOWN


def set_global_seeds(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)


def git_commit_hash() -> str:
    for key in ("BGA_GIT_COMMIT", "BELESKE_GIT_COMMIT"):
        if env := os.getenv(key):
            return env.strip()[:64]
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parents[3],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=2,
        )
        return out.strip()[:64]
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return GIT_COMMIT_UNKNOWN


def sha256_directory(path: Path, *, patterns: tuple[str, ...] = ("*.csv", "*.json")) -> str:
    digest = hashlib.sha256()
    files: list[Path] = []
    for pattern in patterns:
        files.extend(sorted(path.glob(pattern)))
    for file in files:
        digest.update(file.name.encode())
        digest.update(file.read_bytes())
    return digest.hexdigest()
