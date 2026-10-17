"""Community graph visualization (DEO 8.2)."""

from collections.abc import Mapping
from pathlib import Path

import igraph as ig
import matplotlib.pyplot as plt
from pyvis.network import Network

from bluesky_graph_analytics.constants import VIZ_MAX_EDGES_PER_NODE, VIZ_MAX_NODES_LIVE

_HTML_LAYOUT_RADIUS = 1000.0


def _subsample_graph(graph: ig.Graph, max_nodes: int) -> ig.Graph:
    if graph.vcount() <= max_nodes:
        return graph
    degrees = graph.degree()
    top_idx = sorted(range(graph.vcount()), key=lambda i: -degrees[i])[:max_nodes]
    return graph.induced_subgraph(top_idx)


def _strongest_edges(graph: ig.Graph, per_node: int) -> list[int]:
    weights = graph.es["weight"] if "weight" in graph.edge_attributes() else [1.0] * graph.ecount()
    keep: set[int] = set()
    for v in range(graph.vcount()):
        incident = sorted(graph.incident(v), key=lambda e: (-weights[e], e))
        keep.update(incident[:per_node])
    return sorted(keep)


def _community_of(graph: ig.Graph, communities: Mapping[str, int] | None) -> list[int | None]:
    names = [str(n) for n in graph.vs["name"]] if graph.vcount() else []
    if not communities:
        return [None] * len(names)
    return [communities.get(name) for name in names]


def write_community_graph_html(
    graph: ig.Graph,
    path: Path,
    *,
    communities: Mapping[str, int] | None = None,
) -> None:
    g = _subsample_graph(graph, VIZ_MAX_NODES_LIVE)
    groups = _community_of(g, communities)
    net = Network(height="600px", width="100%", directed=False, cdn_resources="remote")
    coords = g.layout_fruchterman_reingold().coords if g.vcount() else []
    extent = max((max(abs(x), abs(y)) for x, y in coords), default=1.0) or 1.0
    scale = _HTML_LAYOUT_RADIUS / extent
    for i, (x, y) in enumerate(coords):
        group = groups[i]
        net.add_node(
            i,
            label=" ",
            title=f"community {group}" if group is not None else "no community",
            group=group if group is not None else -1,
            x=x * scale,
            y=y * scale,
            size=8,
        )
    weights = g.es["weight"] if "weight" in g.edge_attributes() else None
    for eidx in _strongest_edges(g, VIZ_MAX_EDGES_PER_NODE):
        edge = g.es[eidx]
        w = float(weights[eidx]) if weights is not None else 1.0
        net.add_edge(edge.source, edge.target, value=w, color="#cccccc")
    net.set_options('{"physics": {"enabled": false}, "edges": {"smooth": false}}')
    net.save_graph(str(path))


def write_community_graph_png(
    graph: ig.Graph,
    path: Path,
    *,
    communities: Mapping[str, int] | None = None,
) -> None:
    g = _subsample_graph(graph, VIZ_MAX_NODES_LIVE)
    groups = _community_of(g, communities)
    layout = g.layout_fruchterman_reingold()
    coords = layout.coords if hasattr(layout, "coords") else layout
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    cmap = plt.get_cmap("tab10")
    colors = [cmap(grp % 10) if grp is not None else "#bbbbbb" for grp in groups]
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.scatter(xs, ys, s=8, alpha=0.7, c=colors)
    ax.set_title("Community projection")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
