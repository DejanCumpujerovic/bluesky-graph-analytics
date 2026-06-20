"""Jaccard similarity on neighborhood sets."""

import networkx as nx

from bluesky_graph_analytics.domain.similarity.base import SimilarityStrategy
from bluesky_graph_analytics.domain.value_objects import SimilarityScore


class JaccardSimilarity(SimilarityStrategy):
    def score(self, graph: nx.Graph, u: str, v: str) -> SimilarityScore:
        nu = set(graph.neighbors(u)) | {u}
        nv = set(graph.neighbors(v)) | {v}
        intersection = nu & nv
        union = nu | nv
        overlap_size = len(intersection)
        value = overlap_size / len(union) if union else 0.0
        return SimilarityScore(metric_name="jaccard", value=value, overlap_size=overlap_size)
