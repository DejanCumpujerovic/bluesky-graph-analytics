"""Follower–follower projection (DEO 5.3)."""

from dataclasses import dataclass

from bluesky_graph_analytics.domain.similarity.overlap import compute_overlap
from bluesky_graph_analytics.domain.value_objects import DID


@dataclass(frozen=True, slots=True)
class ProjectionParams:
    min_overlap: int = 1
    edge_threshold: float = 0.1


def overlap_weight(seeds_a: set[DID], seeds_b: set[DID]) -> float:
    """w(A,B) = overlap(S(A), S(B)) — shared compute_overlap (DEO 8.1 / 5.3)."""
    return compute_overlap(
        frozenset(str(s) for s in seeds_a),
        frozenset(str(s) for s in seeds_b),
    )


def build_weighted_projection(
    follower_to_seeds: dict[DID, set[DID]],
    *,
    params: ProjectionParams,
) -> dict[DID, dict[DID, float]]:
    """Return adjacency with overlap weights; filter w < edge_threshold."""
    followers = [f for f, s in follower_to_seeds.items() if len(s) >= params.min_overlap]
    adj: dict[DID, dict[DID, float]] = {f: {} for f in followers}

    for i, a in enumerate(followers):
        sa = follower_to_seeds[a]
        for b in followers[i + 1 :]:
            sb = follower_to_seeds[b]
            if len(sa & sb) < params.min_overlap:
                continue
            w = overlap_weight(sa, sb)
            if w < params.edge_threshold:
                continue
            adj[a][b] = w
            adj[b][a] = w
    return adj
