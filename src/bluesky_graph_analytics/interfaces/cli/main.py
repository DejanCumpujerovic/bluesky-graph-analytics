"""Typer CLI (DEO 8.4 — `bga` commands)."""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from collections.abc import Coroutine
from typing import Any

import typer
from returns.result import Failure

from bluesky_graph_analytics.application.dto import (
    AnalysisRequestDTO,
    CollectRequestDTO,
    ExportRequestDTO,
)
from bluesky_graph_analytics.application.services.health_service import run_health
from bluesky_graph_analytics.composition_root import build_container, dispose_container
from bluesky_graph_analytics.config import load_settings
from bluesky_graph_analytics.domain.value_objects import DID, Handle, SnapshotId

app = typer.Typer(help="Bluesky Graph Analytics — Phase 1 MVP")
analyze_app = typer.Typer(help="Analysis layers (DEO 8)")
deletion_app = typer.Typer(help="GDPR deletion workflow")
app.add_typer(analyze_app, name="analyze")
app.add_typer(deletion_app, name="deletion")


def _run(coro: Coroutine[Any, Any, Any]) -> Any:
    return asyncio.run(coro)


def _fail(result: Any) -> None:
    if isinstance(result, Failure):
        typer.secho(str(result.failure()), fg=typer.colors.RED)
        raise typer.Exit(1)


@app.command()
def health(
    check_api: bool = typer.Option(False, "--check-api"),
    verbose: bool = typer.Option(False, "--verbose"),
) -> None:
    """JSON health report on stdout (DEO 8.4.1)."""

    async def _health() -> None:
        settings = load_settings()
        container = build_container()
        try:
            payload, code = await run_health(container.engine, settings, check_api=check_api)
            typer.echo(json.dumps(payload, indent=2))
            if verbose:
                print(json.dumps(payload, indent=2), file=sys.stderr)
            raise typer.Exit(code)
        finally:
            await dispose_container(container)

    _run(_health())


@app.command()
def version() -> None:
    from bluesky_graph_analytics import __version__

    typer.echo(__version__)


@app.command("collect")
def collect(
    topic: str | None = typer.Option(None),
    handle: list[str] | None = typer.Option(None, "--handle", "-h"),  # noqa: B008
    snapshot_id: str | None = typer.Option(None, "--snapshot-id"),
    force_resnapshot: bool = typer.Option(False, "--force-resnapshot"),
) -> None:
    async def _collect() -> None:
        container = build_container()
        try:
            req = CollectRequestDTO(
                seed_handles=[Handle(h) for h in (handle or [])],
                topic=topic,
                snapshot_id=SnapshotId(snapshot_id) if snapshot_id else None,
                force_resnapshot=force_resnapshot,
            )
            result = await container.collection.collect(req)
            if isinstance(result, Failure):
                err = result.failure()
                details = getattr(err, "details", None)
                if isinstance(details, dict) and details.get("abort") == "no_valid_seeds":
                    typer.secho(str(err.message), fg=typer.colors.RED)
                    raise typer.Exit(2)
            _fail(result)
            typer.echo(json.dumps(result.unwrap(), default=str))
        finally:
            await dispose_container(container)

    _run(_collect())


async def _run_layer(layer: str, snapshot_id: str, run_label: str) -> None:
    container = build_container()
    try:
        req = AnalysisRequestDTO(run_label=run_label, snapshot_id=SnapshotId(snapshot_id))
        svc = container.analysis
        if layer == "similarity":
            result = await svc.run_similarity(req)
        elif layer == "community":
            result = await svc.run_community(req)
        elif layer == "prediction":
            result = await svc.run_prediction(req)
        else:
            result = await svc.run_all(req)
        _fail(result)
        typer.echo(f"Run complete: {result.unwrap().id}")
    finally:
        await dispose_container(container)


@analyze_app.command("similarity")
def analyze_similarity(
    snapshot_id: str = typer.Option(..., "--snapshot-id"),
    run_label: str = typer.Option("default", "--run-label", "-l"),
) -> None:
    _run(_run_layer("similarity", snapshot_id, run_label))


