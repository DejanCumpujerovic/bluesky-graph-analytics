"""Leiden community detection."""

import igraph as ig

from bluesky_graph_analytics.domain.community.leiden import LeidenCommunityDetector


def test_leiden_small_graph() -> None:
    g = ig.Graph()
    g.add_vertices(4, attributes={"name": ["a", "b", "c", "d"]})
    g.add_edges([(0, 1), (1, 2), (2, 3)], attributes={"weight": [0.5, 0.5, 0.5]})
    detector = LeidenCommunityDetector(modularity_min=0.0, random_seed=42)
    communities, modularity = detector.detect_on_igraph(g)
    assert len(communities) == 4
    assert modularity >= 0.0


def test_leiden_empty_graph() -> None:
    g = ig.Graph()
    communities, modularity = LeidenCommunityDetector().detect_on_igraph(g)
    assert communities == {}
    assert modularity == 0.0
