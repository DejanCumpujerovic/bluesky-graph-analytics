import networkx as nx

from bluesky_graph_analytics.domain.graph.similarity_analysis import compute_bipartite_similarity
from bluesky_graph_analytics.domain.value_objects import DID


def test_bipartite_similarity_produces_rows() -> None:
    g = nx.Graph()
    g.add_edges_from(
        [
            ("f1", "s1"),
            ("f1", "s2"),
            ("f1", "s3"),
            ("f2", "s1"),
            ("f2", "s2"),
            ("f2", "s3"),
            ("f3", "s1"),
            ("f3", "s2"),
            ("f3", "s3"),
        ]
    )
    seeds = {DID("s1"), DID("s2"), DID("s3")}
    rows = compute_bipartite_similarity(
        g,
        seeds,
        max_pairs=10,
        random_seed=42,
        min_overlap_relative=0.01,
    )
    assert rows
    assert rows[0].metric_name in {"jaccard", "adamic_adar", "overlap"}
