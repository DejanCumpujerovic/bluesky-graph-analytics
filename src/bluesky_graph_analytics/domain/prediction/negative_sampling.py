"""Hard negative sampling for link prediction (§5.11)."""

from random import Random

import networkx as nx

from bluesky_graph_analytics.domain.prediction.directed_heuristics import _pred
from bluesky_graph_analytics.domain.value_objects import DID


def common_neighbor_filtered_negatives(
    graph: nx.DiGraph,
    seeds: set[DID],
    positive_test: list[tuple[DID, DID]],
    *,
    ratio: float = 1.0,
    random_seed: int = 42,
) -> list[tuple[DID, DID]]:
    """For seed u, pick v not following u but sharing an in-neighbor with u."""
    rng = Random(random_seed)
    followers_of: dict[DID, set[DID]] = {}
    for u, v in graph.edges():
        followers_of.setdefault(v, set()).add(u)

    negatives: list[tuple[DID, DID]] = []
    target_count = int(len(positive_test) * ratio)

    for seed in seeds:
        if len(negatives) >= target_count:
            break
        followers = followers_of.get(seed, set())
        candidates: list[DID] = []
        seed_preds = _pred(graph, seed)
        for node in graph.nodes():
            if node == seed or node in followers:
                continue
            if not seed_preds:
                continue
            if _pred(graph, node) & seed_preds:
                candidates.append(node)
        rng.shuffle(candidates)
        for cand in candidates:
            if len(negatives) >= target_count:
                break
            negatives.append((cand, seed))

    rng.shuffle(negatives)
    return negatives[:target_count]
