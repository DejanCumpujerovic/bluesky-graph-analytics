"""Node2Vec-based link prediction (Faza 1 placeholder wiring)."""

import networkx as nx
from node2vec import Node2Vec

from bluesky_graph_analytics.domain.prediction.base import LinkPredictionStrategy


class Node2VecLinkPredictor(LinkPredictionStrategy):
    def predict_scores(self, graph: nx.Graph, pairs: list[tuple[str, str]]) -> list[float]:
        if graph.number_of_edges() == 0:
            return [0.0] * len(pairs)
        walker = Node2Vec(graph, dimensions=16, walk_length=10, num_walks=20, workers=1)
        model = walker.fit(window=5, min_count=1, batch_words=4)
        scores: list[float] = []
        for u, v in pairs:
            if u not in model.wv or v not in model.wv:
                scores.append(0.0)
            else:
                scores.append(float(model.wv.similarity(u, v)))
        return scores
