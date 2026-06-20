"""Link prediction strategy protocol."""

from abc import ABC, abstractmethod

import networkx as nx


class LinkPredictionStrategy(ABC):
    @abstractmethod
    def predict_scores(self, graph: nx.Graph, pairs: list[tuple[str, str]]) -> list[float]:
        """Return scores for candidate pairs (higher = more likely link)."""
