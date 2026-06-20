import networkx as nx

from bluesky_graph_analytics.domain.similarity.jaccard import JaccardSimilarity


def test_jaccard_returns_similarity_score() -> None:
    g = nx.Graph()
    g.add_edges_from([("a", "b"), ("a", "c"), ("b", "c")])
    result = JaccardSimilarity().score(g, "b", "c")
    assert result.metric_name == "jaccard"
    assert 0.0 <= result.value <= 1.0
    assert result.overlap_size >= 1
