from bluesky_graph_analytics.application.run_stats import (
    increment_nested_counter,
    increment_stat,
    merge_section,
    merge_stat,
)


def test_merge_stat_dot_path() -> None:
    stats = merge_stat({}, "collection.seeds_total", 100)
    assert stats["collection"]["seeds_total"] == 100


def test_merge_section() -> None:
    stats = merge_section({"collection": {"a": 1}}, "collection", {"b": 2})
    assert stats["collection"] == {"a": 1, "b": 2}


def test_increment_stat() -> None:
    stats = increment_stat({"collection": {"seeds_valid": 1}}, "collection.seeds_valid", 2)
    assert stats["collection"]["seeds_valid"] == 3


def test_increment_nested_counter() -> None:
    stats = increment_nested_counter(
        {},
        "collection.seeds_skipped_reasons",
        "out_of_range",
    )
    assert stats["collection"]["seeds_skipped_reasons"]["out_of_range"] == 1
