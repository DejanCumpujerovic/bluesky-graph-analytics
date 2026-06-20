"""Metric correlation computation."""

from bluesky_graph_analytics.domain.similarity.metric_correlation import compute_metric_correlations


def test_compute_metric_correlations() -> None:
    scores = [
        ("a", "b", "jaccard", 0.5),
        ("a", "b", "overlap", 0.6),
        ("a", "b", "adamic_adar", 0.4),
        ("c", "d", "jaccard", 0.1),
        ("c", "d", "overlap", 0.2),
        ("c", "d", "adamic_adar", 0.15),
    ]
    rows = compute_metric_correlations(scores)
    assert rows
    assert {r.metric_a for r in rows} >= {"jaccard", "overlap", "adamic_adar"}


def test_compute_metric_correlations_empty() -> None:
    assert compute_metric_correlations([]) == []
