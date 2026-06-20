from bluesky_graph_analytics.domain.prediction.split_strategy import RandomStratifiedSplit
from bluesky_graph_analytics.domain.value_objects import DID


def test_stratified_split_preserves_seed_coverage() -> None:
    edges = [
        (DID("did:plc:f1"), DID("did:plc:s1")),
        (DID("did:plc:f2"), DID("did:plc:s1")),
        (DID("did:plc:f3"), DID("did:plc:s2")),
        (DID("did:plc:f4"), DID("did:plc:s2")),
    ]
    split = RandomStratifiedSplit().split(edges, test_fraction=0.5, random_seed=42)
    assert split.train_edges
    assert split.warning is not None
