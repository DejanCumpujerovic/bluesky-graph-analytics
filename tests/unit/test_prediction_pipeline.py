"""Prediction pipeline edge cases."""

import networkx as nx

from bluesky_graph_analytics.domain.prediction.pipeline import run_prediction_pipeline
from bluesky_graph_analytics.domain.value_objects import DID


def test_pipeline_skips_node2vec_when_only_one_class() -> None:
    """Single-seed star: hard negatives are empty → skip LogReg, keep heuristics."""
    seed = DID("did:plc:seed")
    edges = [(DID(f"did:plc:f{i}"), seed) for i in range(20)]
    digraph = nx.DiGraph()
    digraph.add_edges_from(edges)

    result = run_prediction_pipeline(
        digraph,
        edges,
        {seed},
        test_fraction=0.2,
        random_seed=42,
        node2vec=None,
    )
    assert result.metrics
    methods = {m.method for m in result.metrics}
    assert "node2vec_logreg" not in methods
    assert result.split_warning is not None
    assert "Skipped Node2Vec+LogReg" in result.split_warning
