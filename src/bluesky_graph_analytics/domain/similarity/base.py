"""Similarity strategy protocol."""

from abc import ABC, abstractmethod

import networkx as nx

from bluesky_graph_analytics.domain.value_objects import SimilarityScore


class SimilarityStrategy(ABC):
    @abstractmethod
    def score(self, graph: nx.Graph, u: str, v: str) -> SimilarityScore:
        """Return normalized similarity score for nodes u and v."""
