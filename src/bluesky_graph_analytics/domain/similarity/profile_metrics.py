"""Profile–profile similarity metrics on neighbor sets (DEO 8.1)."""

import math
from dataclasses import dataclass

from bluesky_graph_analytics.domain.similarity.overlap import compute_overlap, dynamic_min_overlap


@dataclass(frozen=True, slots=True)
class ProfilePairScore:
    node_u: str
    node_v: str
    metric_name: str
    value: float
    overlap_size: int


def jaccard_sets(set_a: frozenset[str], set_b: frozenset[str]) -> float:
    union = set_a | set_b
    if not union:
        return 0.0
    return len(set_a & set_b) / len(union)


def adamic_adar_sets(
    set_a: frozenset[str],
    set_b: frozenset[str],
    *,
    degree_fn: dict[str, int] | None = None,
) -> float:
    common = set_a & set_b
    score = 0.0
    for w in common:
        deg = degree_fn.get(w, 1) if degree_fn else 1
        if deg > 1:
            score += 1.0 / math.log(deg)
    return score


def overlap_sets(set_a: frozenset[str], set_b: frozenset[str]) -> float:
    return compute_overlap(set_a, set_b)


def score_profile_pairs(
    neighbor_sets: dict[str, frozenset[str]],
    *,
    metrics: list[str],
    min_overlap_relative: float = 0.01,
) -> list[ProfilePairScore]:
    nodes = list(neighbor_sets.keys())
    rows: list[ProfilePairScore] = []
    degree_fn = {n: len(neighbor_sets[n]) for n in nodes}

    for i, u in enumerate(nodes):
        su = neighbor_sets[u]
        for v in nodes[i + 1 :]:
            sv = neighbor_sets[v]
            overlap_size = len(su & sv)
            threshold = dynamic_min_overlap(len(su), len(sv), relative=min_overlap_relative)
            if overlap_size < threshold:
                continue
            for metric in metrics:
                if metric == "jaccard":
                    value = jaccard_sets(su, sv)
                elif metric == "adamic_adar":
                    value = adamic_adar_sets(su, sv, degree_fn=degree_fn)
                elif metric == "overlap":
                    value = overlap_sets(su, sv)
                else:
                    continue
                rows.append(
                    ProfilePairScore(
                        node_u=u,
                        node_v=v,
                        metric_name=metric,
                        value=value,
                        overlap_size=overlap_size,
                    )
                )
    return rows
