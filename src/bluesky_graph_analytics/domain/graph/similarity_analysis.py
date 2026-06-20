"""Bipartite similarity scoring (DEO 5.2, 6.1 analysis.similarity)."""

from dataclasses import dataclass
from random import Random

import networkx as nx

from bluesky_graph_analytics.constants import MIN_OVERLAP_ABSOLUTE
from bluesky_graph_analytics.domain.similarity.adamic_adar import AdamicAdarSimilarity
from bluesky_graph_analytics.domain.similarity.base import SimilarityStrategy
from bluesky_graph_analytics.domain.similarity.jaccard import JaccardSimilarity
from bluesky_graph_analytics.domain.similarity.overlap import OverlapSimilarity
from bluesky_graph_analytics.domain.value_objects import DID, SimilarityScore

_METRIC_REGISTRY: dict[str, SimilarityStrategy] = {
    "jaccard": JaccardSimilarity(),
    "adamic_adar": AdamicAdarSimilarity(),
    "overlap": OverlapSimilarity(),
}


def strategies_for_metrics(metrics: list[str]) -> list[SimilarityStrategy]:
    unknown = [m for m in metrics if m not in _METRIC_REGISTRY]
    if unknown:
        msg = f"Unknown similarity metrics: {unknown}"
        raise ValueError(msg)
    return [_METRIC_REGISTRY[m] for m in metrics]


@dataclass(frozen=True, slots=True)
class SimilarityResultRow:
    node_u: str
    node_v: str
    metric_name: str
    value: float
    overlap_size: int


def _common_seed_count(graph: nx.Graph, u: str, v: str, seeds: set[str]) -> int:
    nu = set(graph.neighbors(u)) & seeds
    nv = set(graph.neighbors(v)) & seeds
    return len(nu & nv)


def compute_bipartite_similarity(
    graph: nx.Graph,
    seeds: set[DID],
    *,
    metrics: list[str] | None = None,
    max_pairs: int = 5000,
    random_seed: int = 42,
    min_overlap_relative: float = 0.01,
) -> list[SimilarityResultRow]:
    """Score follower–follower pairs on the bipartite seed↔follower graph."""
    metric_list = metrics or list(_METRIC_REGISTRY.keys())
    strategy_list = strategies_for_metrics(metric_list)

    seed_set = {str(s) for s in seeds}
    followers = [n for n in graph.nodes() if str(n) not in seed_set]
    if len(followers) < 2:
        return []

    rng = Random(random_seed)
    all_pairs: list[tuple[str, str]] = []
    for i, u in enumerate(followers):
        for v in followers[i + 1 :]:
            overlap = _common_seed_count(graph, str(u), str(v), seed_set)
            nu = len(set(graph.neighbors(u)) & seed_set)
            nv = len(set(graph.neighbors(v)) & seed_set)
            min_seeds = min(nu, nv)
            if overlap < MIN_OVERLAP_ABSOLUTE:
                continue
            if min_seeds > 0 and overlap / min_seeds < min_overlap_relative:
                continue
            all_pairs.append((str(u), str(v)))

    rng.shuffle(all_pairs)
    pairs = all_pairs[:max_pairs]

    rows: list[SimilarityResultRow] = []
    for u, v in pairs:
        for strategy in strategy_list:
            score: SimilarityScore = strategy.score(graph, u, v)
            rows.append(
                SimilarityResultRow(
                    node_u=u,
                    node_v=v,
                    metric_name=score.metric_name,
                    value=score.value,
                    overlap_size=score.overlap_size,
                )
            )
    return rows
