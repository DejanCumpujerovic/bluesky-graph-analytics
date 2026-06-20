"""Train/test edge split utilities for evaluation."""

from dataclasses import dataclass

import networkx as nx


@dataclass(frozen=True, slots=True)
class EdgeSplit:
    train: nx.Graph
    test_edges: list[tuple[str, str]]


def random_edge_split(graph: nx.Graph, test_ratio: float = 0.2, seed: int = 42) -> EdgeSplit:
    import random

    rng = random.Random(seed)
    edges = list(graph.edges())
    rng.shuffle(edges)
    cut = max(1, int(len(edges) * test_ratio))
    test = edges[:cut]
    train_edges = edges[cut:]
    train = nx.Graph()
    train.add_nodes_from(graph.nodes())
    train.add_edges_from(train_edges)
    return EdgeSplit(train=train, test_edges=test)