@analyze_app.command("community")
def analyze_community(
    snapshot_id: str = typer.Option(..., "--snapshot-id"),
    run_label: str = typer.Option("default", "--run-label", "-l"),
) -> None:
    _run(_run_layer("community", snapshot_id, run_label))


@analyze_app.command("prediction")
def analyze_prediction(
    snapshot_id: str = typer.Option(..., "--snapshot-id"),
    run_label: str = typer.Option("default", "--run-label", "-l"),
) -> None:
    _run(_run_layer("prediction", snapshot_id, run_label))


@analyze_app.command("all")
def analyze_all(
    snapshot_id: str = typer.Option(..., "--snapshot-id"),
    run_label: str = typer.Option("default", "--run-label", "-l"),
) -> None:
    _run(_run_layer("all", snapshot_id, run_label))


@app.command("analyze")
def analyze_legacy(
    run_label: str = typer.Option("default", "--run-label", "-l"),
    snapshot_id: str | None = typer.Option(None, "--snapshot-id"),
) -> None:
    if not snapshot_id:
        typer.echo("--snapshot-id required", err=True)
        raise typer.Exit(2)
    _run(_run_layer("all", snapshot_id, run_label))


@app.command("export")
def export_cmd(
    snapshot_id: str = typer.Option(..., "--snapshot-id"),
    format: str = typer.Option("anonymized", "--format"),  # noqa: A002
    output: str | None = typer.Option(None, "--output"),
) -> None:
    async def _export() -> None:
        container = build_container()
        try:
            req = ExportRequestDTO(
                snapshot_id=SnapshotId(snapshot_id),
                anonymized=format == "anonymized",
                output=output,
            )
            result = await container.export.export(req)
            _fail(result)
            typer.echo(f"Wrote {result.unwrap()}")
        finally:
            await dispose_container(container)

    _run(_export())


@app.command("dashboard")
def dashboard() -> None:
    settings = load_settings()
    host = settings.dashboard.host
    port = settings.dashboard.port
    typer.echo(f"[bga] Dashboard starting on http://localhost:{port}")
    typer.echo("[bga] Press Ctrl+C to stop.")
    home = "src/bluesky_graph_analytics/interfaces/streamlit/Home.py"
    subprocess.run(
        [
            "streamlit",
            "run",
            home,
            f"--server.address={host}",
            f"--server.port={port}",
            "--server.headless=true",
        ],
        check=False,
    )


@deletion_app.command("add")
def deletion_add(
    did: str | None = typer.Option(None, "--did"),
    handle: str | None = typer.Option(None, "--handle"),
    reason: str | None = typer.Option(None, "--reason"),
) -> None:
    async def _add() -> None:
        container = build_container()
        try:
            result = await container.deletion.add_request(
                did=DID(did) if did else None,
                handle=Handle(handle) if handle else None,
                reason=reason,
            )
            _fail(result)
            typer.echo(f"Queued: {result.unwrap().subject_did}")
        finally:
            await dispose_container(container)

    _run(_add())


@deletion_app.command("process")
def deletion_process() -> None:
    async def _process() -> None:
        container = build_container()
        try:
            result = await container.deletion.process_pending()
            _fail(result)
            typer.echo(f"Processed {result.unwrap()} request(s)")
        finally:
            await dispose_container(container)

    _run(_process())


@deletion_app.command("list")
def deletion_list(pending: bool = typer.Option(True, "--pending")) -> None:
    async def _list() -> None:
        container = build_container()
        try:
            if not pending:
                raise typer.Exit(1)
            result = await container.deletion.list_pending()
            _fail(result)
            for row in result.unwrap():
                typer.echo(f"{row.subject_did}  {row.reason or ''}")
        finally:
            await dispose_container(container)

    _run(_list())


def main() -> None:
    app()


if __name__ == "__main__":
    main()
