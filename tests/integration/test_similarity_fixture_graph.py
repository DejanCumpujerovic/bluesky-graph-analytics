"""Integration: profile similarity on a 10-node fixture graph (DEO 8.1)."""

from bluesky_graph_analytics.domain.graph.builders import build_bipartite_similarity_graph
from bluesky_graph_analytics.domain.models import FollowRelation
from bluesky_graph_analytics.domain.similarity.profile_metrics import score_profile_pairs
from bluesky_graph_analytics.domain.value_objects import DID, SnapshotId


def _fixture_relations() -> list[FollowRelation]:
    """8 followers + 2 seeds = 10 nodes, shared overlap for pair scoring."""
    snap = SnapshotId("test_snap")
    edges = [
        ("f1", "s1"),
        ("f1", "s2"),
        ("f2", "s1"),
        ("f2", "s2"),
        ("f3", "s1"),
        ("f3", "s2"),
        ("f4", "s1"),
        ("f4", "s2"),
        ("f5", "s1"),
        ("f5", "s2"),
        ("f6", "s1"),
        ("f7", "s2"),
        ("f8", "s1"),
        ("f8", "s2"),
    ]
    return [
        FollowRelation(
            follower_did=DID(f),
            followee_did=DID(s),
            snapshot_id=snap,
        )
        for f, s in edges
    ]


def test_similarity_on_ten_node_fixture() -> None:
    relations = _fixture_relations()
    seeds = {DID("s1"), DID("s2")}
    graph = build_bipartite_similarity_graph(relations, seeds)
    assert graph.number_of_nodes() == 10

    neighbor_sets = {str(n): frozenset(str(x) for x in graph.neighbors(n)) for n in graph.nodes()}
    scores = score_profile_pairs(
        neighbor_sets,
        metrics=["jaccard", "adamic_adar", "overlap"],
        min_overlap_relative=0.01,
    )
    assert scores
    metrics = {s.metric_name for s in scores}
    assert metrics == {"jaccard", "adamic_adar", "overlap"}
    for s in scores:
        assert s.value >= 0.0
        if s.metric_name in {"jaccard", "overlap"}:
            assert s.value <= 1.0
        assert s.overlap_size >= 1
