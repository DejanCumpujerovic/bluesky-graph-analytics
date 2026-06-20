"""Community graph visualization."""

import igraph as ig

from bluesky_graph_analytics.domain.community.visualization import (
    write_community_graph_html,
    write_community_graph_png,
)


def test_write_community_graphs(tmp_path) -> None:
    g = ig.Graph()
    g.add_vertices(3, attributes={"name": ["a", "b", "c"]})
    g.add_edges([(0, 1), (1, 2)], attributes={"weight": [0.5, 0.5]})
    html = tmp_path / "g.html"
    png = tmp_path / "g.png"
    write_community_graph_html(g, html)
    write_community_graph_png(g, png)
    assert html.stat().st_size > 0
    assert png.stat().st_size > 0
