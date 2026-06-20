"""Shared overlap coefficient (DEO 8.1 / 5.3 — single implementation)."""

import networkx as nx

from bluesky_graph_analytics.constants import MIN_OVERLAP_ABSOLUTE
from bluesky_graph_analytics.domain.similarity.base import SimilarityStrategy
from bluesky_graph_analytics.domain.value_objects import SimilarityScore


def compute_overlap(set_a: frozenset[str], set_b: frozenset[str]) -> float:
    """overlap(A, B) = |A ∩ B| / min(|A|, |B|) in [0, 1]."""
    if not set_a or not set_b:
        return 0.0
    inter = len(set_a & set_b)
    if inter == 0:
        return 0.0
    return inter / min(len(set_a), len(set_b))


def dynamic_min_overlap(len_a: int, len_b: int, *, relative: float = 0.01) -> int:
    """max(MIN_OVERLAP_ABSOLUTE, int(relative * min(len_a, len_b)))."""
    return max(MIN_OVERLAP_ABSOLUTE, int(relative * min(len_a, len_b)))


class OverlapSimilarity(SimilarityStrategy):
    """Graph neighbor-set overlap via shared compute_overlap."""

    def score(self, graph: nx.Graph, u: str, v: str) -> SimilarityScore:
        nu = frozenset(str(n) for n in graph.neighbors(u))
        nv = frozenset(str(n) for n in graph.neighbors(v))
        overlap_size = len(nu & nv)
        value = compute_overlap(nu, nv)
        return SimilarityScore(metric_name="overlap", value=value, overlap_size=overlap_size)
