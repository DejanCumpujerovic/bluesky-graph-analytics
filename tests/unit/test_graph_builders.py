"""Graph builders."""

from bluesky_graph_analytics.domain.graph.builders import (
    build_bipartite_similarity_graph,
    build_follower_follower_projection,
    build_prediction_digraph,
    directed_positive_edges,
)
from bluesky_graph_analytics.domain.models import FollowRelation
from bluesky_graph_analytics.domain.value_objects import DID, SnapshotId


def test_builders_small_graph() -> None:
    snap = SnapshotId("s")
    seeds = {DID("did:plc:s1")}
    rels = [
        FollowRelation(
            follower_did=DID("did:plc:f1"),
            followee_did=DID("did:plc:s1"),
            snapshot_id=snap,
        ),
        FollowRelation(
            follower_did=DID("did:plc:f2"),
            followee_did=DID("did:plc:s1"),
            snapshot_id=snap,
        ),
    ]
    bi = build_bipartite_similarity_graph(rels, seeds)
    assert bi.number_of_edges() == 2
    dig = build_prediction_digraph(rels, seeds)
    assert dig.number_of_edges() == 2
    pos = directed_positive_edges(rels, seeds)
    assert len(pos) == 2
    proj = build_follower_follower_projection(rels, seeds, min_overlap=1, edge_threshold=0.0)
    assert proj.vcount() >= 1
