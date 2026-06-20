"""Adamic-Adar link prediction score (normalized to [0, 1])."""

import math

import networkx as nx

from bluesky_graph_analytics.domain.similarity.base import SimilarityStrategy
from bluesky_graph_analytics.domain.value_objects import SimilarityScore


class AdamicAdarSimilarity(SimilarityStrategy):
    def score(self, graph: nx.Graph, u: str, v: str) -> SimilarityScore:
        common = set(graph.neighbors(u)) & set(graph.neighbors(v))
        raw = sum(1.0 / math.log(graph.degree(w)) for w in common if graph.degree(w) > 1)
        # Normalize via 1 - exp(-x) so unbounded raw scores map into [0, 1]
        value = 1.0 - math.exp(-raw) if raw > 0 else 0.0
        return SimilarityScore(metric_name="adamic_adar", value=value, overlap_size=len(common))
