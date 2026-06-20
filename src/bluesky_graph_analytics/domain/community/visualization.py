"""Community graph visualization (DEO 8.2)."""

from pathlib import Path

import igraph as ig
import matplotlib.pyplot as plt
from pyvis.network import Network

from bluesky_graph_analytics.constants import VIZ_MAX_NODES_LIVE


def _subsample_graph(graph: ig.Graph, max_nodes: int) -> ig.Graph:
    if graph.vcount() <= max_nodes:
        return graph
    degrees = graph.degree()
    top_idx = sorted(range(graph.vcount()), key=lambda i: -degrees[i])[:max_nodes]
    return graph.induced_subgraph(top_idx)


def write_community_graph_html(graph: ig.Graph, path: Path, *, title: str = "communities") -> None:
    g = _subsample_graph(graph, VIZ_MAX_NODES_LIVE)
    net = Network(height="600px", width="100%", directed=False)
    layout = g.layout_fruchterman_reingold()
    positions = {i: (layout[i][0], layout[i][1]) for i in range(g.vcount())}
    names = [str(g.vs[i]["name"]) for i in range(g.vcount())]
    for i, name in enumerate(names):
        x, y = positions[i]
        net.add_node(name, label=name[:12], x=float(x), y=float(y))
    weights = g.es["weight"] if "weight" in g.edge_attributes() else None
    for eidx, edge in enumerate(g.es):
        src = names[edge.source]
        tgt = names[edge.target]
        w = float(weights[eidx]) if weights is not None else 1.0
        net.add_edge(src, tgt, value=w)
    net.set_options('{"physics": {"enabled": true}}')
    net.save_graph(str(path))


def write_community_graph_png(graph: ig.Graph, path: Path) -> None:
    g = _subsample_graph(graph, VIZ_MAX_NODES_LIVE)
    layout = g.layout_fruchterman_reingold()
    fig, ax = plt.subplots(figsize=(10, 8))
    coords = layout.coords if hasattr(layout, "coords") else layout
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    ax.scatter(xs, ys, s=8, alpha=0.7)
    ax.set_title("Community projection")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
