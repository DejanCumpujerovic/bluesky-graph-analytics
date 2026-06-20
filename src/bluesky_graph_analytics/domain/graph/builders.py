"""Build analysis graphs from follow relations (DEO 5.2–5.3)."""

from collections import defaultdict

import igraph as ig
import networkx as nx

from bluesky_graph_analytics.domain.community.projection import (
    ProjectionParams,
    build_weighted_projection,
)
from bluesky_graph_analytics.domain.models import FollowRelation, Profile
from bluesky_graph_analytics.domain.value_objects import DID


def _seed_dids(profiles: list[Profile]) -> set[DID]:
    return {p.did for p in profiles if p.is_seed}


def build_bipartite_similarity_graph(
    relations: list[FollowRelation],
    seeds: set[DID],
) -> nx.Graph:
    """Undirected bipartite seed ↔ follower graph for similarity (§5.2)."""
    graph: nx.Graph = nx.Graph()
    for rel in relations:
        if rel.followee_did not in seeds:
            continue
        graph.add_edge(rel.follower_did, rel.followee_did)
    return graph


def build_prediction_digraph(relations: list[FollowRelation], seeds: set[DID]) -> nx.DiGraph:
    """Directed follower → seed graph for link prediction (§5.2, §5.4)."""
    graph: nx.DiGraph = nx.DiGraph()
    for rel in relations:
        if rel.followee_did not in seeds:
            continue
        graph.add_edge(rel.follower_did, rel.followee_did)
    return graph


def build_follower_follower_projection(
    relations: list[FollowRelation],
    seeds: set[DID],
    *,
    min_overlap: int = 1,
    edge_threshold: float = 0.1,
) -> ig.Graph:
    """Weighted follower–follower projection for Leiden (§5.3)."""
    # S(X) = seeds that follower X follows (followee in seed set)
    follower_to_seeds: dict[DID, set[DID]] = defaultdict(set)
    followers: set[DID] = set()
    for rel in relations:
        if rel.followee_did not in seeds:
            continue
        followers.add(rel.follower_did)
        follower_to_seeds[rel.follower_did].add(rel.followee_did)

    weighted = build_weighted_projection(
        follower_to_seeds,
        params=ProjectionParams(min_overlap=min_overlap, edge_threshold=edge_threshold),
    )
    if not weighted:
        return ig.Graph(n=0)

    nodes = list(weighted)
    index = {did: i for i, did in enumerate(nodes)}
    edges: list[tuple[int, int]] = []
    weights: list[float] = []
    for u, nbrs in weighted.items():
        for v, w in nbrs.items():
            if index[u] < index[v]:
                edges.append((index[u], index[v]))
                weights.append(w)

    g = ig.Graph(n=len(nodes), edges=edges, directed=False)
    g.es["weight"] = weights
    g.vs["name"] = nodes
    return g


def directed_positive_edges(
    relations: list[FollowRelation], seeds: set[DID]
) -> list[tuple[DID, DID]]:
    """(follower, seed) directed edges for prediction evaluation."""
    return [(rel.follower_did, rel.followee_did) for rel in relations if rel.followee_did in seeds]
