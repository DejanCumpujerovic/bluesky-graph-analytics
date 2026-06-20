"""Health checks (DEO 8.4.1)."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Any

import httpx
import yaml
from returns.result import Failure
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from bluesky_graph_analytics import __version__
from bluesky_graph_analytics.application.reproducibility import git_commit_hash
from bluesky_graph_analytics.application.seeds_loader import load_seed_file
from bluesky_graph_analytics.config import AppSettings
from bluesky_graph_analytics.constants import DEFAULT_CONFIG_PATH, SEED_PROFILES_PATH


async def run_health(
    engine: AsyncEngine,
    settings: AppSettings,
    *,
    check_api: bool = False,
) -> tuple[dict[str, Any], int]:
    checks: dict[str, Any] = {}
    exit_code = 0

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = {"ok": True, "detail": "connected"}
    except Exception as exc:  # noqa: BLE001
        checks["database"] = {"ok": False, "detail": str(exc)}
        exit_code = 2

    try:
        heads = subprocess.check_output(
            ["alembic", "heads"], text=True, stderr=subprocess.DEVNULL, timeout=10
        ).strip()
        current = subprocess.check_output(
            ["alembic", "current"], text=True, stderr=subprocess.DEVNULL, timeout=10
        ).strip()
        ok = heads.splitlines()[0].split()[0] in current if heads else True
        checks["migrations"] = {"ok": ok, "current": current, "head": heads}
        if not ok and exit_code < 2:
            exit_code = 1
    except Exception as exc:  # noqa: BLE001
        checks["migrations"] = {"ok": False, "detail": str(exc)}
        exit_code = max(exit_code, 1)

    missing: list[str] = []
    if not settings.pseudonym_salt:
        missing.append("PSEUDONYM_SALT")
    if not settings.bluesky_auth_token and not (
        settings.bluesky_handle and settings.bluesky_app_password
    ):
        missing.append("BLUESKY_AUTH_TOKEN or BLUESKY_HANDLE+BLUESKY_APP_PASSWORD")
    env_ok = "PSEUDONYM_SALT" not in missing and (
        "BLUESKY_AUTH_TOKEN" not in missing and "BLUESKY_HANDLE+BLUESKY_APP_PASSWORD" not in missing
    )
    checks["env"] = {"ok": env_ok, "missing": missing}
    if not env_ok:
        exit_code = 2
    if not settings.sentry_dsn:
        checks["env"]["sentry_warning"] = "SENTRY_DSN not set"

    config_ok = Path(DEFAULT_CONFIG_PATH).is_file() and Path(SEED_PROFILES_PATH).is_file()
    yaml_ok = False
    if config_ok:
        try:
            yaml.safe_load(Path(DEFAULT_CONFIG_PATH).read_text(encoding="utf-8"))
            yaml.safe_load(Path(SEED_PROFILES_PATH).read_text(encoding="utf-8"))
            yaml_ok = True
        except Exception:  # noqa: BLE001
            yaml_ok = False
    seed_result = load_seed_file(settings)
    seed_ok = not isinstance(seed_result, Failure)
    checks["config"] = {"ok": config_ok and yaml_ok and seed_ok}
    if not (config_ok and yaml_ok and seed_ok) and exit_code < 2:
        exit_code = 1

    if check_api:
        t0 = time.perf_counter()
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(settings.bluesky.api_base)
            latency = int((time.perf_counter() - t0) * 1000)
            checks["api"] = {"ok": response.status_code < 500, "latency_ms": latency}
            if response.status_code >= 500 and exit_code < 2:
                exit_code = 1
        except Exception as exc:  # noqa: BLE001
            checks["api"] = {"ok": False, "detail": str(exc)}
            if exit_code < 2:
                exit_code = 1
    else:
        checks["api"] = {"ok": True, "skipped": True}

    status = "healthy" if exit_code == 0 else ("down" if exit_code == 2 else "degraded")
    payload = {
        "status": status,
        "checks": checks,
        "version": __version__,
        "git_commit": git_commit_hash(),
    }
    return payload, exit_code
