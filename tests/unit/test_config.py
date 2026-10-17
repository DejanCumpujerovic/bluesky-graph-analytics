from pathlib import Path

from bluesky_graph_analytics.config import load_settings


def test_load_nested_config_yaml() -> None:
    settings = load_settings(dev_config_path=Path("config/does-not-exist.yaml"))
    assert settings.bluesky.api_base == "https://bsky.social"
    assert settings.collection.min_followers == 50
    assert settings.reproducibility.random_seed == 42
    assert "jaccard" in settings.analysis.similarity.metrics
    assert settings.analysis.prediction.node2vec.dimensions == 64
    assert settings.ethics.pseudonym_digest_size == 8
    assert settings.dashboard.port == 8501
