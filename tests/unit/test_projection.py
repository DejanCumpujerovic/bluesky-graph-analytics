from bluesky_graph_analytics.domain.community.projection import overlap_weight
from bluesky_graph_analytics.domain.value_objects import DID


def test_overlap_weight_formula() -> None:
    a = {DID("did:plc:seed1"), DID("did:plc:seed2")}
    b = {DID("did:plc:seed1"), DID("did:plc:seed3")}
    assert overlap_weight(a, b) == 0.5
