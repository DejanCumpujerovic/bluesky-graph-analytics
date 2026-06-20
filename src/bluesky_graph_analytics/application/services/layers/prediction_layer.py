"""Layer 3 — link prediction (DEO 8.3)."""

from __future__ import annotations

import csv
import time
from pathlib import Path

import matplotlib.pyplot as plt
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
from bluesky_graph_analytics.domain.graph.builders import (
    build_prediction_digraph,
    directed_positive_edges,
)
from bluesky_graph_analytics.domain.prediction.evaluation import PredictionMetricsRow
from bluesky_graph_analytics.domain.prediction.pipeline import (
    Node2VecParams,
    run_prediction_pipeline,
)
from bluesky_graph_analytics.domain.value_objects import DID, SnapshotId
from bluesky_graph_analytics.infrastructure.pseudonymization import Pseudonymizer

logger = structlog.get_logger(__name__)


class PredictionLayerService:
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
        pred_cfg = self._settings.analysis.prediction
        n2v_cfg = pred_cfg.node2vec

        digraph = build_prediction_digraph(relations, seeds)
        pos_edges = directed_positive_edges(relations, seeds)
        prediction = run_prediction_pipeline(
            digraph,
            pos_edges,
            seeds,
            test_fraction=pred_cfg.test_fraction,
            random_seed=self._settings.reproducibility.random_seed,
            k_values=pred_cfg.k_values,
            negative_ratio=pred_cfg.negative_ratio,
            node2vec=Node2VecParams(
                dimensions=n2v_cfg.dimensions,
                walk_length=n2v_cfg.walk_length,
                num_walks=n2v_cfg.num_walks,
                p=n2v_cfg.p,
                q=n2v_cfg.q,
                workers=n2v_cfg.workers,
            ),
        )

        out_dir = results_dir_for(snapshot_id)
        out_dir.mkdir(parents=True, exist_ok=True)
        _write_prediction_csv(out_dir / "prediction_results.csv", prediction.metrics)
        if prediction.split_warning:
            (out_dir / "methodology_warning.txt").write_text(
                prediction.split_warning, encoding="utf-8"
            )

        _write_roc_curves(out_dir / "roc_curves.png", prediction.roc_curves)
        pseudo = self._pseudonymizer()
        _write_top_predicted_links(
            out_dir / "top_predicted_links.csv",
            prediction.top_predicted_links[:100],
            pseudo,
        )

        duration = round(time.perf_counter() - t0, 1)
        test_pos = max(1, int(len(pos_edges) * pred_cfg.test_fraction))
        await self._runs.merge_stats_section(
            run.id,
            "prediction",
            {
                "positive_edges": len(pos_edges),
                "test_positives": test_pos,
                "negatives_sampled": test_pos,
                "methods_evaluated": sorted({m.method for m in prediction.metrics}),
                "duration_seconds": duration,
            },
        )
        logger.info("prediction_layer_complete", duration=duration)
        return await refresh_run(self._runs, run.id, run)

    def _pseudonymizer(self) -> Pseudonymizer | None:
        salt = self._settings.pseudonym_salt
        if not salt or len(salt.encode()) < 32:
            return None
        return Pseudonymizer(salt.encode(), digest_size=self._settings.ethics.pseudonym_digest_size)


def _write_prediction_csv(path: Path, rows: list[PredictionMetricsRow]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["method", "auc", "precision_at_k", "recall_at_k", "k", "map"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "method": row.method,
                    "auc": row.auc,
                    "precision_at_k": row.precision_at_k,
                    "recall_at_k": row.recall_at_k,
                    "k": row.k,
                    "map": row.map_score,
                }
            )


def _write_roc_curves(path: Path, curves: dict[str, tuple[list[int], list[float]]]) -> None:
    from sklearn.metrics import roc_curve

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="random")
    for method, (y_true, y_score) in sorted(curves.items()):
        if len(set(y_true)) < 2:
            continue
        fpr, tpr, _ = roc_curve(y_true, y_score)
        ax.plot(fpr, tpr, label=method)
    ax.set_xlabel("FPR")
    ax.set_ylabel("TPR")
    ax.set_title("ROC curves")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def _write_top_predicted_links(
    path: Path,
    edges: list[tuple[DID, DID, float]],
    pseudo: Pseudonymizer | None,
) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["follower_did", "seed_did", "score"])
        writer.writeheader()
        for follower, seed, score in edges:
            fd = pseudo.hash_did(follower) if pseudo else str(follower)
            sd = pseudo.hash_did(seed) if pseudo else str(seed)
            writer.writerow({"follower_did": fd, "seed_did": sd, "score": round(score, 6)})
