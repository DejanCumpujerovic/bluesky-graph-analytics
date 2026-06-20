"""Heuristic link prediction (common neighbors)."""

import networkx as nx

from bluesky_graph_analytics.domain.prediction.base import LinkPredictionStrategy


class CommonNeighborsPredictor(LinkPredictionStrategy):
    def predict_scores(self, graph: nx.Graph, pairs: list[tuple[str, str]]) -> list[float]:
        scores: list[float] = []
        for u, v in pairs:
            scores.append(len(set(graph.neighbors(u)) & set(graph.neighbors(v))))
        return scores
