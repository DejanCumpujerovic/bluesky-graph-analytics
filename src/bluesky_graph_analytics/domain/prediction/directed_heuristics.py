"""Directed link prediction heuristics using in-neighbors (DEO 5.4)."""

import math

import networkx as nx

from bluesky_graph_analytics.domain.value_objects import DID


def _pred(G: nx.DiGraph, node: DID) -> set[DID]:
    if node not in G:
        return set()
    return set(G.predecessors(node))


def common_neighbors_directed(G: nx.DiGraph, u: DID, v: DID) -> float:
    return float(len(_pred(G, u) & _pred(G, v)))


def adamic_adar_directed(G: nx.DiGraph, u: DID, v: DID) -> float:
    common = _pred(G, u) & _pred(G, v)
    score = 0.0
    for w in common:
        deg = len(_pred(G, w))
        if deg > 1:
            score += 1.0 / math.log(deg)
    return score


def jaccard_directed(G: nx.DiGraph, u: DID, v: DID) -> float:
    pred_u, pred_v = _pred(G, u), _pred(G, v)
    union = pred_u | pred_v
    if not union:
        return 0.0
    return len(pred_u & pred_v) / len(union)


DIRECTED_HEURISTICS: dict[str, object] = {
    "common_neighbors": common_neighbors_directed,
    "adamic_adar": adamic_adar_directed,
    "jaccard": jaccard_directed,
}
