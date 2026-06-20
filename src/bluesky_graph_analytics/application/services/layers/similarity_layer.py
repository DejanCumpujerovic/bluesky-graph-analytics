"""Layer 1 — profile similarity (DEO 8.1)."""

from __future__ import annotations

import csv
import time
from pathlib import Path

import pandas as pd
import structlog
from returns.result import Failure, Result

from bluesky_graph_analytics.application.ports.follow_repository import FollowRepository
from bluesky_graph_analytics.application.ports.profile_repository import ProfileRepository
from bluesky_graph_analytics.application.ports.run_repository import RunRepository
from bluesky_graph_analytics.application.records import AnalysisRun
from bluesky_graph_analytics.application.services.layers._common import (
    refresh_run,
    resolve_run,
    results_dir_for,
)
from bluesky_graph_analytics.config import AppSettings
from bluesky_graph_analytics.domain.errors import DomainError
from bluesky_graph_analytics.domain.graph.builders import build_bipartite_similarity_graph
from bluesky_graph_analytics.domain.similarity.metric_correlation import compute_metric_correlations
from bluesky_graph_analytics.domain.similarity.profile_metrics import (
    ProfilePairScore,
    score_profile_pairs,
)
from bluesky_graph_analytics.domain.value_objects import DID, SnapshotId
from bluesky_graph_analytics.infrastructure.pseudonymization import Pseudonymizer

logger = structlog.get_logger(__name__)


class SimilarityLayerService:
    def __init__(
        self,
        runs: RunRepository,
        follows: FollowRepository,
        profiles: ProfileRepository,
        settings: AppSettings,
    ) -> None:
        self._runs = runs
        self._follows = follows
        self._profiles = profiles
        self._settings = settings

    async def run(self, snapshot_id: SnapshotId) -> Result[AnalysisRun, DomainError]:
        run_result = await resolve_run(self._runs, snapshot_id)
        if isinstance(run_result, Failure):
            return run_result
        run = run_result.unwrap()
        assert run.id is not None

        t0 = time.perf_counter()
        relations = (await self._follows.list_by_snapshot(snapshot_id)).unwrap()
        seeds = {p.did for p in (await self._profiles.list_seeds(snapshot_id)).unwrap()}

        graph = build_bipartite_similarity_graph(relations, seeds)
        neighbor_sets = {
            str(n): frozenset(str(x) for x in graph.neighbors(n)) for n in graph.nodes()
        }
        sim_cfg = self._settings.analysis.similarity
        scores = score_profile_pairs(
            neighbor_sets,
            metrics=sim_cfg.metrics,
            min_overlap_relative=sim_cfg.min_overlap_relative,
        )
        if sim_cfg.max_pairs and len(scores) > sim_cfg.max_pairs:
            scores = sorted(scores, key=lambda s: -s.value)[: sim_cfg.max_pairs]

        out_dir = results_dir_for(snapshot_id)
        out_dir.mkdir(parents=True, exist_ok=True)

        for metric in sim_cfg.metrics:
            rows = [s for s in scores if s.metric_name == metric]
            df = pd.DataFrame(
                [
                    {
                        "node_u": s.node_u,
                        "node_v": s.node_v,
                        "value": s.value,
                        "overlap_size": s.overlap_size,
                    }
                    for s in rows
                ],
                columns=["node_u", "node_v", "value", "overlap_size"],
            )
            df.to_parquet(out_dir / f"similarity_{metric}.parquet", index=False)

        pseudo = self._pseudonymizer()
        top = sorted(scores, key=lambda s: -s.value)[:500]
        _write_top_pairs(out_dir / "top_pairs.csv", top, pseudo)

        corr_input = [(s.node_u, s.node_v, s.metric_name, s.value) for s in scores]
        corr_rows = compute_metric_correlations(corr_input)
        with (out_dir / "metric_correlation.csv").open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(
                fh,
                fieldnames=["metric_a", "metric_b", "spearman", "kendall", "rbo_at_50"],
            )
            writer.writeheader()
            for row in corr_rows:
                writer.writerow(
                    {
                        "metric_a": row.metric_a,
                        "metric_b": row.metric_b,
                        "spearman": row.spearman,
                        "kendall": row.kendall,
                        "rbo_at_50": row.rbo_at_50,
                    }
                )

        duration = round(time.perf_counter() - t0, 1)
        await self._runs.merge_stats_section(
            run.id,
            "similarity",
            {
                "pairs_computed": len(scores),
                "pairs_above_threshold": len(
                    [s for s in scores if s.value >= sim_cfg.min_overlap_relative]
                ),
                "duration_seconds": duration,
            },
        )
        logger.info("similarity_layer_complete", pairs=len(scores), duration=duration)
        return await refresh_run(self._runs, run.id, run)

    def _pseudonymizer(self) -> Pseudonymizer | None:
        salt = self._settings.pseudonym_salt
        if not salt or len(salt.encode()) < 32:
            return None
        return Pseudonymizer(salt.encode(), digest_size=self._settings.ethics.pseudonym_digest_size)


def _write_top_pairs(
    path: Path,
    rows: list[ProfilePairScore],
    pseudo: Pseudonymizer | None,
) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["node_u", "node_v", "metric_name", "value", "overlap_size"],
        )
        writer.writeheader()
        for row in rows:
            u = pseudo.hash_did(DID(row.node_u)) if pseudo else row.node_u
            v = pseudo.hash_did(DID(row.node_v)) if pseudo else row.node_v
            writer.writerow(
                {
                    "node_u": u,
                    "node_v": v,
                    "metric_name": row.metric_name,
                    "value": row.value,
                    "overlap_size": row.overlap_size,
                }
            )
