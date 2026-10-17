"""Layer 2 — community detection (DEO 8.2)."""

from __future__ import annotations

import csv
import json
import time
from collections import defaultdict

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
from bluesky_graph_analytics.domain.community.leiden import LeidenCommunityDetector
from bluesky_graph_analytics.domain.community.nlp_labeling import community_top_terms
from bluesky_graph_analytics.domain.community.visualization import (
    write_community_graph_html,
    write_community_graph_png,
)
from bluesky_graph_analytics.domain.errors import DomainError
from bluesky_graph_analytics.domain.graph.builders import build_follower_follower_projection
from bluesky_graph_analytics.domain.models import Profile
from bluesky_graph_analytics.domain.value_objects import DID, SnapshotId
from bluesky_graph_analytics.infrastructure.pseudonymization import Pseudonymizer

logger = structlog.get_logger(__name__)


class CommunityLayerService:
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
        all_profiles = (await self._profiles.list_for_snapshot(snapshot_id)).unwrap()
        by_did = {p.did: p for p in all_profiles}

        comm_cfg = self._settings.analysis.community
        nlp_cfg = self._settings.analysis.nlp
        projection = build_follower_follower_projection(
            relations,
            seeds,
            min_overlap=comm_cfg.min_overlap_seeds,
            edge_threshold=comm_cfg.edge_threshold,
        )
        detector = LeidenCommunityDetector(
            resolution=comm_cfg.resolution,
            modularity_min=comm_cfg.modularity_min,
            algorithm=comm_cfg.algorithm,
            random_seed=self._settings.reproducibility.random_seed,
        )
        communities, modularity = detector.detect_on_igraph(projection)

        members: dict[int, list[Profile]] = defaultdict(list)
        for did, cid in communities.items():
            prof = by_did.get(DID(did))
            if prof:
                members[cid].append(prof)

        stats_rows: list[dict[str, object]] = []
        communities_out: dict[str, dict[str, object]] = {}
        pseudo = self._pseudonymizer()

        for cid, profs in members.items():
            top_terms, lang_dist = community_top_terms(
                profs,
                lang_threshold=nlp_cfg.langdetect_threshold,
                top_n=nlp_cfg.top_terms_per_community,
            )
            stats_rows.append(
                {
                    "community_id": cid,
                    "size": len(profs),
                    "modularity_contribution": round(modularity / max(len(members), 1), 4),
                    "top_terms": "|".join(top_terms),
                    "language_distribution": json.dumps(lang_dist),
                }
            )
            for p in profs:
                key = pseudo.hash_did(p.did) if pseudo else str(p.did)
                communities_out[str(key)] = {
                    "community_id": cid,
                    "top_terms": list(top_terms),
                }

        out_dir = results_dir_for(snapshot_id)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "communities.json").write_text(
            json.dumps(communities_out, indent=2), encoding="utf-8"
        )
        fieldnames = [
            "community_id",
            "size",
            "modularity_contribution",
            "top_terms",
            "language_distribution",
        ]
        with (out_dir / "community_stats.csv").open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(stats_rows)

        write_community_graph_html(
            projection, out_dir / "community_graph.html", communities=communities
        )
        write_community_graph_png(
            projection, out_dir / "community_graph.png", communities=communities
        )

        sizes = [len(v) for v in members.values()]
        duration = round(time.perf_counter() - t0, 1)
        await self._runs.merge_stats_section(
            run.id,
            "community",
            {
                "num_communities": len(members),
                "modularity": round(modularity, 4),
                "largest_community_size": max(sizes) if sizes else 0,
                "duration_seconds": duration,
            },
        )
        logger.info("community_layer_complete", modularity=modularity, duration=duration)
        return await refresh_run(self._runs, run.id, run)

    def _pseudonymizer(self) -> Pseudonymizer | None:
        salt = self._settings.pseudonym_salt
        if not salt or len(salt.encode()) < 32:
            return None
        return Pseudonymizer(salt.encode(), digest_size=self._settings.ethics.pseudonym_digest_size)
