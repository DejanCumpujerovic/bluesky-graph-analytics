import networkx as nx

from bluesky_graph_analytics.domain.prediction.directed_heuristics import (
    common_neighbors_directed,
    jaccard_directed,
)
from bluesky_graph_analytics.domain.value_objects import DID


def test_common_neighbors_uses_predecessors() -> None:
    g: nx.DiGraph = nx.DiGraph()
    g.add_edge(DID("did:plc:f1"), DID("did:plc:seed"))
    g.add_edge(DID("did:plc:f2"), DID("did:plc:seed"))
    g.add_edge(DID("did:plc:f1"), DID("did:plc:target"))
    score = common_neighbors_directed(g, DID("did:plc:target"), DID("did:plc:seed"))
    assert score >= 1.0


def test_jaccard_directed_bounded() -> None:
    g: nx.DiGraph = nx.DiGraph()
    g.add_edge("a", "s")
    g.add_edge("b", "s")
    v = jaccard_directed(g, "a", "b")
    assert 0.0 <= v <= 1.0
